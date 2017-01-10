import ext.netgraph.netgraph as netgraph
from pox.core import core
from pox.lib.revent import *
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4

class Qos(EventMixin):

    def __init__(self):
        def startup():
            core.openflow.addListeners(self)

        core.call_when_ready(startup, ('openflow'))

    def _handle_PacketIn(self, event):
        """
        PacketIn event callback.
        Handles IPv4 packets.
        Finds paths for IPv4 packets based on DSCP values.
        """

        packet = event.parsed

        if isinstance(packet.next, ipv4):
            print packet.next
            path = netgraph.find_path(str(packet.next.srcip), str(packet.next.dstip), packet.next.tos >> 2)
            for switch, port in path:
                switch.send(of.ofp_flow_mod(command=of.OFPFC_DELETE,
                                            match=of.ofp_match(dl_type=0x0800,
                                                               nw_src=packet.next.srcip,
                                                               nw_dst=packet.next.dstip,
                                                               nw_tos=packet.next.tos)))

                switch.send(of.ofp_flow_mod(action=of.ofp_action_output(port=port),
                                            priority=10000,
                                            match=of.ofp_match(dl_type=0x0800,
                                                               nw_src=packet.next.srcip,
                                                               nw_dst=packet.next.dstip,
                                                               nw_tos=packet.next.tos)))

def launch():
    core.registerNew(Qos)