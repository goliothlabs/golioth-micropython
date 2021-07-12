# Golioth SDK for MicroPython

Adding support for building IoT devices using Golioth and Micropython.

- Samples
  - [LightDB](./samples/main.py)

### Download and Install MicroPython (Work In Progress)

We forked MicroPython to add support for DTLS. Soon we are gonna add instruction on how to build.

### Install tools

```
$ pip3 install adafruit-ampy
$ pip3 install esptool
```

### Find serial port

```
$ ls /dev/tty.*
# In my case was /dev/tty.SLAB_USBtoUART
```

### Clean flash and send micropython binary

```
$ esptool.py --port /dev/tty.SLAB_USBtoUART erase_flash
$ esptool.py --chip esp32 --port /dev/tty.SLAB_USBtoUART --baud 460800 write_flash -z 0x1000 esp32.bin
```

### Install Libraries

```
$ ampy --port /dev/tty.SLAB_USBtoUART put lib/microCoAPy/microcoapy
```

### Copy Sample

```
$ ampy --port /dev/tty.SLAB_USBtoUART put samples/main.py main.py
```

## References

- Micro CoAP Implementation - https://github.com/insighio/microCoAPy
  - We vendored it temporarely to add more features like observation, ping and asyncio.
  - [MicroCoAPy](./lib/microCoAPy)
