#!/bin/sh

awk -v rc=1 "/AFG3022B/ { rc=0 } 1; END {exit rc}"
