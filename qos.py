from pox.core import core  
import pox.openflow.libopenflow_01 as of  
from pox.lib.revent import *  
from pox.lib.recoco import Timer  
from collections import defaultdict  
from pox.openflow.discovery import Discovery  
from pox.lib.util import dpid_to_str
from pox.lib.packet import ipv4  
import time
import json
import netgraph

class qos(EventMixin):

    def __init__(self):
        def startup():
            core.openflow.addListeners(self)
            core.openflow_discovery.addListeners(self)
            core.host_tracker.addListeners(self)

            with open('static_link_params.json') as config:
                self.links = json.load(config)["links"]

            with open('dscp.json') as dscps:
                self.dscps = json.load(dscps)

        core.call_when_ready(startup, ('openflow','openflow_discovery', 'host_tracker'))

    def _handle_LinkEvent(self, event):
        src = 's%d' % event.link.dpid1
        dst = 's%d' % event.link.dpid2

        link = [x for x in self.links if (x["src"], x["dst"]) == (src, dst)]
        len(link) > 0 and netgraph.addLink(src, dst, **link[0]["params"])

    def _handle_ConnectionUp(self, event):
        pass

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if isinstance(packet.next, ipv4):
            netgraph.findPath(packet.next.srcip, packet.next.dstip, self.dscps['%x' % packet.next.tos])

    def _handle_HostEvent(self, event):
        pass

def launch():
    core.registerNew(qos)