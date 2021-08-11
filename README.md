**gpibtool**:  https://github.com/jakeogh/gpibtool


### Description:
gpibtool is a utility for sending and troubleshooting GPIB commands via the [PyVISA](https://pyvisa.readthedocs.io/en/latest) library.

gpibtool requires GPIB kernel drivers.

Use [linux-gpib-installer](https://github.com/jakeogh/linux-gpib-installer) to install the kernel drivers on a Debian 11 system.


### Installation:
```
$ sudo apt-get install python3-pip -y
$ pip install --force-reinstall git+https://git@github.com/jakeogh/gpibtool
$ source ~/.profile
```
### Examples:
```
$ gpibtool

$ gpibtool --help
Usage: gpibtool [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose
  --dict
  --verbose-inf
  --help         Show this message and exit.

Commands:
  addresses
  command-query
  command-write
  idn
  idns
  info
  syntax

$ # list current GPIB addresses:
$ gpibtool addresses
GPIB0::1::INSTR
GPIB0::2::INSTR
GPIB0::6::INSTR

$ # send the `*IDN?` command to each address:
$ gpibtool idns
{'GPIB0::1::INSTR': 'ODCI+0.0000E+0,V+1.0000E+0,W+3.0000E-3,L+1.0000E+0'}
{'GPIB0::2::INSTR': 'TEKTRONIX,AFG3022B,C037086,SCPI:99.0 FV:3.2.2'}
{'GPIB0::6::INSTR': 'KEITHLEY INSTRUMENTS INC.,MODEL 2410,1069942,C32   Oct  4 2010 14:20:11/A02  /K/H'}

$ # send the `*IDN?` command to an address:
$ gpibtool command-query "GPIB0::2::INSTR" "*IDN?"
TEKTRONIX,AFG3022B,C037086,SCPI:99.0 FV:3.2.2

$ # display troubleshooting info:
$ gpibtool info
Output of /usr/bin/pyvisa-info:
Machine Details:
   Platform ID:    Linux-5.19.0-gentoo-x86_64-x86_64-Intel-R-_Core-TM-_i7-4910MQ_CPU_@_2.90GHz-with-glibc2.36
   Processor:      Intel(R) Core(TM) i7-4910MQ CPU @ 2.90GHz

Python:
   Implementation: CPython
   Executable:     /usr/bin/python3.10
   Version:        3.10.7
   Compiler:       GCC 11.3.0
   Bits:           64bit
   Build:          Sep 27 2022 18:25:44 (#main)
   Unicode:        UCS4

PyVISA Version: 1.12.0

Backends:
   ivi:
      Version: 1.12.0 (bundled with PyVISA)
      Binary library: Not found
   py:
      Version: 0.5.3
      ASRL INSTR: Available via PySerial (3.5)
      USB INSTR: Available via PyUSB (1.2.1). Backend: libusb1
      USB RAW: Available via PyUSB (1.2.1). Backend: libusb1
      TCPIP INSTR: Available 
      TCPIP SOCKET: Available 
      GPIB INSTR: Available via Linux GPIB (b'4.3.5')
      GPIB INTFC: Available via Linux GPIB (b'4.3.5')
   sim:
      Version: 0.4.0
      Spec version: 1.1

Output of /usr/bin/lsusb:
Bus 003 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 026: ID 07a6:8511 ADMtek, Inc. ADM8511 Pegasus II Ethernet
Bus 001 Device 025: ID 3923:709b National Instruments Corp. GPIB-USB-HS
Bus 001 Device 024: ID 067b:2303 Prolific Technology, Inc. PL2303 Serial Port / Mobile Action MA-8910P
Bus 001 Device 023: ID 05e3:0608 Genesys Logic, Inc. Hub

```