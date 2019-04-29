#!/usr/bin/env python3
import os
from binascii import hexlify, unhexlify
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
            with open(str(filename), "wb") as file:
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
            with open(str(filename), "wb") as file:
                file.write(self.pack(encrypt=encrypt))
                return file.name

        def __repr__(self):
            return self.get_name()

    def __init__(self, file):
        fp = open(str(file), 'r+b')

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
                with open(str(os.path.join(directory, file_obj.get_name())), "wb") as file:
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
        with open(str(filename), "wb") as file:
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


class LocDat(BigEndianStructure):
    """Shows info for the "loc.dat" located used by the SD Card menu and present inside the "private" folder.
       Reference: http://wiibrew.org/wiki//shared2/wc24/nwc24fl.bin

       Args:
           file (str[optional]): Path to a file
    """

    MAGIC = b"sdal"

    class Channel(BigEndianStructure):
        _pack_ = 1
        _fields_ = [
            ("id4", ARRAY(c_byte, 4)),
        ]

        def delete(self):
            """Empties channel slot. Note that the Wii will re-populate it if it's on SD.
               NOTE: MD5 has to be updated!
            """
            self.id4 = ARRAY(c_byte, sizeof(self.id4)).from_buffer_copy(b"\x00" * sizeof(self.id4))

        def get_titleid(self):
            """Returns the lower title id of the channel."""
            return hexlify(bytes(self.id4)).decode()

        def get_id4(self):
            """Returns the Title ID4 of the channel."""
            return bytes(self.id4).decode()

        def is_used(self):
            """Returns True if there's a channel in the slot."""
            if bytes(self.id4) == b"\x00" * 4:
                return False
            else:
                return True

        def __repr__(self):
            return self.get_id4()

    _pack_ = 1
    _fields_ = [
        ("magic", ARRAY(c_char, 4)),
        ("md5", ARRAY(c_byte, 16)),
        ("channels", ARRAY(Channel, 240)),
        ("padding", ARRAY(c_byte, 12))
    ]

    def generate_md5(self):
        """Generates the md5sum."""
        filecopy = copy(self)
        filecopy.md5 = ARRAY(c_byte, sizeof(filecopy.md5)).from_buffer_copy(MD5BLANKER)
        return Crypto.create_md5hash(filecopy.pack(encrypt=False))

    def update_md5(self):
        """Updates the md5sum in the Struct."""
        self.md5 = ARRAY(c_byte, sizeof(self.md5)).from_buffer_copy(self.generate_md5())

    def get_used_blocks(self):
        """Returns the number of used channel slots."""
        used_blocks = 0
        for channel in self.channels:
            if channel.is_used():
                used_blocks += 1
        return used_blocks

    def get_free_blocks(self):
        """Returns the number of free channel slots."""
        return len(self.channels) - self.get_used_blocks()

    def _get_channel_by_id4_or_tid(self, search, by_titleid=False, return_index=False):
        """Helper function for get_channel_by_id4 and get_channel_by_titleid.

        Args:
            search (str): String to search for (ID4 or titleid)
            by_titleid (bool): Search by lower Title ID instead of ID4
            return_index (bool): Return index instead of Channel class
        """
        if by_titleid:
            if len(search) != 8:
                raise ValueError("Lower Title ID must be 8 characters long.")
        else:
            if len(search) != 4:
                raise ValueError("ID4 must be 4 characters long.")

        for i, channel in enumerate(self.channels):
            if by_titleid:
                if channel.get_titleid() == search.lower():
                    if return_index:
                        return i
                    else:
                        return channel
            else:
                if channel.get_id4() == search.upper():
                    if return_index:
                        return i
                    else:
                        return channel
        raise LookupError("Channel not found.")

    def get_channel_by_id4(self, id4):
        """Finds a channel by its ID4."""
        return self._get_channel_by_id4_or_tid(id4)

    def get_channel_index_by_id4(self, id4):
        """Finds a channel index in self.channels by its ID4."""
        return self._get_channel_by_id4_or_tid(id4, return_index=True)

    def get_channel_by_titleid(self, tid):
        """Finds a channel by its Title ID."""
        return self._get_channel_by_id4_or_tid(tid, by_titleid=True)

    def get_channel_index_by_titleid(self, tid):
        """Finds a channel index in self.channels by its Title ID."""
        return self._get_channel_by_id4_or_tid(tid, by_titleid=True, return_index=True)

    def _add_channel_by_id4_or_tid(self, tid, col, row, page, by_titleid=False):
        """Helper function for add_channel_by_id4 and add_channel_by_titleid.

        Args:
            tid (str): ID4 or lower Title ID
            col (int): Column in SD Card Menu (0-3)
            row (int): Row in SD Card Menu (0-2)
            page (int): Page in SD Card Menu (0-19)
            by_titleid (bool): Search by lower Title ID instead of ID4
        """
        if not 0 <= col <= 3 or not 0 <= row <= 2 or not 0 <= page <= 19:
            raise ValueError("Out of bounds.")

        if not by_titleid:  # ID4s must be big
            tid = tid.upper()

        try:
            if by_titleid:
                self._get_channel_by_id4_or_tid(tid, by_titleid=True)
            else:
                self._get_channel_by_id4_or_tid(tid)
            raise Exception("Channel already exists.")
        except LookupError:
            pass

        pos = (col + (row * 4) + (page * 12))
        channel = self.channels[pos]

        if channel.is_used():
            raise Exception("Destination is not free (used by {0}).".format(channel.get_id4()))

        if by_titleid:
            self.channels[pos].id4 = ARRAY(c_byte, 4).from_buffer_copy(unhexlify(tid.encode()))
        else:
            self.channels[pos].id4 = ARRAY(c_byte, 4).from_buffer_copy(tid.encode())
        self.update_md5()

    def add_channel_by_id4(self, id4, col, row, page):
        self._add_channel_by_id4_or_tid(id4, col, row, page)

    def add_channel_by_titleid(self, id4, col, row, page):
        self._add_channel_by_id4_or_tid(id4, col, row, page, by_titleid=True)

    def move_channel(self, col1, row1, page1, col2, row2, page2):
        """Moves channel from col1, row1, page1 to col2, row2, page2"""
        if not 0 <= col1 <= 3 or not 0 <= row1 <= 2 or not 0 <= page1 <= 19:
            raise ValueError("Source is out of bounds")
        if not 0 <= col2 <= 3 or not 0 <= row2 <= 2 or not 0 <= page2 <= 19:
            raise ValueError("Destination is out of bounds")
        if (col1, row1, page1) == (col2, row2, page2):
            raise ValueError("Title is already on this position")

        old_position = (col1 + (row1 * 4) + (page1 * 12))
        old_channel = self.channels[old_position]
        new_position = (col2 + (row2 * 4) + (page2 * 12))
        new_channel = self.channels[new_position]

        if not old_channel.is_used():
            raise Exception("No channel on source.")
        if new_channel.is_used():
            raise Exception("Destination is not free (used by {0}).".format(new_channel.get_id4()))

        self.channels[new_position] = self.channels[old_position]
        old_channel.delete()
        self.update_md5()

    def pack(self, encrypt=True):
        """Optionally encrypts data before packing."""
        if encrypt:
            pack = Crypto.encrypt_data(SDKEY, SDIV, bytes(self), align=False)
        else:
            pack = bytes(self)
        return pack

    def dump(self, filename, encrypt=True):
        """Dumps Struct to filename. Returns the filename. Defaults to encrypted."""
        with open(str(filename), "wb") as fp:
            fp.write(self.pack(encrypt=encrypt))
            return fp.name

    def __new__(cls, file=None):
        """Loads file intro Struct if given and decrypts it."""
        if file:
            with open(str(file), "rb") as fp:
                buffer = fp.read((sizeof(cls)))
            buffer = Crypto.decrypt_data(SDKEY, SDIV, buffer, align=False)
            c_struct = cls.from_buffer_copy(buffer)
            return c_struct
        else:
            return super().__new__(cls)

    def __repr__(self):
        return "Wii LocDat: {0} slot{1} used out of 240 ({2} free)".format(
            self.get_used_blocks(),
            "" if self.get_used_blocks() == 1 else "s",
            self.get_free_blocks()
        )

    def __str__(self):
        output = "LocDat:\n"
        output += "  Used {0} slot{1} out of 240 ({2} free)\n\n".format(
            self.get_used_blocks(),
            "" if self.get_used_blocks() == 1 else "s",
            self.get_free_blocks()
        )

        for page in range(20):
            output += "  Page {0}:\n    ".format(page + 1)
            for row in range(3):
                for slot in range(4):
                    curtitle = self.channels[(slot + (row * 4) + (page * 12))]
                    if curtitle.is_used():
                        output += "{0:8}".format(curtitle.get_id4())
                    else:
                        output += "{0:8}".format("Free")
                if row == 2:  # Last row
                    output += "\n\n"
                else:
                    output += "\n    "
        return output

    def __init__(self, file=None):
        if not file:
            self.magic = self.MAGIC
            self.update_md5()

        if self.magic != self.MAGIC:
            raise Exception("Not a valid NWC24fl file!")

        if self.generate_md5() != bytes(self.md5):
            print("MD5 sum mismatch!")

        super().__init__()
