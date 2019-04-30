#!/usr/bin/env python3
import os
from binascii import hexlify

import Wii


class TestSavegame:
    def test_file(self):
        obj = Wii.Savegame("tests/data/data.bin")
        assert obj.header.banner.magic == obj.BANNERMAGIC
        assert obj.bkHeader.magic == obj.BACKUPMAGIC
        assert hexlify(obj.header.generate_md5()) == b"6491bdf32bf1ef0bed029a84e4385647"

        assert obj.header.main.savegameID == 281476357506896
        assert obj.header.main.bannerSize == 29344
        assert obj.header.main.permissions == 60
        assert obj.header.main.get_md5_hash() == "6491bdf32bf1ef0bed029a84e4385647"
        assert obj.header.main.get_icon_count() == 1

        assert obj.header.banner.can_be_copied()
        assert obj.header.banner.animationSpeed == 3
        assert obj.header.banner.get_game_title() == "SUPER MARIO GALAXY"
        assert obj.header.banner.get_game_subtitle() == "Launch into a cosmic adventure!"

        assert obj.bkHeader.headerSize == 112
        assert obj.bkHeader.version == 1
        assert obj.bkHeader.NGid == 90852710
        assert obj.bkHeader.filesCount == 1
        assert obj.bkHeader.filesSize == 48768
        assert obj.bkHeader.totalSize == 49728
        assert obj.bkHeader.get_gameid() == "RMGP"
        assert obj.bkHeader.get_mac_address() == "00:25:a0:72:44:fd"
        assert obj.bkHeader.get_region() == "Europe"
        assert obj.bkHeader.get_blocks() == 1

        assert obj.files[0].get_name() == "GameData.bin"
        assert obj.files[0].is_file()
        assert hexlify(obj.files[0].iv) == b"7c3bdba41f6964f83866ae056a9f7005"

    def test_file_modification(self, tmpdir):
        tmpdir = str(tmpdir)
        obj = Wii.Savegame("tests/data/data.bin")
        obj.erase_mac_address()
        obj.bkHeader.set_gameid("ZMGP")
        obj.header.set_title("SUPER LUIGI GALAXY")
        obj.header.set_subtitle("Launch into a Luigi adventure!")
        obj.dump(tmpdir + "/data.bin")

        new_obj = Wii.Savegame(tmpdir + "/data.bin")
        assert new_obj.header.main.get_md5_hash() == hexlify(new_obj.header.generate_md5()).decode()
        assert new_obj.bkHeader.get_mac_address() == "00:00:00:00:00:00"
        assert obj.header.banner.get_game_title() == "SUPER LUIGI GALAXY"
        assert obj.header.banner.get_game_subtitle() == "Launch into a Luigi adventure!"
        assert new_obj.bkHeader.get_gameid() == "ZMGP"

    def test_dumping(self, tmpdir):
        tmpdir = str(tmpdir)
        obj = Wii.Savegame("tests/data/data.bin")
        obj.extract_files(tmpdir + "/savegame_extracted")
        assert os.path.getsize(tmpdir + "/savegame_extracted/" + obj.files[0].get_name()) == obj.files[0].get_size()
