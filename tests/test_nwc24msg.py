#!/usr/bin/env python3
import Wii


class TestNWC24msg:
    def test_creation(self):
        obj = Wii.NWC24msg()
        assert obj.magic == obj.MAGIC
        assert obj.version == 8
        assert obj.friendCode == 9999999999999999

        assert obj.get_mail_domain() == "@wii.com"
        assert obj.get_password() == "Wii.py3"
        assert obj.get_mlchkid() == "GeneratedWithWiipy3"
        assert obj.get_engine_urls() == [
            "https://amw.wc24.wii.com/cgi-bin/account.cgi",
            "http://rcw.wc24.wii.com/cgi-bin/check.cgi",
            "https://mtw.wc24.wii.com/cgi-bin/receive.cgi",
            "https://mtw.wc24.wii.com/cgi-bin/delete.cgi",
            "https://mtw.wc24.wii.com/cgi-bin/send.cgi"
        ]

        assert obj.generate_checksum() == 2557606060

    def test_file(self):
        # NOTE: Password and Mail Check ID have been replaced from a real file
        obj = Wii.NWC24msg("tests/data/nwc24msg.cfg")
        assert obj.magic == obj.MAGIC
        assert obj.version == 8
        assert obj.titleBooting == 0
        assert obj.friendCode == 7615213554627182
        assert obj.idGeneration == 7

        assert obj.get_mail_domain() == "@wii.com"
        assert obj.get_password() == "PHDBABfqeiAxWZFa"
        assert obj.get_mlchkid() == "3f715346482aaddg61a112d2af5a3192"
        assert obj.get_engine_urls() == [
            "https://amw.wc24.wii.com/cgi-bin/account.cgi",
            "http://rcw.wc24.wii.com/cgi-bin/check.cgi",
            "https://mtw.wc24.wii.com/cgi-bin/receive.cgi",
            "https://mtw.wc24.wii.com/cgi-bin/delete.cgi",
            "https://mtw.wc24.wii.com/cgi-bin/send.cgi"
        ]

        assert obj.generate_checksum() == 3307623949

    def test_file_modification(self, tmpdir):
        obj = Wii.NWC24msg("tests/data/nwc24msg.cfg")
        obj.set_mail_domain("example.com")
        obj.set_password("WiiPy3Password")
        obj.set_mlchkid("WiiPy3MailCheckID")
        obj.set_engine_url(0, "https://example.com/account")
        obj.set_engine_url(1, "https://example.com/check")
        obj.set_engine_url(2, "https://example.com/receive")
        obj.set_engine_url(3, "https://example.com/delete")
        obj.set_engine_url(4, "https://example.com/send")
        obj.dump(tmpdir + "/nwc24msg.cfg")

        new_obj = Wii.NWC24msg(tmpdir + "/nwc24msg.cfg")
        assert new_obj.get_mail_domain() == "@example.com"
        assert new_obj.get_password() == "WiiPy3Password"
        assert new_obj.get_mlchkid() == "WiiPy3MailCheckID"
        assert new_obj.get_engine_urls() == [
            "https://example.com/account",
            "https://example.com/check",
            "https://example.com/receive",
            "https://example.com/delete",
            "https://example.com/send"
        ]
        assert new_obj.generate_checksum() == 381436838
