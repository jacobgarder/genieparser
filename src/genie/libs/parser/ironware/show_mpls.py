"""
Module:
    genie.libs.parser.ironware.show_mpls

Author:
    James Di Trapani <james@ditrapani.com.au> - https://github.com/jamesditrapani

Description:
    MPLS parsers for IronWare devices

Parsers:
    * show mpls lsp
    * show mpls vll <vll>
"""

from genie.metaparser import MetaParser
from genie.metaparser.util.schemaengine import Any, Or, Optional
import re

# ======================================================
# Schema for 'show mpls lsp wide'
# ======================================================
class ShowMPLSLSPSchema(MetaParser):
    """Schema for show mpls lsp"""
    schema = {
        'lsps': {
            Any(): {
                'destination': str,
                'admin': str,
                'operational': str,
                'flap_count': int,
                'retry_count': int,
                Optional('tunnel_interface'): str,
                Optional('path'): str
            }
        }
    }

# ====================================================
#  parser for 'show mpls lsp wide'
# ====================================================
class ShowMPLSLSP(ShowMPLSLSPSchema):
    """
    Parser for show mpls lsp wide on Devices running IronWare
    """
    cli_command = 'show mpls lsp'

    """
    Note: LSPs marked with * are taking a Secondary Path
                                                                      Admin Oper  Tunnel   Up/Dn Retry Active
    Name                                              To              State State Intf     Times No.   Path
    mlx8.1_to_ces.2                                   1.1.1.1  UP    UP    tnl0     1     0     --   
    mlx8.1_to_ces.1                                   2.2.2.2   UP    UP    tnl56    1     0     --   
    mlx8.1_to_mlx8.2                                  3.3.3.3   UP    UP    tnl63    1     0     --   
    mlx8.1_to_mlx8.3                                  4.4.4.4   DOWN  DOWN  --       0     0     --
    """

    def cli(self, output=None):
        if output is None:
            # auto expand to wide
            out = self.device.execute(self.cli_command + ' wide')
        else:
            out = output
        lsp_dict = {}

        result_dict = {}

        p0 = re.compile(
            r'(^(?P<name>\S+)\s+(?P<endpoint>\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})\s+ '
            r'(?P<adminstate>UP|DOWN)\s+(?P<operationstate>UP|DOWN)\s+ '
            r'(?P<tunnelint>tnl\d+|--)\s+(?P<flapcount>\d+)\s+(?P<retrynum>\d+)\s+(?P<activepath>\S+))'
        )

        for line in out.splitlines():
            line = line.strip()

            m = p0.match(line)
            if m:
                if 'lsps' not in lsp_dict:
                    result_dict = lsp_dict.setdefault('lsps', {})
                
                lsp_name = m.groupdict()['name']
                result_dict[lsp_name] = {
                    'destination': m.groupdict()['endpoint'],
                    'admin': m.groupdict()['adminstate'],
                    'operational': m.groupdict()['operationstate'],
                    'flap_count': int(m.groupdict()['flapcount']),
                    'retry_count': int(m.groupdict()['retrynum'])
                }

                tunnel = m.groupdict()['tunnelint']
                if tunnel != '--':
                    result_dict[lsp_name]['tunnel_interface'] = tunnel
                
                path = m.groupdict()['activepath']
                if path != '--':
                    result_dict[lsp_name]['path'] = path

                continue
        return lsp_dict

# ======================================================
# Schema for 'show mpls vll {vll}'
# ======================================================
class ShowMPLSVLLSchema(MetaParser):
    """Schema for show mpls vll {vll}"""
    schema = {
        'vll': {
            Any(): {
                'vcid': int,
                'vll_index': int,
                'local': {
                    'type': str,
                    'interface': str,
                    Optional('vlan_id'): int,
                    'state': str,
                    Optional('mct_state'): str,
                    Optional('ifl_id'): str,
                    'vc_type': str,
                    'mtu': int,
                    'cos': str,
                    Optional('extended_counters'): bool,
                    Optional('counters'): bool
                },
                'peer': {
                    'ip': str,
                    'state': str,
                    Optional('reason'): str,
                    'vc_type': str,
                    'mtu': int,
                    'local_label': Or(int, str),
                    'remote_label': Or(int, str),
                    'local_group_id': Or(int, str),
                    'remote_group_id': Or(int, str),
                    'tunnel_lsp': {
                        'name': str,
                        Optional('tunnel_interface'): str
                    },
                    'lsps_assigned': str
                }
            }
        }
    }

# ====================================================
#  parser for 'show mpls vll {vll}'
# ====================================================
class ShowMPLSVLL(ShowMPLSVLLSchema):
    """
    Parser for show mpls vll {vll} on Devices running IronWare

    Reference Documenation - https://resources.ditrapani.com.au/#!index.md#Vendor_Documentation

    """
    cli_command = 'show mpls vll {vll}'

    """
    VLL VLL-TEST1, VC-ID 2456, VLL-INDEX 2

    End-point        : tagged  vlan 3043  e 2/5
    End-Point state  : Up
    MCT state        : None
    IFL-ID           : --
    Local VC type    : tag
    Local VC MTU     : 9190
    COS              : --
    Extended Counters: Enabled
    Counter          : disabled

    Vll-Peer         : 192.168.1.1
        State          : UP
        Remote VC type : tag               Remote VC MTU  : 9190
        Local label    : 852217            Remote label   : 852417
        Local group-id : 0                 Remote group-id: 0
        Tunnel LSP     : mlx8.1_to_ces.2 (tnl15)
        MCT Status TLV : --
        LSPs assigned  : No LSPs assigned
    """

    def cli(self, vll, output=None):
        if output is None:
            out = self.device.execute(self.cli_command.format(vll=vll))
        else:
            out = output

        result_dict = {}

        # VLL VLL-TEST1, VC-ID 2456, VLL-INDEX 2
        p0 = re.compile(r'(^VLL\s+(?P<name>[^,]+),+\s+VC-ID\s+(?P<vcid>[^,]+),\s+VLL-INDEX\s+(?P<vllindex>\d+$))')

        # End-point        : tagged  vlan 3043  e 2/5
        p1 = re.compile(r'(^End-point\s+:\s+(?P<type>tagged|untagged)(\s+vlan\s+(?P<vid>\d+)|)\s+e\s+(?P<interface>\d{1,3}\/\d{1,3}))')

        # End-Point state  : Up
        p2 = re.compile(r'(^End-Point state\s+:\s+(?P<state>Up|Down))')

        # MCT state        : None
        p3 = re.compile(r'(^MCT state\s+:\s+(?P<mctstate>\S+$))')

        # IFL-ID           : --
        # IFL-ID           : n/a
        # IFL-ID           : 1234
        p4 = re.compile(r'(^IFL-ID\s+:\s+(?P<iflid>n\/a$|\d+$|--$))')

        # Local VC type    : tag
        # Local VC type : raw-pass-through
        p5 = re.compile(r'(^Local VC type\s+:\s+(?P<vctype>tag$|raw-pass-through$|--$|raw-mode$))')

        # Local VC MTU     : 9190
        p6 = re.compile(r'(^Local VC MTU\s+:\s+(?P<mtu>\d+$|--$))')

        # COS              : --
        p7 = re.compile(r'(^COS\s+:\s+(?P<cos>\S+$))')

        # Extended Counters: Enabled
        p8 = re.compile(r'(^Extended Counters:\s+(?P<extcounters>[e|E]nabled|[d|D]isabled)$)')

        # Counter          : disabled
        p9 = re.compile(r'(^Counter\s+:\s+(?P<counter>[e|E]nabled|[d|D]isabled)$)')

        # Vll-Peer         : 192.168.1.1
        p10 = re.compile(r'(^Vll-Peer\s+:\s+(?P<ip>\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$))')

        # State          : UP
        # For all states see page 550 in reference material
        p11 = re.compile(r'(^State\s+:\s+(?P<state>UP|DOWN)(\s+[^\(]+\(Reason:(?P<reason>[^\)]+)\)$|$))')

        # Remote VC type : tag               Remote VC MTU  : 9190
        p12 = re.compile(r'(^Remote VC type\s+:\s+(?P<vctype>tag|raw-pass-through|--)\s+Remote VC MTU\s+:\s+(?P<mtu>\d+$|--$))')

        # Local label    : 852217            Remote label   : 852417
        # Local label    : --                Remote label   : --
        p13 = re.compile(r'(^Local label\s+:\s(?P<local>\d+|--)\s+Remote label\s+:\s+(?P<remote>\d+$|--$))')

        # Local group-id : 0                 Remote group-id: 0
        p14 = re.compile(r'(^Local group-id\s+:\s+(?P<localgid>\d+|--)\s+Remote group-id:\s+(?P<remotegid>\d+$|--$))')

        # Tunnel LSP     : mlx8.1_to_ces.2 (tnl15)
        p15 = re.compile(r'(^Tunnel LSP\s+:\s+(?P<lspname>[^+\s]+)\s+\((?P<tunnel>\w+)\)$)')

        # LSPs assigned  : No LSPs assigned
        p16 = re.compile(r'(^LSPs\s+assigned\s+:\s+(?P<lsps>\w+.*$))')

        for line in out.splitlines():
            line = line.strip()

            
            m = p0.match(line)
            if m:
                vll_dict = result_dict.setdefault('vll', {}).setdefault(vll, {
                    'vcid': int(m.groupdict()['vcid']),
                    'vll_index': int(m.groupdict()['vllindex'])
                })
                continue
            
            m = p1.match(line)
            if m:
                tag_type = m.groupdict()['type']

                vll_dict['local'] = {
                    'type': tag_type,
                    'interface': 'ethernet {0}'.format(m.groupdict()['interface'])
                }

                if tag_type == 'tagged':
                    vll_dict['local']['vlan_id'] = int(m.groupdict()['vid'])
                continue

            m = p2.match(line)
            if m:
                local_state = m.groupdict()['state']
                vll_dict['local']['state'] = local_state
                continue
            
            m = p3.match(line)
            if m:
                mct_state = m.groupdict()['mctstate']
                vll_dict['local']['mct_state'] = mct_state
                continue
            
            m = p4.match(line)
            if m:
                ifl_id = m.groupdict()['iflid']
                vll_dict['local']['ifl_id'] = ifl_id
                continue
            
            m = p5.match(line)
            if m:
                vc_type = m.groupdict()['vctype']
                vll_dict['local']['vc_type'] = vc_type
                continue
            
            m = p6.match(line)
            if m:
                mtu = m.groupdict()['mtu']
                if mtu == '--':
                    mtu = 0

                vll_dict['local']['mtu'] = int(mtu)
                continue
            
            m = p7.match(line)
            if m:
                vll_dict['local']['cos'] = m.groupdict()['cos']
                continue
            
            m = p8.match(line)
            if m:
                extcounters = m.groupdict()['extcounters']
                vll_dict['local']['extended_counters'] = True if extcounters.lower() == 'enabled' \
                        else False
                continue
            
            m = p9.match(line)
            if m:
                counters = m.groupdict()['counter']
                vll_dict['local']['counters'] = True if counters.lower() == 'enabled' \
                        else False
                continue

            m = p10.match(line)
            if m:
                vll_dict['peer'] = {
                    'ip': m.groupdict()['ip']
                }
                continue
            
            m = p11.match(line)
            if m:
                state = m.groupdict()['state']
                reason = m.groupdict().get('reason')
                vll_dict['peer']['state'] = state

                if state.lower() == 'down':
                    vll_dict['peer']['reason'] = reason if reason is not None \
                            else 'Unknown'
                continue
            
            m = p12.match(line)
            if m:
                vc_type = m.groupdict()['vctype']
                mtu = m.groupdict()['mtu']
                if mtu == '--':
                    mtu = 0

                vll_dict['peer']['vc_type'] = vc_type
                vll_dict['peer']['mtu'] = int(mtu)
                continue
            
            m = p13.match(line)
            if m:
                local = m.groupdict()['local']
                remote = m.groupdict()['remote']

                if local == '--':
                    vll_dict['peer']['local_label'] = local
                else:
                    vll_dict['peer']['local_label'] = int(local)
                
                if remote == '--':
                    vll_dict['peer']['remote_label'] = remote
                else:
                    vll_dict['peer']['remote_label'] = int(remote)
                continue
            
            m = p14.match(line)
            if m:
                local = m.groupdict()['localgid']
                remote = m.groupdict()['remotegid']

                if local == '--':
                    vll_dict['peer']['local_group_id'] = local
                else:
                    vll_dict['peer']['local_group_id'] = int(local)
                
                if remote == '--':
                    vll_dict['peer']['remote_group_id'] = remote
                else:
                    vll_dict['peer']['remote_group_id'] = int(remote)
                continue

            m = p15.match(line)
            if m:
                lsp = m.groupdict()['lspname']
                tunnel = m.groupdict().get('tunnel')

                if tunnel is not None:
                    vll_dict['peer']['tunnel_lsp'] = {
                        'name': lsp,
                        'tunnel_interface': tunnel
                    }
                else:
                    vll_dict['peer']['tunnel_lsp'] = {
                        'name': lsp
                    }
                continue
            
            m = p16.match(line)
            if m:
                vll_dict['peer']['lsps_assigned'] = m.groupdict()['lsps']
                continue

        return result_dict