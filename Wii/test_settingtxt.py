#!/usr/bin/env python3
import pytest

import Wii


class TestSettingTXT:
    def test_creation(self):
        obj = Wii.SettingTXT()
        assert obj.get_area() == "EUR"
        assert obj.get_model() == "RVL-001(EUR)"
        assert obj.get_dvd() == "0"
        assert obj.get_mpch() == "0x7FFE"
        assert obj.get_code() == "LEH"
        assert obj.get_serial() == "133713379"
        assert obj.get_video() == "PAL"
        assert obj.get_game() == "EU"

    @staticmethod
    def _test_file(obj):
        assert obj.get_area() == "EUR"
        assert obj.get_model() == "RVL-001(EUR)"
        assert obj.get_dvd() == "0"
        assert obj.get_mpch() == "0x7FFE"
        assert obj.get_code() == "LEH"
        assert obj.get_serial() == "133789940"
        assert obj.get_video() == "PAL"
        assert obj.get_game() == "EU"

    def test_file_encrypted(self):
        # File created by ModMii
        obj = Wii.SettingTXT("tests/data/setting.txt")
        self._test_file(obj)

    def test_file_unencrypted(self):
        # Same file as above
        obj = Wii.SettingTXT("tests/data/setting_unencrypted.txt", encrypted=False)
        self._test_file(obj)

    @staticmethod
    def _test_file_modification(obj):
        assert obj.get_area() == "KOR"
        assert obj.get_model() == "RVL-001(KOR)"
        assert obj.get_dvd() == "1"
        assert obj.get_mpch() == "0x7FFF"
        assert obj.get_code() == "LUK"
        assert obj.get_serial() == "133713371"
        assert obj.get_video() == "NTSC"
        assert obj.get_game() == "KR"

    def test_file_modification(self, tmpdir):
        obj = Wii.SettingTXT("tests/data/setting.txt")
        obj.set_area("KOR")
        obj.set_model("RVL-001(KOR)")
        obj.set_dvd("1")
        obj.set_mpch("0x7FFF")
        obj.set_code("LUK")
        obj.set_serial("133713371")
        obj.set_video("NTSC")
        obj.set_game("KR")
        obj.dump(tmpdir + "/setting.txt")
        obj.dump(tmpdir + "/setting_unencrypted.txt", encrypt=False)

        self._test_file_modification(Wii.SettingTXT(tmpdir + "/setting.txt"))
        self._test_file_modification(Wii.SettingTXT(tmpdir + "/setting_unencrypted.txt", encrypted=False))

    def test_exceptions(self):
        obj = Wii.SettingTXT()
        with pytest.raises(KeyError):
            obj.get("NOTEXISTING")

        with pytest.raises(ValueError):
            obj.set("TESTVALUE", "EXAMPLE" * 200)
            
        with pytest.raises(LookupError):
            obj.delete("NOTEXISTING")
