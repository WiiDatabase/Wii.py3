#!/usr/bin/env python3
from ctypes import sizeof
import pytest

import Wii


class TestNetConfig:
    def test_creation(self):
        obj = Wii.NetConfig()
        assert bytes(obj.unknown2) == b"\x07\x00\x00"
        assert sizeof(obj.connections) == 6996

    def test_file(self):
        obj = Wii.NetConfig("tests/data/config.dat")
        assert obj.connected == 1

        assert obj.connections[0].is_selected()
        assert obj.connections[0].is_connected()
        assert not obj.connections[0].uses_proxy()
        assert obj.connections[0].is_ip_dhcp()
        assert not obj.connections[0].is_dns_dhcp()
        assert not obj.connections[0].is_lan()
        assert obj.connections[0].get_ssid() == "TestConnection"
        assert obj.connections[0].get_encryption_type() == "WPA2-PSK (AES)"
        assert obj.connections[0].get_key() == "TestPassword"
        assert obj.connections[0].get_mtu() == 0
        assert obj.connections[0].get_primary_dns() == "216.69.185.14"
        assert obj.connections[0].get_secondary_dns() == "173.201.71.14"

        assert not obj.connections[1].is_selected()
        assert not obj.connections[1].is_connected()
        assert obj.connections[1].uses_proxy()
        assert not obj.connections[1].is_ip_dhcp()
        assert not obj.connections[1].is_dns_dhcp()
        assert not obj.connections[1].is_lan()
        assert obj.connections[1].get_ssid() == "WEP64"
        assert obj.connections[1].get_encryption_type() == "WEP64"
        assert obj.connections[1].get_key() == "yY:ft"
        assert obj.connections[1].get_mtu() == 1500
        assert obj.connections[1].get_ip() == "192.168.0.16"
        assert obj.connections[1].get_netmask() == "255.255.255.255"
        assert obj.connections[1].get_gateway() == "192.168.0.0"
        assert obj.connections[1].get_primary_dns() == "8.8.8.8"
        assert obj.connections[1].get_secondary_dns() == "1.1.1.1"
        assert obj.connections[1].get_proxy_server() == "192.168.0.16"
        assert obj.connections[1].get_proxy_port() == 8888
        assert obj.connections[1].get_proxy_username() == "iCON"
        assert obj.connections[1].get_proxy_password() == "Irgendein Passwort"

        assert not obj.connections[2].is_selected()
        assert obj.connections[2].is_connected()
        assert not obj.connections[2].uses_proxy()
        assert obj.connections[2].is_ip_dhcp()
        assert obj.connections[2].is_dns_dhcp()
        assert not obj.connections[2].is_lan()
        assert obj.connections[2].get_ssid() == "WEP128"
        assert obj.connections[2].get_encryption_type() == "WEP128"
        assert obj.connections[2].get_key() == "585b5a5f23322737395368234e"
        assert obj.connections[2].get_mtu() == 0

    def test_file_modification(self, tmpdir):
        obj = Wii.NetConfig()
        connection = obj.connections[2]
        connection.set_wifi()
        connection.set_status(passed=True)
        connection.set_ssid("Example SSID")
        connection.set_key("m&oVl,nV\"YuOH", encryption="WEP128")
        connection.set_ip("192.168.0.1")
        connection.set_netmask("255.255.255.255")
        connection.set_gateway("192.168.0.0")
        connection.set_dns("8.8.8.8", primary=True)
        connection.set_dns("8.8.4.4", primary=False)
        connection.set_mtu(1000)
        connection.set_proxy("192.168.255.255", 2006)
        connection.set_proxy_auth("Example Proxy User", "Example Proxy Password")
        obj.select_slot(2)

        obj.dump(tmpdir + "/config.dat")
        new_obj = Wii.NetConfig(tmpdir + "/config.dat")
        new_connection = new_obj.connections[2]
        assert new_connection.is_selected()
        assert new_connection.is_connected()
        assert new_connection.uses_proxy()
        assert not new_connection.is_ip_dhcp()
        assert not new_connection.is_dns_dhcp()
        assert not new_connection.is_lan()
        assert new_connection.get_ssid() == "Example SSID"
        assert new_connection.get_encryption_type() == "WEP128"
        assert new_connection.get_key() == "m&oVl,nV\"YuOH"
        assert new_connection.get_mtu() == 1000
        assert new_connection.get_ip() == "192.168.0.1"
        assert new_connection.get_netmask() == "255.255.255.255"
        assert new_connection.get_gateway() == "192.168.0.0"
        assert new_connection.get_primary_dns() == "8.8.8.8"
        assert new_connection.get_secondary_dns() == "8.8.4.4"
        assert new_connection.get_proxy_server() == "192.168.255.255"
        assert new_connection.get_proxy_port() == 2006
        assert new_connection.get_proxy_username() == "Example Proxy User"
        assert new_connection.get_proxy_password() == "Example Proxy Password"

    def test_exceptions(self):
        obj = Wii.NetConfig()
        connection = obj.connections[0]

        with pytest.raises(ValueError):
            connection.set_ip("999.999.999.999")

        connection.enable_custom_ip()
        with pytest.raises(Exception):
            connection.disable_custom_dns()

        with pytest.raises(ValueError):
            connection.set_mtu(-1)
