import struct
import numpy as np

def read_int32(file, offset):
    file.seek(offset)
    return (struct.unpack('i', file.read(4))[0])

def read_string(file, offset, string_length):
    file.seek(offset)
    s = ''
    for i in range(string_length):
        s_ = str(struct.unpack('c', file.read(1))[0], 'ascii')
        if ord(s_):
            s += s_
    return s

def read_int16(file, offset):
    file.seek(offset)
    return (struct.unpack('h', file.read(2))[0])

def read_uint16(file, offset):
    file.seek(offset)
    return np.uint16(struct.unpack('h', file.read(2))[0])

def read_uint32(file, offset):
    file.seek(offset)
    return np.uint32(struct.unpack('i', file.read(4))[0])
