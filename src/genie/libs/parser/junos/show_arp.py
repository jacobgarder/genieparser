# Python
import re

# Metaparser
from genie.metaparser import MetaParser
from genie.metaparser.util.schemaengine import (Any, 
        Optional, Use, SchemaTypeError, Schema)

class ShowArpSchema(MetaParser):
    """ Parser for:
            * show arp
            * show arp | no-more
    """
    """schema = {
        "arp-table-information": {
            "arp-entry-count": str,
            "arp-table-entry": [
                {
                    "arp-table-entry-flags": str,
                    "hostname": str,
                    "interface-name": str,
                    "ip-address": str,
                    "mac-address": str
                }
            ]
        }
    }"""

    def validate_arp_table_entry_list(value):
        # Pass arp-entry list of dict in value
        if not isinstance(value, list):
            raise SchemaTypeError('arp-table-entry is not a list')
        # Create Arp Entry Schema
        entry_schema = Schema({
            "arp-table-entry-flags": str,
            "hostname": str,
            "interface-name": str,
            "ip-address": str,
            "mac-address": str
        })
        # Validate each dictionary in list
        for item in value:
            entry_schema.validate(item)
        return value
    
    # Main Schema
    schema = {
        "arp-table-information": {
            "arp-entry-count": str,
            "arp-table-entry": Use(validate_arp_table_entry_list)
        }
    }

class ShowArp(ShowArpSchema):
    """ Parser for:
            * show arp
    """
    cli_command = 'show arp'
    
    def cli(self, output=None):

        if not output:
            out = self.device.execute(cli_command)
        else:
            out = output

        ret_dict = {}

        # 00:50:56:8d:2d:e1 1.0.0.1         1.0.0.1                   fxp0.0                  none
        p1 = re.compile(r'^(?P<mac_address>[\w:]+) +(?P<address>\S+) +(?P<name>\S+) +'
                r'(?P<interface>\S+) +(?P<flags>\S+)$')
        
        # Total entries: 7
        p2 = re.compile(r'^Total +entries: +(?P<total_entries>\d+)$')

        for line in out.splitlines():
            line = line.strip()
            
            # 00:50:56:8d:2d:e1 1.0.0.1         1.0.0.1                   fxp0.0                  none
            m = p1.match(line)
            if m:
                group = m.groupdict()
                mac_address = group['mac_address']
                address = group['address']
                name = group['name']
                interface = group['interface']
                flags = group['flags']
                arp_table_entry_list = ret_dict.setdefault('arp-table-information', {}). \
                    setdefault('arp-table-entry', [])
                arp_table_entry_dict = {}
                arp_table_entry_dict['interface-name'] = interface
                arp_table_entry_dict['mac-address'] = mac_address
                arp_table_entry_dict['ip-address'] = address
                arp_table_entry_dict['hostname'] = name
                arp_table_entry_dict['arp-table-entry-flags'] = flags
                arp_table_entry_list.append(arp_table_entry_dict)
                continue
        
            m = p2.match(line)
            if m:
                group = m.groupdict()
                total_entries = group['total_entries']
                ret_dict.setdefault('arp-table-information', {}).\
                    setdefault('arp-entry-count', total_entries)
                continue
        return ret_dict

class ShowArpNoMore(ShowArp):
    """ Parser for:
            * show arp | no-more
    """
    cli_command = 'show arp | no-more'
    def cli(self, output=None):

        if not output:
            out = self.device.execute(self.cli_command)
        else:
            out = output
        
        return super().cli(output=out)