#!/usr/bin/env python3
import hashlib
from ctypes import *


def pad_to_blocksize(value, block=64):
    """Pads value to blocksize.

    Args:
        value (bytes): Value to pad
        block (int): Block size (Default: 64)

    Returns:
        bytes: Padded value
    """
    if len(value) % block != 0:
        value += b"\x00" * (block - (len(value) % block))
    return value


def pad_to_cbyte_array(value, size):
    """Helper function: Pads value to size and packs it into a cbyte array with size as length.

    Args:
        value (bytes): Value to pad and pack
        size (int): Size of the cbyte array
    """
    value = pad_to_blocksize(value, size)
    value = ARRAY(c_byte, size).from_buffer_copy(value)
    return value


class BigEndianStructure(BigEndianStructure):
    """Extends BigEndianStructure class to optionally load bytes from file.

       Args:
           file (str[optional]): Path to a file
    """

    def __new__(cls, file=None):
        """Loads file intro Struct if given."""
        if file:
            fp = open(file, 'r+b')
            c_struct = cls.from_buffer_copy(fp.read(sizeof(cls)))
            fp.close()
            return c_struct
        else:
            return super().__new__(cls)

    def __init__(self, file=None):
        super().__init__()

    def pack(self):
        """Helper class which packs the Struct into a bytes object."""
        return bytes(self)

    def dump(self, filename):
        """Dumps Struct to filename. Returns the filename."""
        with open(filename, "wb") as file:
            file.write(self.pack())
            return file.name


class Crypto:
    """Cryptographic/Hash helper class."""

    @classmethod
    def create_md5hash(cls, data):
        """MD5 hashes a byte-string.

        Args:
            data (bytes): Data to hash

        Returns:
            bytes: MD5 hash
        """
        return hashlib.md5(data).digest()

    @classmethod
    def generate_checksum(cls, data):
        """Generates a checksum for NANDBOOTINFO, nwc24msg.cfg and probably more.
        Make sure to pass data without the checksum!

        Checksum calculation works like this:
          1) Break the entire file (without the checksum) into 4 byte groups
          2) Convert the bytes into an integer and add them all together
          3) Grab the lower 32 bits
        Reference: https://git.io/fj3iW

        Args:
            data (bytes): Data to generate checksum for

        Returns:
            int: The generated checksum
        """
        checksum = 0
        for block in range(0, len(data), 4):
            b = data[block:block + 4]
            checksum += int.from_bytes(b, byteorder="big")
        checksum &= 0xFFFFFFFF
        return checksum
