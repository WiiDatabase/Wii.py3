#!/usr/bin/env python3
import Wii


class TestNWC24fl:
    def test_creation(self):
        obj = Wii.NWC24fl()
        assert obj.magic == obj.MAGIC
        assert obj.maxEntries == 100
        assert obj.friendCount == 0

    def test_file(self):
        obj = Wii.NWC24fl("tests/data/nwc24fl.bin")
        assert obj.magic == obj.MAGIC
        assert obj.maxEntries == 100
        assert obj.friendCount == 3

        assert obj.friendList[0].get_name() == "Example"
        assert obj.friendList[1].get_name() == "WiiDB.de"
        assert obj.friendList[2].get_name() == "testID"

        assert obj.friendList[0].get_friend_code() == "test@example.com"
        assert obj.friendList[1].get_friend_code() == 7135382492659598
        assert obj.friendList[2].get_friend_code() == 4252889816926870

        assert obj.friendList[0].miiID == 0
        assert obj.friendList[1].miiID == 2224914684
        assert obj.friendList[2].miiID == 0

        assert obj.friendList[0].get_status() == "Unconfirmed"
        assert obj.friendList[1].get_status() == "Unconfirmed"
        assert obj.friendList[2].get_status() == "Unconfirmed"
