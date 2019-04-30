#!/usr/bin/env python3
import pytest

import Wii


class TestLocDat:
    def test_creation(self):
        obj = Wii.LocDat()
        assert obj.magic == obj.MAGIC
        assert obj.get_md5_hash() == "24efb66fb25baa9a74f5c0e970d5264e"
        assert obj.get_used_blocks() == 0
        assert obj.get_free_blocks() == 240

    def test_file(self):
        obj = Wii.LocDat("tests/data/loc.dat")
        assert obj.magic == obj.MAGIC
        assert obj.get_used_blocks() == 47
        assert obj.get_free_blocks() == 193

        tids_should_be = [
            "46414750", "4642324c", "46425950", "46435750", "46414b50", "46425a50", "4a414450", "4a414150", "4a415650",
            "4a43424d", "4e414150", "4e414450", "4e415550", "4e415a50", "4e414550", "4e414b50", "4e414c50", "4e414250",
            "4e414350", "4e415250", "4a435750", "46424450", "46425250", "4d414850", "4d424250", "4d434450", "4e414850",
            "4e544c43", "00000000", "00000000", "00000000", "00000000", "00000000", "574a4550", "57534e50", "57575250",
            "57435650", "57524c50", "57413450", "574d3850", "57585050", "57544b50", "57474f50", "57464c50", "534d4758",
            "48415650", "48414450", "48435250", "48435850", "48415050", "48415450", "00000000", "00000000", "00000000",
            "00000000", "00000000", "00000000", "00000000", "00000000", "00000000", "00000000", "00000000", "00000000",
            "00000000", "00000000", "00000000", "00000000", "00000000", "00000000", "00000000", "00000000", "4d424d50"
        ]
        for i in range(168):  # Rest is just empty
            tids_should_be.append("00000000")

        tids = []
        for channel in obj.channels:
            tids.append(channel.get_titleid())
        assert tids == tids_should_be

        id4s_should_be = [
            "FAGP", "FB2L", "FBYP", "FCWP", "FAKP", "FBZP", "JADP", "JAAP", "JAVP", "JCBM", "NAAP", "NADP", "NAUP",
            "NAZP", "NAEP", "NAKP", "NALP", "NABP", "NACP", "NARP", "JCWP", "FBDP", "FBRP", "MAHP", "MBBP", "MCDP",
            "NAHP", "NTLC", "", "", "", "", "", "WJEP", "WSNP", "WWRP", "WCVP", "WRLP", "WA4P", "WM8P", "WXPP", "WTKP",
            "WGOP", "WFLP", "SMGX", "HAVP", "HADP", "HCRP", "HCXP", "HAPP", "HATP", "", "", "", "", "", "", "", "", "",
            "", "", "", "", "", "", "", "", "", "", "", "MBMP"
        ]
        for i in range(168):  # Rest is just empty
            id4s_should_be.append("")

        id4s = []
        for channel in obj.channels:
            id4s.append(channel.get_id4())
        assert id4s == id4s_should_be

        assert obj.get_channel_by_id4("SMGX").get_titleid() == "534d4758"
        assert obj.get_channel_index_by_id4("SMGX") == 44
        assert obj.get_channel_by_titleid("48415650").get_id4() == "HAVP"
        assert obj.get_channel_index_by_titleid("48415650") == 45

    def test_file_modification(self, tmpdir):
        obj = Wii.LocDat("tests/data/loc.dat")
        obj.move_channel(0, 0, 0, 0, 0, 19)
        obj.add_channel_by_id4("HAXX", 1, 1, 15)
        obj.add_channel_by_titleid("54455354", 0, 2, 9)

        obj.dump(tmpdir + "/loc.dat")

        new_obj = Wii.LocDat(tmpdir + "/loc.dat")
        assert new_obj.get_md5_hash() == "e4b1e0e756ef7cd7794fc74b29f372a0"
        assert new_obj.get_used_blocks() == 49
        assert new_obj.get_free_blocks() == 191
        assert not new_obj.channels[0].is_used()
        assert new_obj.get_channel_index_by_id4("HAXX") == 185
        assert new_obj.get_channel_index_by_titleid("54455354") == 116

    def test_exception(self):
        obj = Wii.LocDat("tests/data/loc.dat")

        with pytest.raises(LookupError):
            obj.get_channel_by_id4("LULZ")
            obj.get_channel_by_titleid("99999999")
            obj.move_channel(1, 1, 19, 0, 0, 3)

        with pytest.raises(ValueError):
            obj.move_channel(1, 0, 0, 0, 0, 0)
            obj.add_channel_by_id4("HAXX", 99, 99, 99)
