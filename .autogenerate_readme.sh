#!/bin/sh

#tty:
gpibtool --help

# list current GPIB addresses:
#tty:
gpibtool addresses

# send the `*IDN?` command to each address:
#tty:
gpibtool idns

# send the `*IDN?` command to an address:
#tty:
gpibtool command-query "GPIB0::2::INSTR" "*IDN?"

# display troubleshooting info:
#tty:
gpibtool info
