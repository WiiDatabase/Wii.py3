#!/usr/bin/env python3
import os

import Wii


class TestIplSave:
    def test_file(self):
        obj = Wii.VFF("tests/data/wc24dl.vff")
        assert obj.header.magic == obj.MAGIC
        assert obj.header.fileSize == 90112
        assert obj.header.headerSize == 32
        assert obj.offset == 5152
        assert obj.fat1.type == 12

        assert obj.root.entries[0].get_full_name() == "MB"
        assert not obj.root.entries[0].is_empty()

        assert obj.root.entries[1].get_full_name() == "DISTMAP.BIN"
        assert not obj.root.entries[1].is_empty()

        assert obj.root.entries[2].get_full_name() == "GHOST.BIN"
        assert not obj.root.entries[2].is_empty()

        assert obj.root["MB"].entries[0].attributes == 16
        assert obj.root["MB"].entries[1].attributes == 16
        assert len(obj.root["DISTMAP.BIN"]) == 20870
        assert len(obj.root["GHOST.BIN"]) == 2876

    def test_dumping(self, tmpdir):
        obj = Wii.VFF("tests/data/wc24dl.vff")
        obj.dump(tmpdir + "/wc24dl_extracted")
        assert os.path.getsize(tmpdir + "/wc24dl_extracted/DISTMAP.BIN") == 20870
        assert os.path.getsize(tmpdir + "/wc24dl_extracted/GHOST.BIN") == 2876
        assert os.path.isdir(tmpdir + "/wc24dl_extracted/MB")
