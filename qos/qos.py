import json
import netgraph
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4

class Qos(EventMixin):

    def __init__(self):
        def startup():
            core.openflow.addListeners(self)

            with open('dscp.json') as dscps:
                self.dscps = json.load(dscps)

        core.call_when_ready(startup, ('openflow'))

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if isinstance(packet.next, ipv4):
            path = netgraph.findPath(packet.next.srcip, packet.next.dstip, self.dscps['%x' % packet.next.tos])
            for switch, port in path:
                switch.connection.send( of.ofp_flow_mod( action=of.ofp_action_output( port=port ),
                                                         match=of.ofp_match( dl_type=0x0800, 
                                                                             nw_dst=src,
                                                                             nw_tos=packet.next.tos)))

def launch():
    core.registerNew(Qos)