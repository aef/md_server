#
# libvirt.py: extract data from libvirt and libvirt domain XML
#
# Copyright 2020 Australian National University
#
# Please see the LICENSE.txt file for details.

import xmltodict
from mdserver.database import Database


def get_domain_data(domain, mds_net):
    """Extract key data from the supplied domain XML.

    Data extracted are: the name, uuid, and MAC address from the mds network
    interface.
    """

    ddata = Database.new_entry()
    dom = xmltodict.parse(domain)
    ddata['domain_name'] = dom['domain']['name']
    ddata['domain_uuid'] = dom['domain']['uuid']
    try:
        mds_interfaces = [i for i in dom['domain']['devices']['interface']
                          if '@network' in i['source'] and
                          i['source']['@network'] == mds_net]
        ddata['mds_mac'] = mds_interfaces[0]['mac']['@address']
    except KeyError:
        return None
    return ddata
