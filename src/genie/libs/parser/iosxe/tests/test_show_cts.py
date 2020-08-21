import unittest
from unittest.mock import Mock

from genie.metaparser.util.exceptions import SchemaEmptyParserError
from genie.libs.parser.iosxe.show_cts import ShowCtsRbacl


# =================================
# Unit test for 'show cts rbacl'
# =================================
class TestShowCtsRbacl(unittest.TestCase):
    """Unit test for 'show cts rbacl'"""

    maxDiff = None
    empty_output = {'execute.return_value': ''}
    golden_parsed_output1 = {
    "cts_rbacl": {
        "ip_ver_support": "IPv4 & IPv6",
        "TCP_51005-01": {
            "ip_protocol_version": "IPV4",
            "refcnt": 2,
            "flag": "0x41000000",
            "stale": False,
            1: {
                "action": "permit",
                "protocol": "tcp",
                "direction": "dst",
                "port": 51005
            }
        },
        "TCP_51060-02": {
            "ip_protocol_version": "IPV4",
            "refcnt": 4,
            "flag": "0x41000000",
            "stale": False,
            1: {
                "action": "permit",
                "protocol": "tcp",
                "direction": "dst",
                "port": 51060
            }
        },
        "TCP_51144-01": {
            "ip_protocol_version": "IPV4",
            "refcnt": 10,
            "flag": "0x41000000",
            "stale": False,
            1: {
                "action": "permit",
                "protocol": "tcp",
                "direction": "dst",
                "port": 51144
            }
        },
        "TCP_51009-01": {
            "ip_protocol_version": "IPV4",
            "refcnt": 2,
            "flag": "0x41000000",
            "stale": False,
            1: {
                "action": "permit",
                "protocol": "tcp",
                "direction": "dst",
                "port": 51009
            }
        }
    }
}

    golden_output1 = {'execute.return_value': '''
CTS RBACL Policy
================
RBACL IP Version Supported: IPv4 & IPv6
  name   = TCP_51005-01
  IP protocol version = IPV4
  refcnt = 2
  flag   = 0x41000000
  stale  = FALSE
  RBACL ACEs:
    permit tcp dst eq 51005

  name   = TCP_51060-02
  IP protocol version = IPV4
  refcnt = 4
  flag   = 0x41000000
  stale  = FALSE
  RBACL ACEs:
    permit tcp dst eq 51060

  name   = TCP_51144-01
  IP protocol version = IPV4
  refcnt = 10
  flag   = 0x41000000
  stale  = FALSE
  RBACL ACEs:
    permit tcp dst eq 51144

  name   = TCP_51009-01
  IP protocol version = IPV4
  refcnt = 2
  flag   = 0x41000000
  stale  = FALSE
  RBACL ACEs:
    permit tcp dst eq 51009
    
    '''}

    def test_show_cts_rbacl_full(self):
        self.device = Mock(**self.golden_output1)
        obj = ShowCtsRbacl(device=self.device)
        parsed_output = obj.parse()
        self.assertEqual(parsed_output, self.golden_parsed_output1)

    def test_show_cts_rbacl_empty(self):
        self.device = Mock(**self.empty_output)
        obj = ShowCtsRbacl(device=self.device)
        with self.assertRaises(SchemaEmptyParserError):
            parsed_output = obj.parse()


if __name__ == '__main__':
    unittest.main()
