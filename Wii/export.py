#!/usr/bin/env python3
import os
from binascii import hexlify
from copy import copy

from .common import *


class Savegame:
    """Represents a Wii savegame 'data.bin'
       Reference: http://wiibrew.org/wiki/Savegame_Files

       Args:
           file (str): Path to a file
    """
    # TODO: Certificates at end of file

    BANNERMAGIC = b"WIBN"
    BACKUPMAGIC = b"Bk"
    FILEMAGIC = b"\x03\xad\xf1\x7e"

    class Header(BigEndianStructure):

        class MainHeader(BigEndianStructure):
            _pack_ = 1
            _fields_ = [
                ("savegameID", c_uint64),
                ("bannerSize", c_uint32),
                ("permissions", c_uint8),
                ("unknown1", c_byte),
                ("md5", ARRAY(c_byte, 16)),
                ("unknown2", ARRAY(c_byte, 2)),
            ]

            def get_md5_hash(self):
                """Returns MD5 hash as string."""
                return hexlify(bytes(self.md5)).decode()

            def get_icon_count(self):
                """Return snumber of banner icons."""
                if self.bannerSize != 0x72A0:
                    return 8
                else:
                    return 1

            def __repr__(self):
                return "Savegame Main Header for ID {0}".format(self.savegameID)

            def __str__(self):
                output = "  Main header:\n"
                output += "    Savegame ID: {0}\n".format(self.savegameID)
                output += "    Banner size: {0} bytes\n".format(self.bannerSize)
                output += "    Permissions: {0}\n".format(self.permissions)
                output += "    MD5 hash: {0}\n".format(self.get_md5_hash())

                return output

        class Banner(BigEndianStructure):
            _pack_ = 1
            _fields_ = [
                ("magic", ARRAY(c_char, 4)),
                ("flags", c_uint32),
                ("animationSpeed", c_uint16),
                ("reserved", ARRAY(c_byte, 22)),
                ("gameTitle", ARRAY(c_byte, 64)),
                ("gameSubTitle", ARRAY(c_byte, 64)),
                ("banner", ARRAY(c_byte, 24576)),
                ("icon0", ARRAY(c_byte, 4608)),
                ("icon1", ARRAY(c_byte, 4608)),
                ("icon2", ARRAY(c_byte, 4608)),
                ("icon3", ARRAY(c_byte, 4608)),
                ("icon4", ARRAY(c_byte, 4608)),
                ("icon5", ARRAY(c_byte, 4608)),
                ("icon6", ARRAY(c_byte, 4608)),
                ("icon7", ARRAY(c_byte, 4608))
            ]

            def can_be_copied(self):
                """Returns True if the savegame can be copied to SD/NAND."""
                if self.flags == 1:
                    return False
                else:
                    return True

            def get_game_title(self):
                """Returns the game title."""
                return bytes(self.gameTitle).rstrip(b"\x00").decode("utf-16-be")

            def get_game_subtitle(self):
                """Returns the game title."""
                return bytes(self.gameSubTitle).rstrip(b"\x00").decode("utf-16-be")

            def __repr__(self):
                return "Savegame Banner Header for {0}".format(self.get_game_title())

            def __str__(self):
                output = "  Banner header:\n"
                output += "    Game Title: {0}\n".format(self.get_game_title())
                output += "    Game Subtitle: {0}\n".format(self.get_game_subtitle())
                output += "    Copying possible: {0}\n".format(self.can_be_copied())

                return output

        _pack_ = 1
        _fields_ = [
            ("main", MainHeader),
            ("banner", Banner)
        ]

        def pack(self, encrypt=True):
            """Optionally encrypts data before packing."""
            if encrypt:
                pack = Crypto.encrypt_data(SDKEY, SDIV, bytes(self), align=True)
            else:
                pack = bytes(self)
            return pack

        def dump(self, filename, encrypt=True):
            """Dumps Struct to filename. Returns the filename. Defaults to encrypted."""
            with open(filename, "wb") as file:
                file.write(self.pack(encrypt=encrypt))
                return file.name

        def generate_md5(self):
            """Generates the md5sum."""
            headercopy = copy(self)
            headercopy.main.md5 = ARRAY(c_byte, sizeof(headercopy.main.md5)).from_buffer_copy(MD5BLANKER)
            return Crypto.create_md5hash(headercopy.pack(encrypt=False))

        def update_md5(self):
            """Updates the md5sum in the Struct."""
            self.main.md5 = ARRAY(c_byte, sizeof(self.main.md5)).from_buffer_copy(self.generate_md5())

        def __repr__(self):
            return "Savegame Header for {0}".format(self.banner.get_game_title())

        def __str__(self):
            output = str(self.main)
            output += "\n"
            output += str(self.banner)

            return output

    class BkHeader(BigEndianStructure):
        _pack_ = 1
        _fields_ = [
            ("headerSize", c_uint32),
            ("magic", ARRAY(c_char, 2)),
            ("version", c_uint16),
            ("NGid", c_uint32),
            ("filesCount", c_uint32),
            ("filesSize", c_uint32),
            ("unknown1", ARRAY(c_byte, 4)),
            ("unknown2", ARRAY(c_byte, 4)),
            ("totalSize", c_uint32),
            ("unknown3", ARRAY(c_byte, 64)),
            ("unknown4", ARRAY(c_byte, 4)),
            ("gameID", ARRAY(c_char, 4)),
            ("macAddress", ARRAY(c_uint8, 6)),
            ("unknown5", ARRAY(c_byte, 2)),
            ("padding", ARRAY(c_byte, 16))
        ]

        def get_gameid(self):
            """Returns the Game ID."""
            return self.gameID.decode()

        def get_mac_address(self):
            """Returns the MAC address of the Wii the savegame belongs to."""
            macaddr = "{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(
                self.macAddress[0], self.macAddress[1], self.macAddress[2], self.macAddress[3],
                self.macAddress[4], self.macAddress[5]
            )
            return macaddr

        def get_region(self):
            """Returns the savegame's region."""
            regioncodes = {
                "P": "Europe",
                "E": "USA",
                "J": "Japan",
                "K": "Korea"
            }
            try:
                return regioncodes[self.get_gameid()[3]]
            except KeyError:
                return "Free"

        def get_blocks(self):
            """Returns savedata size in blocks, rounded to next integer."""
            return int(round(self.totalSize / 131072, 0))

        def __repr__(self):
            return "Savegame Backup Header for {0}".format(self.get_gameid())

        def __str__(self):
            output = "  Backup header:\n"
            output += "    Game ID: {0}\n".format(self.get_gameid())
            output += "    Region: {0}\n".format(self.get_region())
            output += "    Wii ID: {0}\n".format(self.NGid)
            output += "    Wii MAC Address: {0}\n".format(self.get_mac_address())
            output += "    Files found: {0}\n".format(self.filesCount)
            output += "    Size of files: {0} bytes\n".format(self.filesSize)
            output += "    Savegame size: {0} bytes ({1} block{2})\n".format(
                self.totalSize,
                self.get_blocks(),
                "" if self.get_blocks() == 1 else "s"
            )

            return output

    class File(BigEndianStructure):

        class FileHeader(BigEndianStructure):
            _pack_ = 1
            _fields_ = [
                ("magic", ARRAY(c_byte, 4)),
                ("size", c_uint32),
                ("permissions", c_uint8),
                ("attribute", c_uint8),
                ("type", c_uint8),
                ("namedata", ARRAY(c_byte, 117))
            ]

        _pack_ = 1
        _fields_ = [
            ("header", FileHeader)
        ]

        def get_name(self):
            """Returns the file name."""
            return bytes(self.header.namedata).split(b"\x00")[0].decode()

        def is_file(self):
            """Returns True if the file is a file and False if it's a directory."""
            if self.header.type == 1:
                return True
            else:
                return False

        def encrypt_data(self):
            """Returns the encrypted file data."""
            return Crypto.encrypt_data(SDKEY, self.iv, self.data, align=True)

        def pack(self, encrypt=True):
            """Optionally encrypts the data before packing."""
            header = self.header.pack()
            if encrypt:
                file = self.encrypt_data()
            else:
                file = self.data
            return header + file

        def dump(self, filename, encrypt=True):
            """Dumps Struct to filename. Returns the filename. Defaults to encrypted."""
            with open(filename, "wb") as file:
                file.write(self.pack(encrypt=encrypt))
                return file.name

        def __repr__(self):
            return self.get_name()

    def __init__(self, file):
        fp = open(file, 'r+b')

        # Decrypt header
        headerbuffer = fp.read(0xF0C0)
        headerbuffer = Crypto.decrypt_data(SDKEY, SDIV, headerbuffer, align=True)
        self.header = self.Header.from_buffer_copy(headerbuffer)

        if self.header.banner.magic != self.BANNERMAGIC:
            raise Exception("This is not a valid Wii savegame (wrong banner magic).")

        # BkHeader is unencrypted
        bkheaderbuffer = fp.read(sizeof(self.BkHeader))
        self.bkHeader = self.BkHeader.from_buffer_copy(bkheaderbuffer)

        if self.bkHeader.magic != self.BACKUPMAGIC:
            raise Exception("This is not a valid Wii savegame (wrong backup magic).")

        if self.header.generate_md5() != bytes(self.header.main.md5):
            print("Header MD5 sum mismatch!")

        # Files
        self.files = []
        for i in range(self.bkHeader.filesCount):
            filehdr = fp.read(sizeof(self.File))
            self.files.append(self.File.from_buffer_copy(filehdr))
            self.files[i].iv = filehdr[0x050:0x050 + 16]  # IV is always at 0x050 in the file header
            filedata = fp.read(align_value(self.files[i].header.size))
            dec_filedata = Crypto.decrypt_data(SDKEY, self.files[i].iv, filedata)
            self.files[i].data = dec_filedata

        for file in self.files:
            if bytes(file.header.magic) != self.FILEMAGIC:
                raise Exception("This is not a valid Wii savegame (wrong file magic for {0}).".format(file.get_name()))

        fp.close()

    def extract_files(self, directory, encrypt=False):
        """Extracts all files from the savegame to a directory. If `encrypt` is True, files will be encrypted."""
        if not os.path.isdir(directory):
            os.makedirs(directory)

        for file_obj in self.files:
            if file_obj.is_file():
                with open(os.path.join(directory, file_obj.get_name()), "wb") as file:
                    if encrypt:
                        file.write(file_obj.encrypt_data())
                    else:
                        file.write(file_obj.data)
            else:
                os.mkdir(os.path.join(directory, file_obj.get_name()))

    def erase_mac_address(self):
        """Sets the Wii MAC to 00."""
        self.bkHeader.macAddress = ARRAY(c_uint8, 6).from_buffer_copy(b"\x00" * 6)

    def pack(self, encrypt=True):
        """Optionally encrypts the data before packing."""
        header = self.header.pack(encrypt=encrypt)
        bkheader = self.bkHeader.pack()
        files = b""
        for file in self.files:
            files += file.pack(encrypt=encrypt)
        return header + bkheader + files

    def dump(self, filename, encrypt=True):
        """Dumps Struct to filename. Returns the filename. Defaults to encrypted."""
        with open(filename, "wb") as file:
            file.write(self.pack(encrypt=encrypt))
            return file.name

    def __repr__(self):
        return "Wii Savegame for {0}".format(self.bkHeader.get_gameid())

    def __str__(self):
        output = "Wii Savegame:\n"
        output += str(self.header)
        output += "\n"
        output += str(self.bkHeader)

        return output
