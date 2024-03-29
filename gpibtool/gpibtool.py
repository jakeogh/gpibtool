#!/usr/bin/env python3
# -*- coding: utf8 -*-

# pylint: disable=missing-docstring               # [C0111] docstrings are always outdated and wrong
# pylint: disable=invalid-name                    # [C0103] single letter var names, name too descriptive

# import gpib
# import visa
# import pyvisa as visa  # conflct with https://github.com/visa-sdk/visa-python
# from pyvisa.errors import VisaIOError
# from gpib import GpibError

from __future__ import annotations

import sys
from collections.abc import Sequence
from math import inf
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal

import click
import pyvisa
import sh
from asserttool import ic
from bnftool import get_bnf_syntax
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tvicgvd
from eprint import eprint
from globalverbose import gvd
from mptool import output
from pyvisa.errors import VisaIOError
from stdiotool import supress_stderr
from unmp import unmp

signal(SIGPIPE, SIG_DFL)


class NoResourcesFoundError(ValueError):
    pass


def get_instrument(
    *,
    address: str,
    verbose: bool = False,
):
    if verbose:
        ic(address)
    rm = pyvisa.ResourceManager("@py")
    inst = rm.open_resource(address)
    if verbose:
        ic(inst)
    return inst


def command_query(
    *,
    address: str,
    command: str,
    verbose: bool = False,
):
    if verbose:
        ic(address)
    inst = get_instrument(
        address=address,
        verbose=verbose,
    )
    # idn = inst.query("*IDN?")
    idn = inst.query(command)
    if verbose:
        ic(idn)
    return idn.strip()


def command_idn(
    *,
    address: str,
    verbose: bool = False,
):
    idn = command_query(address=address, command="*IDN?", verbose=verbose)
    return idn


def get_resources(
    keep_asrl: bool,
    verbose: bool = False,
):
    if verbose:
        ic(keep_asrl)

    if verbose == inf:
        resource_manager = pyvisa.ResourceManager()
        resources = list(resource_manager.list_resources())
    else:
        with supress_stderr():
            resource_manager = pyvisa.ResourceManager()
            resources = list(resource_manager.list_resources())

    if verbose:
        ic(resources)

    if not keep_asrl:
        try:
            resources.remove("ASRL/dev/ttyS0::INSTR")
        except ValueError:
            pass
        try:
            resources.remove("ASRL/dev/ttyUSB0::INSTR")
        except ValueError:
            pass

    if resources:
        return tuple(resources)
    raise NoResourcesFoundError


@click.group(no_args_is_help=True, cls=AHGroup)
@click_add_options(click_global_options)
@click.pass_context
def cli(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
):
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )


@cli.command("idn")
@click_add_options(click_global_options)
@click.pass_context
def _read_command_idn(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
):
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    iterator: Sequence[str] = unmp(valid_types=[str], verbose=verbose)
    for address in iterator:
        output(
            command_idn(address=address, verbose=verbose),
            reason=address,
            dict_output=dict_output,
            tty=tty,
            verbose=verbose,
        )


@cli.command("info")
@click_add_options(click_global_options)
@click.pass_context
def _pyvisa_info(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
):
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    info_command = sh.Command("pyvisa-info")
    # python -c "from pyvisa import util; util.get_debug_info()"
    pyvisa_info_path = str(sh.which("pyvisa-info")).strip()
    eprint(f"Output of {pyvisa_info_path}:")
    info_command(_out=sys.stdout)

    lsusb_command = sh.Command("lsusb")
    lsusb_path = str(sh.which("lsusb")).strip()
    eprint(f"Output of {lsusb_path}:")
    lsusb_command(_out=sys.stdout)


@cli.command("syntax")
@click_add_options(click_global_options)
@click.pass_context
def _bnf_syntax(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
):
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    bnf_symbols = get_bnf_syntax()
    command_message_elements = {
        "<Header>": "This is the basic command name. If the header ends with a question mark, the command is a query. The header may begin with a colon (:) character. If the command is concatenated with other commands, the beginning colon is required. Never use the beginning colon with command headers beginning with a star (*).",
        "<Mnenomic>": "This is a header subfunction. Some command headers have only one mnemonic. If a command header has multiple mnemonics, a colon (:) character always separates them from each other.",
        "<Argument>": "This is a quantity, quality, restriction, or limit associated with the header. Some commands have no arguments while others have multiple arguments. A <space> separates arguments from the header. A <comma> separates arguments from each other.",
        "<Comma>": "A single comma is used between arguments of multiple-argument commands. Optionally, there may be white space characters before and after the comma.",
        "<Space>": "A white space character is used between a command header and the related argument. Optionally, a white space may consist of multiple white space characters.",
    }
    command = "[:]<Header>[<Space><Argument>[<Comma> <Argument>]...]"
    query = ("[:]<Header>", "[:]<Header>[<Space><Argument> [<Comma><Argument>]...]")

    output(
        bnf_symbols,
        reason=None,
        pretty_print=True,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
    )
    output(
        command_message_elements,
        reason=None,
        pretty_print=True,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
    )
    output(
        command,
        reason=None,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
        pretty_print=True,
    )
    output(
        query,
        reason=None,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
        pretty_print=True,
    )


@cli.command("command-write")
@click.argument("address", type=str)
@click.argument("command", type=str)
@click_add_options(click_global_options)
@click.pass_context
def _command_write(
    ctx,
    address: str,
    command: str,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
):
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    inst = get_instrument(
        address=address,
        verbose=verbose,
    )
    if verbose:
        ic(command, len(command))
    result = inst.write(command)
    output(
        result,
        reason={"address": address, "command": command},
        tty=tty,
        dict_output=dict_output,
        verbose=verbose,
    )


@cli.command("command-query")
@click.argument("address", type=str)
@click.argument("command", type=str)
@click_add_options(click_global_options)
@click.pass_context
def _command_query(
    ctx,
    address: str,
    command: str,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
):
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    inst = get_instrument(
        address=address,
        verbose=verbose,
    )
    if verbose:
        ic(command, len(command))
    result = inst.query(command).strip()
    output(
        result,
        reason={"address": address, "command": command},
        tty=tty,
        dict_output=dict_output,
        verbose=verbose,
    )


@cli.command("addresses")
@click.option("--asrl", is_flag=True)
@click_add_options(click_global_options)
@click.pass_context
def _list_addresses(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    asrl: bool,
    verbose: bool = False,
):
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    # https://github.com/pyvisa/pyvisa-py/issues/282
    resources = get_resources(keep_asrl=asrl, verbose=verbose)
    if verbose:
        ic(resources)
    for resource in resources:
        output(resource, reason=None, tty=tty, dict_output=dict_output, verbose=verbose)


@cli.command("idns")
@click.option("--asrl", is_flag=True)
@click_add_options(click_global_options)
@click.pass_context
def _list_idns(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    asrl: bool,
    verbose: bool = False,
):
    dict_output = True  # this does not take input on stdin, todo: fix dict_output convention to reflect this
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    resources = get_resources(keep_asrl=asrl, verbose=verbose)
    for resource in resources:
        if verbose:
            ic(resource)
        try:
            output(
                command_idn(address=resource, verbose=verbose),
                reason=resource,
                tty=tty,
                verbose=verbose,
                dict_output=dict_output,
            )
        except VisaIOError as e:
            if verbose:
                ic(e)
            if not e.args[0].endswith("Timeout expired before operation completed."):
                raise e
