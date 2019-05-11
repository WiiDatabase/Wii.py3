#!/usr/bin/env python3
import Wii


class TestNWC24dl:
    def test_creation(self):
        obj = Wii.NWC24dl()
        assert obj.magic == obj.MAGIC
        assert obj.unknown1 == 1
        assert obj.unknown2 == 32
        assert obj.reservedEntries == 8
        assert obj.maxEntries == 120
        for entry in obj.entries:
            assert entry.type == 255

        assert obj.get_used_entries() == 0
        assert obj.get_free_entries() == 120

    def test_file(self):
        obj = Wii.NWC24dl("tests/data/nwc24dl.bin")
        assert obj.magic == obj.MAGIC
        assert obj.unknown1 == 1
        assert obj.unknown2 == 32
        assert obj.reservedEntries == 8
        assert obj.maxEntries == 120

        assert obj.get_used_entries() == 21
        assert obj.get_free_entries() == 99

        assert not obj.records[0].is_empty()
        assert obj.records[0].get_id4() == "HAEA"
        assert obj.records[0].get_titleid() == "48414541"

        assert obj.records[2].is_empty()

        assert not obj.records[10].is_empty()
        assert obj.records[10].get_id4() == "RMCP"
        assert obj.records[10].get_titleid() == "524d4350"

        assert not obj.records[117].is_empty()
        assert obj.records[117].get_id4() == obj.entries[117].get_id4()
        assert obj.entries[117].get_url() == "http://mariokartwii.race.gs.wiimmfi.de/raceservice/maindl_eu_ge.ashx"
        assert obj.entries[117].get_filename() == "distmap.bin"
        assert obj.entries[117].get_type() == "Title Download"
        assert obj.entries[117].dlLeft == 32766

    def test_file_modification(self, tmpdir):
        obj = Wii.NWC24dl("tests/data/nwc24dl.bin")
        obj.entries[117].set_url("http://example.com")
        obj.entries[117].set_filename("example.bin")
        obj.entries[117].set_dl_left(2006)
        obj.entries[117].set_frequency(1337)

        obj.dump(tmpdir + "/nwc24dl.bin")

        new_obj = Wii.NWC24dl(tmpdir + "/nwc24dl.bin")
        assert new_obj.entries[117].get_url() == "http://example.com"
        assert new_obj.entries[117].get_filename() == "example.bin"
        assert new_obj.entries[117].dlLeft == 2006
        assert new_obj.entries[117].frequency == 1337
