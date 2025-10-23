#!/usr/bin/env python3

"""
PEP 508 URL + Version Workaround Backend with Git Submodule Support

This build backend works around PEP 508's limitation that you cannot specify
both a version constraint AND a git URL for the same dependency.

It provides automatic fallback:
- If custom index is configured: Use version constraints (fast, no git clones)
- If custom index NOT configured: Use git URLs (slow, but still works)
- If git submodules present: Check versions and only install if needed

Usage in pyproject.toml:
    [build-system]
    requires = ["setuptools"]
    build-backend = "pep508_url_version_backend"
    backend-path = ["."]

    [project]
    name = "mypackage"
    version = "1.0.0"
    dependencies = []  # Leave empty, we populate dynamically

    [tool.pep508-url-version-backend]
    dependencies-indexed = [
        "somepackage>=0.0.1234567",
    ]
    dependencies-git = [
        "somepackage @ git+https://github.com/user/somepackage",
    ]
    # Packages provided via git submodules (checked for version updates)
    dependencies-submodules = [
        "privatepackage",
    ]
    index-urls = [
        "jakeogh.github.io",
        "myapps-index",
    ]
"""

import os
import shutil
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

try:
    from tomlkit import dumps as toml_dumps
    from tomlkit import parse as toml_parse
except ImportError:
    toml_parse = None
    toml_dumps = None

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as get_installed_version
except ImportError:
    from importlib_metadata import version as get_installed_version
    from importlib_metadata import PackageNotFoundError

from setuptools import build_meta as _orig_backend


def _has_custom_index():
    """
    Check if a custom package index is configured.

    Returns:
        bool: True if custom index appears to be configured
    """
    extra_index = os.environ.get("PIP_EXTRA_INDEX_URL", "")
    index_url = os.environ.get("PIP_INDEX_URL", "")

    config = _load_config()
    index_markers = config.get("index-urls", ["jakeogh.github.io", "pip-index"])

    for marker in index_markers:
        if marker in extra_index or marker in index_url:
            return True

    return False


def _load_config():
    """
    Load configuration from pyproject.toml.

    Returns:
        dict: Configuration from [tool.pep508-url-version-backend]
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    return data.get("tool", {}).get("pep508-url-version-backend", {})


def _get_submodule_version(submodule_path):
    """
    Get version from a submodule's pyproject.toml.

    Args:
        submodule_path: Path to the submodule directory

    Returns:
        str: Version string or None
    """
    pyproject = submodule_path / "pyproject.toml"
    if not pyproject.exists():
        return None

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version")
    except Exception:
        return None


def _check_submodule_needs_install(package_name, submodule_path):
    """
    Check if a submodule package needs to be installed.

    Args:
        package_name: Name of the package
        submodule_path: Path to the submodule directory

    Returns:
        bool: True if package needs install/update, False if already current
    """
    # Get version from submodule
    submodule_version = _get_submodule_version(submodule_path)
    if not submodule_version:
        # Can't determine version, install to be safe
        return True

    # Check if package is installed
    try:
        installed_version = get_installed_version(package_name)
    except PackageNotFoundError:
        # Not installed, needs install
        return True

    # Compare versions
    if installed_version != submodule_version:
        print(
            f"pep508_url_version_backend: {package_name} needs update: "
            f"{installed_version} -> {submodule_version}",
            file=sys.stderr,
        )
        return True

    print(
        f"pep508_url_version_backend: {package_name} already current ({installed_version})",
        file=sys.stderr,
    )
    return False


def _get_dependencies():
    """
    Get the appropriate dependencies based on index configuration.

    Returns:
        list: List of dependency strings
    """
    config = _load_config()
    deps = []

    if _has_custom_index():
        print("custom index detected, using fast-path", file=sys.stderr)
        deps = list(config.get("dependencies-indexed", []))
        print(
            f"pep508_url_version_backend: Using indexed dependencies (fast path)",
            file=sys.stderr,
        )
    else:
        deps = list(config.get("dependencies-git", []))
        print(
            f"pep508_url_version_backend: Using git URL dependencies (slow fallback)",
            file=sys.stderr,
        )
        print(
            f"pep508_url_version_backend: Tip: Set PIP_EXTRA_INDEX_URL to speed this up",
            file=sys.stderr,
        )

    # Handle submodule dependencies
    submodule_deps = config.get("dependencies-submodules", [])
    if submodule_deps:
        for package_name in submodule_deps:
            # Try common submodule locations
            submodule_path = Path(package_name)
            if not submodule_path.exists():
                submodule_path = Path("_vendor") / package_name
            if not submodule_path.exists():
                submodule_path = Path("submodules") / package_name

            if submodule_path.exists() and submodule_path.is_dir():
                if _check_submodule_needs_install(package_name, submodule_path):
                    # Add as local path dependency
                    deps.append(f"{package_name} @ file://{submodule_path.resolve()}")
                # else: already installed and current, skip
            else:
                print(
                    f"WARNING: Submodule {package_name} not found, skipping",
                    file=sys.stderr,
                )

    return deps


def _create_modified_pyproject():
    """
    Create a temporary modified pyproject.toml with injected dependencies.

    Returns:
        Path: Path to temporary pyproject.toml
    """
    pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        return pyproject_path

    if toml_parse is None:
        print(
            "WARNING: tomlkit not available, cannot inject dependencies",
            file=sys.stderr,
        )
        return pyproject_path

    with open(pyproject_path, "r") as f:
        content = f.read()
        doc = toml_parse(content)

    deps = _get_dependencies()

    if not deps:
        return pyproject_path

    if "project" not in doc:
        doc["project"] = {}

    original_deps = doc["project"].get("dependencies", [])

    merged_deps = list(deps)
    for dep in original_deps:
        if dep and dep not in merged_deps:
            merged_deps.append(dep)

    doc["project"]["dependencies"] = merged_deps

    temp_path = pyproject_path.with_name("pyproject.toml.tmp")

    with open(temp_path, "w") as f:
        f.write(toml_dumps(doc))

    return temp_path


def _with_modified_pyproject(func):
    """
    Decorator that temporarily replaces pyproject.toml with our modified version.
    """

    def wrapper(*args, **kwargs):
        pyproject_path = Path("pyproject.toml")
        backup_path = pyproject_path.with_name("pyproject.toml.backup")
        temp_path = None

        try:
            temp_path = _create_modified_pyproject()

            if temp_path != pyproject_path:
                shutil.copy2(pyproject_path, backup_path)
                shutil.copy2(temp_path, pyproject_path)
                print(
                    "pep508_url_version_backend: Injected dependencies into pyproject.toml",
                    file=sys.stderr,
                )

            result = func(*args, **kwargs)

            return result

        finally:
            if backup_path.exists():
                shutil.copy2(backup_path, pyproject_path)
                backup_path.unlink()
                print(
                    "pep508_url_version_backend: Restored original pyproject.toml",
                    file=sys.stderr,
                )

            if temp_path and temp_path != pyproject_path and temp_path.exists():
                temp_path.unlink()

    return wrapper


# Wrap all the PEP 517 hooks


def get_requires_for_build_wheel(config_settings=None):
    """PEP 517 hook: Get requirements for building a wheel."""
    return _orig_backend.get_requires_for_build_wheel(config_settings)


def get_requires_for_build_sdist(config_settings=None):
    """PEP 517 hook: Get requirements for building an sdist."""
    return _orig_backend.get_requires_for_build_sdist(config_settings)


@_with_modified_pyproject
def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    """
    PEP 517 hook: Prepare metadata for wheel build.

    This is where we inject the appropriate dependencies before setuptools
    generates the metadata.
    """
    return _orig_backend.prepare_metadata_for_build_wheel(
        metadata_directory, config_settings
    )


@_with_modified_pyproject
def build_wheel(
    wheel_directory,
    config_settings=None,
    metadata_directory=None,
):
    """PEP 517 hook: Build a wheel."""
    return _orig_backend.build_wheel(
        wheel_directory, config_settings, metadata_directory
    )


@_with_modified_pyproject
def build_sdist(sdist_directory, config_settings=None):
    """PEP 517 hook: Build an sdist."""
    return _orig_backend.build_sdist(sdist_directory, config_settings)


def get_requires_for_build_editable(config_settings=None):
    """PEP 660 hook: Get requirements for editable install."""
    if hasattr(_orig_backend, "get_requires_for_build_editable"):
        return _orig_backend.get_requires_for_build_editable(config_settings)
    return []


@_with_modified_pyproject
def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    """PEP 660 hook: Prepare metadata for editable install."""
    if hasattr(_orig_backend, "prepare_metadata_for_build_editable"):
        return _orig_backend.prepare_metadata_for_build_editable(
            metadata_directory, config_settings
        )
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)


@_with_modified_pyproject
def build_editable(
    wheel_directory,
    config_settings=None,
    metadata_directory=None,
):
    """PEP 660 hook: Build an editable wheel."""
    if hasattr(_orig_backend, "build_editable"):
        return _orig_backend.build_editable(
            wheel_directory, config_settings, metadata_directory
        )
    return build_wheel(wheel_directory, config_settings, metadata_directory)
