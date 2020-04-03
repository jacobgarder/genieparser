"""
    * 'show dmvpn'
    * 'show dmvpn interface {interface}'
"""

# Metaparser
import re
from genie.metaparser import MetaParser
from genie.metaparser.util.schemaengine import Any, Or, Optional


# ==============================
# Schema for 
#   'show dmvpn'
#   'show dmvpn interface {interface}'
# ==============================
class ShowDmvpnSchema(MetaParser):
    """
    Schema for 
        * 'show dmvpn'
        * 'show dmvpn interface {interface}'
    """

# These are the key-value pairs to add to the parsed dictionary
    schema = {
        'dmvpn': {
            Any(): {
                'total_peers': int,
                'type': str,
                'peers': {
                    Any(): {
                        Any(): {
                            'tunnel_addr': str,
                            'state': str,
                            'time': str,
                            'attrb': str,
                            'ent': int,
                        },
                    },
                }
            },
        },
    }


# Python (this imports the Python re module for RegEx)
# ==============================
# Parser for 
#   'show dmvpn'
#   'show dmvpn interface {interface}'
# ==============================

# The parser class inherits from the schema class

class ShowDmvpn(ShowDmvpnSchema):
    """
    Parser for 
        * 'show dmvpn'
        * 'show dmvpn interface {interface}'
    """

    cli_command = ['show dmvpn interface {interface}', 'show dmvpn']

    # Defines a function to run the cli_command
    def cli(self, interface='', output=None):
        if output is None:
            if interface:
                cmd = self.cli_command[0].format(interface=interface)
            else:
                cmd = self.cli_command[1]
            out = self.device.execute(self.cli_command)
        else:
            out = output

        # Initializes the Python dictionary variable
        parsed_dict = {}

        # Interface: Tunnel84, IPv4 NHRP Details
        # Type:Spoke, NHRP Peers:1,

        p1 = re.compile(r'Interface: +(?P<interface>(\S+)),')
        p2 = re.compile(r'Type:(?P<type>(\S+)),'
                        r' +NHRP Peers:(?P<total_peers>(\d+)),$')

        # # Ent  Peer NBMA Addr Peer Tunnel Add State  UpDn Tm Attrb
        # ----- --------------- --------------- ----- -------- -----
        #     1 172.29.0.1          172.30.90.1   IKE     3w5d     S
        #     1 172.29.0.2          172.30.90.2    UP    6d12h     S
        #                           172.30.90.25   UP    6d12h     S
        #     2 172.29.134.1       172.30.72.72    UP 00:29:40   DT2
        #                          172.30.72.72    UP 00:29:40   DT1

        p3 = re.compile(r'(?P<ent>(\d+))'
                        r' +(?P<nbma_addr>[a-z0-9\.\:]+)'
                        r' +(?P<tunnel_addr>[a-z0-9\.\:]+)'
                        r' +(?P<state>[a-zA-Z]+)'
                        r' +(?P<time>(\d+\w)+|never|[0-9\:]+)'
                        r' +(?P<attrb>(\w)+)')

        # Defines the "for" loop, to pattern match each line of output

        for line in out.splitlines():
            line = line.strip()

            # Processes the matched line | Interface: Tunnel84, IPv4 NHRP Details
            m = p1.match(line)
            if m:
                group = m.groupdict()
                interface = (group['interface'])
                parsed_dict.setdefault('dmvpn', {}).setdefault(
                    interface, {}).setdefault('peers', {})
                continue

            # Processes the matched line | Type:Spoke, NHRP Peers:1,
            m = p2.match(line)

            if m:
                group = m.groupdict()
                parsed_dict['dmvpn'][interface]['type'] = group['type']
                parsed_dict['dmvpn'][interface]['total_peers'] = int(group['total_peers'])
                continue

            # Processes the matched lines |     1 172.29.0.1          172.30.90.1   IKE     3w5d     S
            m = p3.match(line)
            if m:
                group = m.groupdict()
                nbma_addr = group['nbma_addr']
                ent_val = group['ent']
                group['ent'] = int(ent_val)
                group.pop('nbma_addr')
                
                if re.match(r'\d+\.\d+\.\d+\.\d+', nbma_addr):  # ipv4
                    parsed_dict['dmvpn'][interface]['peers'].setdefault('ipv4', {}).setdefault(
                        nbma_addr, {})
                    parsed_dict['dmvpn'][interface]['peers']['ipv4'][nbma_addr].update(
                        group)
                else:
                    parsed_dict['dmvpn'][interface]['peers'].setdefault('ipv6', {}).setdefault(
                        nbma_addr, {})
                    parsed_dict['dmvpn'][interface]['peers']['ipv6'][nbma_addr].update(
                        group)
                continue

        return parsed_dict
