import json
import ext.netgraph.netgraph as netgraph
from pox.core import core
from pox.lib.revent import *
import pox.openflow.libopenflow_01 as of  
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp 

class Topology(EventMixin):
    def __init__(self):
        def startup():
            core.openflow.addListeners(self)
            core.openflow_discovery.addListeners(self)

            with open('ext/static_link_params.json') as config:
                self.links = json.load(config)["links"]

        core.call_when_ready(startup, ('openflow','openflow_discovery'))

    def _handle_LinkEvent(self, event):
        src = "s%d" % event.link.dpid1
        dst = "s%d" % event.link.dpid2
        link = [x for x in self.links if (x["src"], x["dst"]) == (src, dst)]

        if len(link) > 0:
            if event.added:
                netgraph.add_link(src, event.link.port1, dst, event.link.port2, **link[0]["params"])
            elif event.removed:
                removed = netgraph.remove_link(src, dst)
                switch = netgraph.get_switch(src)
                switch and switch.send( of.ofp_flow_mod( command=of.OFPFC_DELETE, out_port=removed.src)

    def _handle_ConnectionUp(self, event):
        netgraph.add_switch("s%d" % event.dpid, event.connection)

    def _handle_ConnectionDown(self, event):
        #netgraph.remove_switch("s%d" % event.dpid)

    def _handle_PacketIn(self, event):
        packet = event.parsed

        if packet.type == ethernet.ARP_TYPE:
            arp_packet = packet.next
            src = str(arp_packet.protosrc)
            dst = str(arp_packet.protodst)
            print arp_packet, "s%d" % event.dpid

            if not netgraph.get_host(src):
                netgraph.add_host(src, "s%d" % event.dpid, event.port)
                for src_switch, connection in netgraph.get_all_switches():
                    path = netgraph.find_path(src_switch, src, 0x00)
                    for switch, port in path:
                        switch.send( of.ofp_flow_mod( action=of.ofp_action_output( port=port ),
                                                                 match=of.ofp_match( dl_type=0x0806,
                                                                                     nw_dst=arp_packet.protosrc)))
            if not netgraph.get_host(dst):
                msg = of.ofp_packet_out()
                msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
                msg.data = event.ofp
                msg.in_port = event.port
                event.connection.send(msg)
def launch():
    core.registerNew(Topology)