#!/usr/bin/env python3
import array
import os

from .common import *


class VFF:
    """Represents a Wii VFF. Can extract and list files.
       Reference: http://wiibrew.org/wiki/VFF

       Original code by marcan: https://mrcn.st/t/vffdump.py

       Args:
           file (str): Path to a file
    """
    # TODO: Add dump_file() function
    # TODO: Add is_directory() to FileEntry class (along with other attributes)

    MAGIC = b"VFF "
    CLUSTERSIZE = 0x200

    class Header(BigEndianStructure):
        _pack_ = 1
        _fields_ = [
            ("magic", ARRAY(c_char, 4)),
            ("unknown1", ARRAY(c_byte, 2)),
            ("unknown2", ARRAY(c_byte, 2)),
            ("fileSize", c_uint32),
            ("headerSize", c_uint16),
            ("padding", ARRAY(c_byte, 18))
        ]

    class FAT:
        """Represents the File Allocation Table."""

        CLUSTERSIZE = 0x200

        def __init__(self, fp, clustercount):
            if clustercount < 4085:
                # FAT12
                self.type = 12
                self.reserved = 0xFF0
                code = "B"
            elif clustercount < 65525:
                # FAT16
                self.type = 16
                self.reserved = 0xFFF0
                code = "H"
            else:
                raise Exception("FAT type not supported")

            fatsize = (clustercount * self.type // 8 + self.CLUSTERSIZE - 1) & ~(self.CLUSTERSIZE - 1)  # Look @ WiiBrew
            data = fp.read(fatsize)
            self.array = array.array(code, data)

        @staticmethod
        def is_available(x):
            return x == 0x0000

        def is_used(self, x):
            return 0x0001 <= x < self.reserved

        def is_reserved(self, x):
            return self.reserved <= x <= (self.reserved + 6)

        def is_bad(self, x):
            return x == (self.reserved + 7)

        def is_last(self, x):
            return (self.reserved + 8) <= x

        def get_chain(self, start):
            chain = []
            clus = start
            while self.is_used(clus):
                chain.append(clus)
                clus = self[clus]
            if not self.is_last(clus):
                raise Exception("Found 0x%04x in cluster chain".format(clus))
            return chain

        def __getitem__(self, item):
            if self.type == 16:
                return self.array[item]
            else:
                off = (item // 2) * 3
                if item & 1:
                    return (self.array[off + 1] >> 4) | (self.array[off + 2] << 4)
                else:
                    return self.array[off] | ((self.array[off + 1] & 0xf) << 8)

    class Directory:
        """Represents the directory table of the FAT file system.
           Reference: https://en.wikipedia.org/wiki/Design_of_the_FAT_file_system#Directory_table
        """

        # FAT Attributes
        # Reference: https://en.wikipedia.org/wiki/Design_of_the_FAT_file_system#DIR_OFS_0Bh
        READONLY = 1  # Read only
        HIDDEN = 2  # Hidden
        SYSTEM = 4  # System file
        VOLUME_LABEL = 8  # Volume Label
        DIRECTORY = 16  # Directory
        ARCHIVE = 32  # Archive
        DEVICE = 64  # Device

        class FileEntry(LittleEndianStructure):
            # Reference: https://en.wikipedia.org/wiki/Design_of_the_FAT_file_system#Directory_entry
            _pack_ = 1
            _fields_ = [
                ("name", ARRAY(c_char, 8)),
                ("fileExtension", ARRAY(c_char, 3)),
                ("attributes", c_uint8),
                ("reserved", c_uint8),
                ("creationTimeMilliseconds", c_uint8),
                ("creationTime", c_uint16),
                ("creationDate", c_uint16),
                ("accessDate", c_uint16),
                ("extendedAttributes", c_uint16),
                ("lastModifiedTime", c_uint16),
                ("lastModifiedDate", c_uint16),
                ("offset", c_uint16),
                ("size", c_uint32)
            ]

            def get_name(self):
                """Returns file name."""
                return self.name.rstrip().decode()

            def get_file_extension(self):
                """Returns the file extensions."""
                return self.fileExtension.rstrip().decode()

            def get_full_name(self):
                """Returns the full file name with the extension."""
                fullname = "{0}.{1}".format(self.get_name(), self.get_file_extension())
                if fullname[-1] == ".":  # No file extension
                    fullname = fullname[:-1]
                return fullname

            def is_empty(self):
                """Returns True if file is deleted (0xE5) or empty (0x00)."""
                if not self.name:
                    return True
                if self.name[0] == 229:  # 0xE5 = deleted
                    return True
                else:
                    return False

            def __repr__(self):
                return self.get_full_name()

        def __init__(self, vff, data):
            self.vff = vff
            self.data = data
            self.entries = []
            for i in range(0, len(self.data), sizeof(self.FileEntry)):
                entry = self.data[i:i + sizeof(self.FileEntry)]
                file = self.FileEntry.from_buffer_copy(entry)
                if file.is_empty():
                    continue
                # https://en.wikipedia.org/wiki/Design_of_the_FAT_file_system#VFAT_long_file_names
                if file.attributes & 0xF == 0xF:
                    continue
                self.entries.append(file)

        def ls(self, pre=""):
            """Lists a directory."""
            for file in self.entries:
                fullname = file.get_full_name()
                if file.attributes & self.DIRECTORY:
                    if fullname in [".", ".."]:
                        continue
                    print("{0}/{1}/".format(pre, fullname))
                    self[fullname].ls("{0}/{1}".format(pre, fullname))
                else:
                    print("{0}/{1} [{2} bytes]".format(pre, fullname, file.size))

        def dump(self, path):
            """Dumps the whole filesystem to path."""
            if not os.path.isdir(path):
                os.makedirs(path)

            for file in self.entries:
                fullname = file.get_full_name()
                if file.attributes & self.DIRECTORY:
                    if fullname in [".", ".."]:
                        continue
                    print("{0}/{1}/".format(path, fullname))
                    self[fullname].dump("{0}/{1}".format(path, fullname))
                else:
                    print("{0}/{1} [{2} bytes]".format(path, fullname, file.size))
                    with open("{0}/{1}".format(path, fullname), "wb") as dumpfile:
                        dumpfile.write(self[fullname])

        def __getitem__(self, d):
            for file in self.entries:
                if file.get_full_name().lower() == d.lower():
                    if file.attributes & self.DIRECTORY:
                        return VFF.Directory(self.vff, self.vff.read_chain(file.offset))
                    elif not file.size:
                        return ""
                    else:
                        return self.vff.read_chain(file.offset)[:file.size]

    def __init__(self, file):
        self.fp = open(str(file), 'r+b')
        self.header = self.Header.from_buffer_copy(self.fp.read(sizeof(self.Header)))

        if self.header.magic != self.MAGIC:
            raise Exception("This is not a valid VFF file (wrong header magic).")

        if self.header.fileSize != os.path.getsize(file):
            raise Exception("This is not a valid VFF file (wrong size).")

        if self.header.headerSize != sizeof(self.Header):
            raise Exception("This is not a valid VFF file (wrong header size).")

        self.clustercount = self.header.fileSize // self.CLUSTERSIZE
        self.fat1 = self.FAT(self.fp, self.clustercount)
        self.fat2 = self.FAT(self.fp, self.clustercount)

        self.root = self.Directory(self, self.fp.read(0x1000))
        self.offset = self.fp.tell()

    def dump(self, path):
        """Shortcut for self.root.dump()."""
        self.root.dump(path)

    def read_cluster(self, num):
        num -= 2
        self.fp.seek(self.offset + self.CLUSTERSIZE * num)
        clus = self.fp.read(self.CLUSTERSIZE)
        return clus

    def read_chain(self, start):
        clusters = self.fat1.get_chain(start)
        data = b""
        for c in clusters:
            data += self.read_cluster(c)
        return data

    def __del__(self):
        self.fp.close()

    def __repr__(self):
        return "Wii VFF: {0} bytes with {1} clusters (FAT{2})".format(self.header.fileSize, self.clustercount,
                                                                      self.fat1.type)

    def __str__(self):
        output = "VFF:\n"
        output += "  Size: {0} bytes\n".format(self.header.fileSize)
        output += "  Cluster size: {0}\n".format(self.CLUSTERSIZE)
        output += "  Number of clusters: {0}\n".format(self.clustercount)
        output += "  FAT type: FAT{0}\n".format(self.fat1.type)

        return output
