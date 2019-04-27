#!/usr/bin/env python3
import socket
from binascii import hexlify, unhexlify
from string import hexdigits

from .common import *


class NWC24fl(BigEndianStructure):
    """Shows info for the friend list, which is stored in /shared2/wc24/nwc24fl.bin.
       Reference: http://wiibrew.org/wiki//shared2/wc24/nwc24fl.bin

       Args:
           file (str[optional]): Path to a file
    """

    MAGIC = b"WcFl"

    class FriendListEntry(BigEndianStructure):
        _pack_ = 1
        _fields_ = [
            ("type", c_uint32),
            ("status", c_uint32),
            ("name", ARRAY(c_byte, 20)),
            ("unknown", ARRAY(c_byte, 4)),
            ("miiID", c_uint32),
            ("systemID", c_uint32),
            ("reserved", ARRAY(c_byte, 24)),
            ("friendCode", ARRAY(c_byte, 96)),
            ("padding", ARRAY(c_byte, 160)),
        ]

        def get_name(self):
            """Returns friend name."""
            return bytes(self.name).rstrip(b"\x00").decode('utf-16-be')

        def get_friend_code(self):
            """Returns friend code or e-mail."""
            if self.type == 0:  # None
                return None
            elif self.type == 1:  # Wii friend
                return int.from_bytes(bytes(self.friendCode).rstrip(b"\00"), byteorder='big')
            elif self.type == 2:  # E-Mail
                return bytes(self.friendCode).rstrip(b"\x00").decode()
            else:
                raise ValueError("Unknown friend type.")

        def get_status(self):
            """Returns status of friend."""
            states = [
                "Unknown",
                "Unconfirmed",
                "Confirmed",
                "Declined"
            ]
            try:
                return states[self.status]
            except IndexError:
                return "Unknown"

    _pack_ = 1
    _fields_ = [
        ("magic", ARRAY(c_char, 4)),
        ("unknown", ARRAY(c_byte, 4)),
        ("maxEntries", c_uint32),
        ("friendCount", c_uint32),
        ("padding", ARRAY(c_byte, 48)),
        ("friendCodes", ARRAY(ARRAY(c_byte, 8), 100)),
        ("friendList", ARRAY(FriendListEntry, 100))
    ]

    def __repr__(self):
        return "Wii Friend List: {0}/{1} Entries used".format(self.friendCount, self.maxEntries)

    def __str__(self):
        output = "Friend List:\n"
        output += "  {0}/{1} Entries used\n\n".format(self.friendCount, self.maxEntries)

        for friend in self.friendList:
            if friend.type == 0:
                continue
            output += "  {0}\n".format(friend.get_name())
            if friend.type == 1:
                output += "    Friend Code: {0}\n".format(friend.get_friend_code())
                output += "    Status: {0}\n".format(friend.get_status())
            else:
                output += "    E-Mail: {0}\n".format(friend.get_friend_code())
            output += "\n"

        return output

    def __init__(self, file=None):
        if not file:
            self.magic = self.MAGIC
            self.maxEntries = 100
            self.unknown = ARRAY(c_byte, 4).from_buffer_copy(b"\x00\x00\x00\x02\x00")

        if self.magic != self.MAGIC:
            raise Exception("Not a valid NWC24fl file!")

        super().__init__()


class NWC24msg(BigEndianStructure):
    """Shows info for WC24 Mail Engine and title booting, which is stored in /shared2/wc24/nwc24msg.cfg.
       Reference: http://wiibrew.org/wiki//shared2/wc24/nwc24msg.cfg

       Args:
           file (str[optional]): Path to a file
    """

    MAGIC = b"WcCf"

    _pack_ = 1
    _fields_ = [
        ("magic", ARRAY(c_char, 4)),
        ("version", c_uint32),
        ("friendCode", c_uint64),
        ("idGeneration", c_uint32),
        ("registered", c_uint32),
        ("mailDomain", ARRAY(c_byte, 64)),
        ("passwd", ARRAY(c_byte, 32)),
        ("mlchkid", ARRAY(c_byte, 36)),
        ("mailEngineURLs", ARRAY(ARRAY(c_byte, 128), 5)),
        ("reserved", ARRAY(c_byte, 220)),
        ("titleBooting", c_uint32),
        ("checksum", c_uint32),
    ]

    def get_password(self):
        """Returns the Wii Mail password."""
        return bytes(self.passwd).rstrip(b"\x00").decode()

    def get_mlchkid(self):
        """Returns the Wii Mail Check ID."""
        return bytes(self.mlchkid).rstrip(b"\x00").decode()

    def get_mail_domain(self):
        """Returns the mail domain for Wii Mail."""
        return bytes(self.mailDomain).rstrip(b"\x00").decode()

    def get_engine_urls(self):
        """Returns the mail engine URLs for Wii Mail."""
        urls = []
        for url in self.mailEngineURLs:
            urls.append(bytes(url).rstrip(b"\x00").decode())
        return urls

    def set_mail_domain(self, domain):
        """Changes the mail domain. Prepends @ if not given. Also updates the checksum."""
        if not domain.startswith("@"):
            domain = "@" + domain
        if len(domain) > 64:
            raise ValueError("Domain must be <= 64 characters.")

        domain = pad_to_cbyte_array(domain.encode(), 64)
        self.mailDomain = domain

        self.update_checksum()

    def set_password(self, password):
        """Changes Wii Mail password. Also updates the checksum."""
        if len(password) > 32:
            raise ValueError("Password must be <= 32 characters.")

        password = pad_to_cbyte_array(password.encode(), 32)
        self.passwd = password

        self.update_checksum()

    def set_mlchkid(self, mlchkid):
        """Changes Wii Mail Check ID. Also updates the checksum."""
        if len(mlchkid) > 36:
            raise ValueError("Mail Check ID must be <= 36 characters.")

        mlchkid = pad_to_cbyte_array(mlchkid.encode(), 36)
        self.mlchkid = mlchkid

        self.update_checksum()

    def set_engine_url(self, num, url):
        """Changes the URLs used by the Mail Engine. Also updates the checksum.

        Args:
            num (int): Index of the engine URL for the action:
                0: account, 1: check, 2: receive, 3: delete, 4: send
            url (str): New URL
        """
        if not 0 <= num <= 4:
            raise ValueError("Please use a number from 0 to 4 for "
                             "'account', 'check', 'receive', 'delete' or 'send' respectively.")

        if not url.startswith("http://") and not url.startswith("https://"):
            raise ValueError("Invalid URL.")

        if len(url) > 128:
            raise ValueError("URL must be <= 128 characters.")

        url = pad_to_cbyte_array(url.encode(), 128)
        self.mailEngineURLs[num] = url

        self.update_checksum()

    def generate_checksum(self):
        """Generates the checksum."""
        return Crypto.generate_checksum(self.pack()[:-4])

    def update_checksum(self):
        """Updates the checksum in the Struct."""
        self.checksum = self.generate_checksum()

    def __repr__(self):
        return "Wii nwc24msg for Friend Code {0}".format(self.friendCode)

    def __str__(self):
        output = "nwc24msg:\n"
        output += "  Version: {0}\n".format(self.version)
        output += "  Title booting: {0}\n".format("Disabled" if self.titleBooting == 0 else "Enabled")
        output += "  Friend code: {0}\n".format(self.friendCode)
        output += "  Generated IDs: {0}\n\n".format(self.idGeneration)

        output += "  Mail domain: {0}\n".format(self.get_mail_domain())
        output += "  Registered: {0}\n".format("Yes" if self.registered == 2 else "No")
        output += "  Password: {0}\n".format(self.get_password())
        output += "  Mlchkid: {0}\n\n".format(self.get_mlchkid())

        output += "  Mail Engine URLs:\n"
        for url in self.get_engine_urls():
            output += "    {0}\n".format(url)

        return output

    def __init__(self, file=None):
        if not file:
            self.magic = self.MAGIC
            self.version = 8
            self.friendCode = 9999999999999999
            self.mailDomain = pad_to_cbyte_array(b"@wii.com", 64)
            self.passwd = pad_to_cbyte_array(b"Wii.py3", 32)
            self.mlchkid = pad_to_cbyte_array(b"GeneratedWithWiipy3", 36)
            self.mailEngineURLs[0] = pad_to_cbyte_array(b"https://amw.wc24.wii.com/cgi-bin/account.cgi", 128)
            self.mailEngineURLs[1] = pad_to_cbyte_array(b"http://rcw.wc24.wii.com/cgi-bin/check.cgi", 128)
            self.mailEngineURLs[2] = pad_to_cbyte_array(b"https://amw.wc24.wii.com/cgi-bin/receive.cgi", 128)
            self.mailEngineURLs[3] = pad_to_cbyte_array(b"https://amw.wc24.wii.com/cgi-bin/delete.cgi", 128)
            self.mailEngineURLs[4] = pad_to_cbyte_array(b"https://amw.wc24.wii.com/cgi-bin/send.cgi", 128)
            self.update_checksum()

        if self.magic != self.MAGIC:
            raise Exception("Not a valid NWC24msg file!")

        if self.checksum != self.generate_checksum():
            print("WARNING: nwc24msg.cfg checksum is invalid!")

        super().__init__()


class NetConfig(BigEndianStructure):
    """Performs network configuration. The file is located at /shared2/sys/net/02/config.dat.
       Reference: http://wiibrew.org/wiki//shared2/sys/net/02/config.dat

       Args:
           file (str[optional]): Path to a file
    """

    class ConnectionEntry(BigEndianStructure):

        class ProxySettings(BigEndianStructure):
            _pack_ = 1
            _fields_ = [
                ("active", c_uint8),
                ("authentication", c_uint8),
                ("padding1", ARRAY(c_byte, 2)),
                ("server", ARRAY(c_byte, 255)),
                ("padding2", c_byte),
                ("port", c_uint16),
                ("username", ARRAY(c_byte, 32)),
                ("padding3", c_byte),
                ("password", ARRAY(c_byte, 32)),
            ]

        class Flags(BigEndianStructure):
            _pack_ = 1
            _fields_ = [
                ('selected', c_uint8, 1),
                ('unknown1', c_uint8, 1),
                ('passed', c_uint8, 1),
                ('proxy', c_uint8, 1),
                ('unknown2', c_uint8, 1),
                ('dnsSource', c_uint8, 1),
                ('ipSource', c_uint8, 1),
                ('interface', c_uint8, 1)
            ]

        _pack_ = 1
        _fields_ = [
            # General
            ("flags", Flags),
            ("padding1", ARRAY(c_byte, 3)),
            ("ip", ARRAY(c_uint8, 4)),
            ("netmask", ARRAY(c_uint8, 4)),
            ("gateway", ARRAY(c_uint8, 4)),
            ("primaryDNS", ARRAY(c_uint8, 4)),
            ("secondaryDNS", ARRAY(c_uint8, 4)),
            ("padding2", ARRAY(c_byte, 2)),
            ("mtu", c_uint16),
            ("padding3", ARRAY(c_byte, 8)),
            # Proxy
            ("proxy", ProxySettings),
            ("padding4", c_byte),
            ("proxyCopy", ProxySettings),
            ("padding5", ARRAY(c_byte, 1297)),
            # Wi-Fi
            ("ssid", ARRAY(c_byte, 32)),
            ("padding6", c_byte),
            ("ssidLength", c_uint8),
            ("padding7", ARRAY(c_byte, 2)),
            ("padding8", c_byte),
            ("encryption", c_uint8),
            ("padding9", ARRAY(c_byte, 2)),
            ("padding10", c_byte),
            ("keyLength", c_uint8),
            ("wepKeyInHex", c_uint8),
            ("padding11", c_byte),
            ("key", ARRAY(c_byte, 64)),
            ("padding12", ARRAY(c_byte, 236)),
        ]

        def is_blank(self):
            """Returns True if the slot is blank."""
            if int.from_bytes(bytes(self.flags), byteorder="big") == 0:
                return True
            else:
                return False

        def is_selected(self):
            """Returns True if the connection is selected."""
            return bool(self.flags.selected)

        def is_connected(self):
            """Returns True if the internet test passed."""
            return bool(self.flags.passed)

        def uses_proxy(self):
            """Returns True if the connection uses a proxy."""
            return bool(self.flags.proxy)

        def is_ip_dhcp(self):
            """Returns True if the IP is retrieved through DHCP."""
            return bool(self.flags.ipSource)

        def is_dns_dhcp(self):
            """Returns True if the DNS servers are retrieved through DHCP."""
            return bool(self.flags.dnsSource)

        def is_lan(self):
            """Returns True if the connection is a LAN connection."""
            return bool(self.flags.interface)

        def get_ssid(self):
            """Returns the network's SSID."""
            return bytes(self.ssid)[:self.ssidLength].decode()

        def get_encryption_type(self):
            """Returns the Wi-Fi encryption type."""
            key_types = {
                0: "OPEN",
                1: "WEP64",
                2: "WEP128",
                4: "WPA-PSK (TKIP)",
                5: "WPA2-PSK (AES)",
                6: "WPA-PSK (AES)"
            }
            try:
                return key_types[self.encryption]
            except KeyError:
                return "Unknown"

        def get_key(self):
            """Returns the Wi-Fi passphrase."""
            if self.get_encryption_type() == "OPEN":
                return None

            if self.encryption >= 4:  # WPA
                return bytes(self.key)[:self.keyLength].decode()
            else:  # WEP
                if self.get_encryption_type() == "WEP64":
                    wepkey_length = 20
                elif self.get_encryption_type() == "WEP128":
                    wepkey_length = 52
                else:
                    raise Exception("Invalid encryption type: {0}".format(self.encryption))

                if self.wepKeyInHex:  # WEP with key in HEX
                    wep_key = hexlify(bytes(self.key)[:wepkey_length])
                else:  # WEP with key in ASCII
                    wep_key = bytes(self.key)[:wepkey_length]

                # Key is stored four times
                wep_key = wep_key[:(len(wep_key) // 4)]

                return wep_key.decode()

        def get_ip(self):
            """Returns IP as string."""
            return ".".join(map(str, self.ip))

        def get_netmask(self):
            """Returns netmask as string."""
            return ".".join(map(str, self.netmask))

        def get_gateway(self):
            """Returns gateway as string."""
            return ".".join(map(str, self.gateway))

        def get_primary_dns(self):
            """Returns primary DNS IP as string."""
            return ".".join(map(str, self.primaryDNS))

        def get_secondary_dns(self):
            """Returns secondary DNS IP as string."""
            return ".".join(map(str, self.secondaryDNS))

        def get_proxy_server(self):
            """Returns the proxy server."""
            return bytes(self.proxy.server).rstrip(b"\x00").decode()

        def get_proxy_port(self):
            """Returns the proxy port."""
            return self.proxy.port

        def get_proxy_username(self):
            """Returns the proxy username."""
            return bytes(self.proxy.username).rstrip(b"\x00").decode()

        def get_proxy_password(self):
            """Returns the proxy password."""
            return bytes(self.proxy.password).rstrip(b"\x00").decode()

        def delete(self):
            """Deletes all settings."""
            # TODO: Find a elegant way to do this instead of re-assigning every single variable
            return NotImplementedError()

        def set_wifi(self):
            """Sets connection type to Wi-Fi."""
            self.flags.interface = 0

        def set_lan(self):
            """Sets connection type to LAN."""
            self.flags.interface = 1

        def set_status(self, passed=True):
            """Sets connection test to passed (True) or failed (False)."""
            if self.is_connected():
                return

            if passed:
                self.flags.passed = 1
            else:
                self.flags.passed = 0

        def enable_custom_ip(self):
            """Enables manual IP settings. Will also force enable custom DNS servers."""
            self.flags.ipSource = 0
            self.enable_custom_dns()

        def disable_custom_ip(self):
            """Disables manual IP settings and uses DHCP."""
            self.flags.ipSource = 1

        @staticmethod
        def _set_ip(ip, setting):
            """Helper class for setting IPs."""
            try:
                socket.inet_aton(ip)
            except OSError:
                raise ValueError("IPv4 address is invalid")

            ip = ip.split(".")
            for num, byt in enumerate(ip):
                setting[num] = int(byt)

        def set_ip(self, ip):
            """Sets IP for connection."""
            self._set_ip(ip, self.ip)
            self.enable_custom_ip()

        def set_netmask(self, ip):
            """Sets subnet mask for connection."""
            self._set_ip(ip, self.netmask)
            self.enable_custom_ip()

        def set_gateway(self, ip):
            """Sets subnet mask for connection."""
            self._set_ip(ip, self.gateway)
            self.enable_custom_ip()

        def enable_custom_dns(self):
            """Enables manual DNS servers."""
            self.flags.dnsSource = 0

        def disable_custom_dns(self):
            """Disables manual DNS servers and uses DHCP."""
            if not self.is_ip_dhcp():
                raise Exception("IP must be set to automatic to be able to disable custom DNS servers.")
            self.flags.dnsSource = 1

        def set_dns(self, ip, primary=True):
            """Sets IP for DNS server and enables it. If 'primary' is False, the secondary DNS is set instead."""
            if primary:
                dns_conf = self.primaryDNS
            else:
                dns_conf = self.secondaryDNS

            self._set_ip(ip, dns_conf)
            self.enable_custom_dns()

        def set_mtu(self, mtu):
            """Sets MTU."""
            if mtu != 0 and not 576 <= mtu <= 1500:
                raise ValueError("Invalid MTU - valid values are 0 and 576 up to 1500.")

            self.mtu = mtu

        def set_ssid(self, ssid):
            """Sets SSID and enables Wi-Fi connection."""
            if len(ssid) > 32:
                raise ValueError("SSID must be <= 32 characters")

            self.ssid = pad_to_cbyte_array(ssid.encode(), 32)
            self.ssidLength = len(ssid)

            self.set_wifi()

        def set_key(self, key=None, encryption="OPEN"):
            """Sets Wi-Fi key and encryption method (default: OPEN)."""
            encryption_types = {
                "OPEN": 0,
                "WEP64": 1,
                "WEP-64": 1,
                "WEP128": 2,
                "WEP-128": 2,
                "WPA (TKIP)": 4,
                "WPA-PSK (TKIP)": 4,
                "WPA2-PSK (AES)": 5,
                "WPA2": 5,
                "WPA2 (AES)": 5,
                "WPA (AES)": 6,
                "WPA-PSK (AES)": 6
            }
            try:
                encryption_type = encryption_types[encryption.upper()]
            except KeyError:
                raise ValueError("Invalid encryption type. Valid types are: 'OPEN', 'WEP64', 'WEP128', 'WPA (TKIP)', "
                                 "'WPA2 (AES)', or 'WPA (AES)'")

            if encryption_type == 0:  # OPEN
                if key:
                    print("WARNING: Encryption type set to 'OPEN', key will be ignored!")
                self.encryption = 0
                self.keyLength = 0
                self.key = pad_to_cbyte_array(b"\x00", 64)
                self.set_wifi()
                return

            if not key:
                raise ValueError("Key must be set if encryption type is not 'OPEN'.")
            if len(key) > 64:
                raise ValueError("Key must be <= 64 characters.")

            if encryption_type >= 4:  # WPA
                self.encryption = encryption_type
                self.keyLength = len(key)
                self.key = pad_to_cbyte_array(key.encode(), 64)
                self.set_wifi()
                return

            # WEP
            key_inhex = False
            if encryption_type == 1:  # WEP64
                if all(c in hexdigits for c in key):  # HEX
                    if len(key) != 10:
                        raise ValueError("HEX key for WEP64 needs to be 10 characters long.")
                    key_inhex = True
                else:  # ASCII
                    if len(key) != 5:
                        raise ValueError("ASCII key for WEP64 needs to be 5 characters long.")
            elif encryption_type == 2:  # WEP128
                if all(c in hexdigits for c in key):  # HEX
                    if len(key) != 26:
                        raise ValueError("HEX key for WEP128 needs to be 26 characters long.")
                    key_inhex = True
                else:  # ASCII
                    if len(key) != 13:
                        raise ValueError("ASCII key for WEP128 needs to be 13 characters long.")

            if key_inhex:
                self.wepKeyInHex = 1
                self.key = pad_to_cbyte_array(unhexlify(key * 4), 64)
            else:
                self.wepKeyInHex = 0
                self.key = pad_to_cbyte_array(key.encode() * 4, 64)

            self.encryption = encryption_type
            self.keyLength = len(key)
            self.set_wifi()

        def enable_proxy(self):
            """Enables proxy."""
            self.flags.proxy = 1
            self.proxy.active = 1
            self.proxyCopy.active = 1

        def disable_proxy(self):
            """Disables proxy and clears all data."""
            self.flags.proxy = 0
            self.proxy.active = 0
            self.proxyCopy.active = 0
            self.proxy.server = pad_to_cbyte_array(b"\x00", 255)
            self.proxyCopy.server = pad_to_cbyte_array(b"\x00", 255)
            self.proxy.port = 0
            self.proxyCopy.port = 0
            self.disable_proxy_auth()

        def disable_proxy_auth(self):
            """Disables authentication for proxy and deletes all data."""
            self.proxy.authentication = 0
            self.proxyCopy.authentication = 0
            self.proxy.username = pad_to_cbyte_array(b"\x00", 32)
            self.proxyCopy.username = pad_to_cbyte_array(b"\x00", 32)
            self.proxy.password = pad_to_cbyte_array(b"\x00", 32)
            self.proxyCopy.password = pad_to_cbyte_array(b"\x00", 32)

        def set_proxy(self, server, port):
            """Sets proxy server and port and enables it."""
            if len(server) > 255:
                raise Exception("Server address must be < 256 characters.")

            if not isinstance(port, int):
                raise ValueError("Port must be an integer.")

            if not 0 < port <= 34463:
                raise ValueError("Port must be between 1 and 34463.")

            self.proxy.server = pad_to_cbyte_array(server.encode(), 255)
            self.proxyCopy.server = pad_to_cbyte_array(server.encode(), 255)
            self.proxy.port = port
            self.proxyCopy.port = port

            self.enable_proxy()

        def set_proxy_auth(self, username, password):
            """Sets username and password for proxy."""
            if len(username) > 32:
                raise ValueError("Username must be <= 32 characters!")

            if len(password) > 32:
                raise ValueError("Password must be <= 32 characters!")

            self.proxy.authentication = 1
            self.proxyCopy.authentication = 1
            self.proxy.username = pad_to_cbyte_array(username.encode(), 32)
            self.proxyCopy.username = pad_to_cbyte_array(username.encode(), 32)
            self.proxy.password = pad_to_cbyte_array(password.encode(), 32)
            self.proxyCopy.password = pad_to_cbyte_array(password.encode(), 32)

    _pack_ = 1
    _fields_ = [
        ("unknown1", ARRAY(c_byte, 4)),
        ("connected", c_uint8),
        ("unknown2", ARRAY(c_byte, 3)),
        ("connections", ARRAY(ConnectionEntry, 3))
    ]

    def select_slot(self, num):
        """Selects slot and deselects old one."""
        if not 0 <= num <= 2:
            raise ValueError("Out of bounds.")

        slot = self.connections[num]
        if slot.is_selected():
            return

        for connection in self.connections:
            if connection.is_selected():
                connection.flags.selected = 0
        slot.flags.selected = 1

    def __repr__(self):
        used_slots = 0
        for slot in self.connections:
            if not slot.is_blank():
                used_slots += 1
        return "Wii Network Config ({0}/3 Slots used)".format(used_slots)

    def __str__(self):
        output = "Wii Network Config:\n"
        for num, slot in enumerate(self.connections):  # TODO: Move to ConnectionEntry
            output += "\n  Slot {0}".format(num + 1)
            if slot.is_selected():
                output += " (selected)"
            output += ":\n"

            if slot.is_blank():
                output += "    Free\n"
                continue

            if not slot.is_connected():
                output += "    Connection test failed\n"

            if slot.is_lan():
                output += "    Connection Type: Wired\n"
            else:
                output += "    Connection Type: Wireless\n"
                output += "    SSID: {0}\n".format(slot.get_ssid())
                output += "    Encryption Type: {0}\n".format(slot.get_encryption_type())
                if slot.get_encryption_type() != "OPEN":
                    output += "    Passphrase: {0}\n".format(slot.get_key())

            if slot.mtu > 0:
                output += "    MTU: {0}\n".format(slot.mtu)

            if not slot.is_ip_dhcp():
                output += "\n    IP settings:\n"
                output += "      IP address: {0}\n".format(slot.get_ip())
                output += "      Subnet mask: {0}\n".format(slot.get_netmask())
                output += "      Gateway: {0}\n".format(slot.get_gateway())

            if not slot.is_dns_dhcp():
                output += "\n    DNS settings:\n"
                output += "      Primary DNS: {0}\n".format(slot.get_primary_dns())
                output += "      Secondary DNS: {0}\n".format(slot.get_secondary_dns())

            if slot.uses_proxy():
                output += "\n    Proxy settings:\n"
                output += "      Proxy server: {0}\n".format(slot.get_proxy_server())
                output += "      Proxy port: {0}\n".format(slot.get_proxy_port())
                if slot.proxy.authentication:
                    output += "      Username: {0}\n".format(slot.get_proxy_username())
                    output += "      Password: {0}\n".format(slot.get_proxy_password())

        return output

    def __init__(self, file=None):
        if not file:
            self.unknown2 = ARRAY(c_byte, 3).from_buffer_copy(b"\x07\x00\x00")

        super().__init__()


class IplSave(BigEndianStructure):
    """Perfoms all iplsave.bin related functions, like (re-)moving and adding channels.
       This file is stored in title/00000001/00000002/data/iplsave.bin.
       Reference: http://wiibrew.org/wiki//title/00000001/00000002/data/iplsave.bin

       Args:
           file (str[optional]): Path to a file
    """
    # TODO: Support 832 bytes file (Wii menu 2.0 - 4.0)

    MAGIC = b"RIPL"

    class Channel(BigEndianStructure):
        _pack_ = 1
        _fields_ = [
            ("type", c_uint8),
            ("secondaryType", c_uint8),
            ("unknown", ARRAY(c_byte, 4)),
            ("flags", c_uint16),
            ("titleid", c_uint64)
        ]

        def get_titleid(self):
            """Returns the long title id of the channel."""
            return "{:08x}{:08x}".format(self.titleid >> 32, self.titleid & 0xFFFFFFFF)

        def get_id4(self):
            """Returns the ID4 of the channel."""
            return unhexlify("{:08x}".format(self.titleid & 0xFFFFFFFF)).decode()

        def is_used(self):
            """Returns True if there's a channel in the slot."""
            return bool(self.type)

        def is_disc_channel(self):
            if self.type == 1:
                return True
            else:
                return False

        def delete(self):
            """Empties channel slot. Note that the Wii will re-populate it. NOTE: MD5 has to be updated!"""
            self.type = 0
            self.secondaryType = 0
            self.unknown = ARRAY(c_byte, sizeof(self.unknown)).from_buffer_copy(b"\x00" * sizeof(self.unknown))
            self.flags = 0
            self.titleid = 0

        def __repr__(self):
            return self.get_titleid()

    _pack_ = 1
    _fields_ = [
        ("magic", ARRAY(c_char, 4)),
        ("filesize", c_uint32),
        ("unknown1", ARRAY(c_byte, 8)),
        ("channels", ARRAY(Channel, 48)),
        ("unknown2", ARRAY(c_byte, 416)),
        ("md5", ARRAY(c_byte, 16))
    ]

    def generate_md5(self):
        """Generates the md5sum."""
        return Crypto.create_md5hash(self.pack()[:-16])

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
            by_titleid (bool): Search by Title ID instead of ID4
            return_index (bool): Return index instead of Channel class
        """
        if by_titleid:
            if len(search) != 16:
                raise ValueError("Title ID must be 16 characters long.")
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

    def get_disc_channel_index(self):
        """Returns the index of the disc channel in self.channels."""
        for i, channel in enumerate(self.channels):
            if channel.is_disc_channel():
                return i

        raise Exception("Disc channel not found.")

    def move_channel(self, col1, row1, page1, col2, row2, page2):
        """Moves channel from col1, row1, page1 to col2, row2, page2"""
        if not 0 <= col1 <= 3 or not 0 <= row1 <= 2 or not 0 <= page1 <= 3:
            raise ValueError("Source is out of bounds")
        if not 0 <= col2 <= 3 or not 0 <= row2 <= 2 or not 0 <= page2 <= 3:
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

    def add_disc_channel(self, col=0, row=0, page=0):
        """Adds/Moves disc channel to col, row on page. Defaults to first slot."""
        if not 0 <= col <= 3 or not 0 <= row <= 2 or not 0 <= page <= 3:
            raise ValueError("Out of bounds.")

        try:
            old_position = self.get_disc_channel_index()
        except Exception:
            old_position = -1

        new_position = (col + (row * 4) + (page * 12))
        new_channel = self.channels[new_position]

        if old_position > -1:  # Move disc channel
            self.channels[new_position] = self.channels[old_position]
            self.channels[old_position].delete()
        else:  # Add disc channel
            new_channel.type = 1
            new_channel.secondaryType = 1
            new_channel.unknown = ARRAY(c_byte, sizeof(new_channel.unknown)).from_buffer_copy(
                b"\x00" * sizeof(new_channel.unknown)
            )
            new_channel.flags = 15
            new_channel.titleid = 0

        self.update_md5()

    def __repr__(self):
        return "Wii IplSave: {0} slot{1} used out of 48 ({2} free)".format(
            self.get_used_blocks(),
            "" if self.get_used_blocks() == 1 else "s",
            self.get_free_blocks()
        )

    def __str__(self):
        output = "IplSave:\n"
        output += "  Used {0} slot{1} out of 48 ({2} free)\n\n".format(
            self.get_used_blocks(),
            "" if self.get_used_blocks() == 1 else "s",
            self.get_free_blocks()
        )

        for page in range(4):
            output += "  Page {0}:\n    ".format(page + 1)
            for row in range(3):
                for slot in range(4):
                    curtitle = self.channels[(slot + (row * 4) + (page * 12))]
                    if curtitle.titleid == 0:
                        if curtitle.is_disc_channel():
                            output += "{0:8}".format("Disc")
                        else:
                            output += "{0:8}".format("Free")
                    else:
                        output += "{0:8}".format(curtitle.get_id4())
                if row == 2:  # Last row
                    output += "\n\n"
                else:
                    output += "\n    "
        return output

    def __init__(self, file=None):
        if not file:
            self.magic = self.MAGIC
            self.filesize = sizeof(self)
            self.unknown1 = ARRAY(c_byte, sizeof(self.unknown1)).from_buffer_copy(b"\x00\x00\x00\x03\x00\x00\x00\x00")
            self.channels[0].flags = 15
            self.channels[0].type = 1
            self.channels[0].secondaryType = 1
            self.update_md5()

        if self.magic != self.MAGIC:
            raise Exception("Not a valid IplSave file!")

        if self.filesize != sizeof(self):
            raise Exception("IplSave filesize is wrong.")

        if bytes(self.md5) != self.generate_md5():
            print("WARNING: iplsave.bin md5 sum mismatch!")

        super().__init__()
