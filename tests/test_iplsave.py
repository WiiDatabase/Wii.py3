#!/usr/bin/env python3
from binascii import hexlify

import pytest

import Wii


class TestIplSave:
    def test_creation(self):
        obj = Wii.IplSave()
        assert obj.magic == obj.MAGIC
        assert bytes(obj.unknown1) == b"\x00\x00\x00\x03\x00\x00\x00\x00"
        assert obj.channels[0].flags == 15
        assert obj.channels[0].type == 1
        assert obj.channels[0].secondaryType == 1
        assert hexlify(obj.generate_md5()) == b"4ebf1b1fc9faca24ba1be13d5121b86b"
        assert obj.get_used_blocks() == 1
        assert obj.get_free_blocks() == 47
        assert obj.get_disc_channel_index() == 0
        assert obj.channels[0].is_used()
        assert obj.channels[0].is_disc_channel()

    def test_file(self):
        obj = Wii.IplSave("tests/data/iplsave.bin")
        assert obj.magic == obj.MAGIC
        assert obj.get_used_blocks() == 16
        assert obj.get_free_blocks() == 32

        assert obj.channels[0].flags == 15
        assert obj.channels[0].type == 1
        assert obj.channels[0].secondaryType == 1
        assert obj.get_disc_channel_index() == 0

        tids_should_be = [
            "0000000000000000", "0001000248414341", "0001000248414141", "0001000248414241", "0001000248414650",
            "0001000248414750", "0001000248435641", "0001000248435550", "000100014f484243", "0001000148435250",
            "0001000148415650", "0001000148415050", "0001000148414a50", "0001000148414450", "00010001354e4541",
            "000100014a415650"
        ]
        for i in range(obj.get_free_blocks()):
            tids_should_be.append("0000000000000000")

        tids = []
        for channel in obj.channels:
            tids.append(channel.get_titleid())
        assert tids == tids_should_be

        id4s_should_be = [
            "", "HACA", "HAAA", "HABA", "HAFP", "HAGP", "HCVA", "HCUP",
            "OHBC", "HCRP", "HAVP", "HAPP", "HAJP", "HADP", "5NEA", "JAVP"
        ]
        for i in range(obj.get_free_blocks()):
            id4s_should_be.append("")

        id4s = []
        for channel in obj.channels:
            id4s.append(channel.get_id4())
        assert id4s == id4s_should_be

        assert obj.get_channel_by_id4("OHBC").get_titleid() == "000100014f484243"
        assert obj.get_channel_index_by_id4("OHBC") == 8
        assert obj.get_channel_by_titleid("0001000248435641").get_id4() == "HCVA"
        assert obj.get_channel_index_by_titleid("0001000248435641") == 6

    def test_file_modification(self, tmpdir):
        obj = Wii.IplSave("tests/data/iplsave.bin")
        obj.add_disc_channel(0, 0, 3)
        obj.move_channel(3, 2, 0, 1, 1, 2)

        obj.dump(tmpdir + "/iplsave.bin")

        new_obj = Wii.IplSave(tmpdir + "/iplsave.bin")
        assert not new_obj.channels[0].is_used()
        assert new_obj.get_disc_channel_index() == 36
        assert not new_obj.channels[11].is_used()
        assert obj.get_channel_index_by_id4("HAPP") == 29

    def test_exceptions(self):
        obj = Wii.IplSave("tests/data/iplsave.bin")

        with pytest.raises(LookupError):
            obj.get_channel_by_id4("LULZ")
            obj.get_channel_by_titleid("0001000333333333")
            obj.move_channel(1, 1, 1, 0, 0, 3)

        with pytest.raises(ValueError):
            obj.move_channel(1, 0, 0, 0, 0, 0)
            obj.add_disc_channel(99, 99, 99)
