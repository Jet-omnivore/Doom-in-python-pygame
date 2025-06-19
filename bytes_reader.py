import struct
import ctypes


def read_int32(file, offset):
    file.seek(offset)
    return (struct.unpack('i', file.read(4))[0])


def read_string(file, offset, string_length=8):
    file.seek(offset)
    s = ''
    for _ in range(string_length):
        s_ = str(struct.unpack('c', file.read(1))[0], 'ascii')
        if ord(s_):
            s += s_
    return s


def read_int16(file, offset):
    file.seek(offset)
    return struct.unpack('h', file.read(2))[0]

def read_color_value(file, offset):
    file.seek(offset)
    return struct.unpack('B', file.read(1))[0]

def read_uint16(file, offset):
    file.seek(offset)
    return ctypes.c_uint16(struct.unpack('h', file.read(2))[0]).value

def read_uint8(file, offset):
    file.seek(offset)
    return ctypes.c_uint8(struct.unpack('B', file.read(1))[0]).value

def read_uint32(file, offset):
    file.seek(offset)
    return ctypes.c_uint32(struct.unpack('i', file.read(4))[0]).value
