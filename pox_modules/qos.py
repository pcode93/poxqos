import json
import ext.netgraph.netgraph as netgraph
from pox.core import core
from pox.lib.revent import *
import pox.openflow.libopenflow_01 as of  
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp 
from pox.lib.addresses import IPAddr

class Qos(EventMixin):
    def __init__(self):
        def startup():
            core.openflow.addListeners(self)
            core.openflow_discovery.addListeners(self)

            #Load static_link_params.json which contains parameters for all links in the network
            with open('ext/static_link_params.json') as config:
                self.links = json.load(config)["links"]

        netgraph.observe(self._new_path)
        core.call_when_ready(startup, ('openflow', 'openflow_discovery'))

    def _new_path(self, event):
        """
        Called whenever a new path has been added.
        Modifies flow tables in switches accordingly.
        Paths for dscp value of 0 are also ARP paths.
        """
        for switch, port in event["path"]:
            switch.send(of.ofp_flow_mod(command=of.OFPFC_DELETE,
                                        match=of.ofp_match(dl_type=0x0800,
                                                           nw_src=event["src"],
                                                           nw_dst=event["dst"],
                                                           nw_tos=event["dscp"] << 2)))

            switch.send(of.ofp_flow_mod(action=of.ofp_action_output(port=port),
                                        priority=10000,
                                        match=of.ofp_match(dl_type=0x0800,
                                                           nw_src=event["src"],
                                                           nw_dst=event["dst"],
                                                           nw_tos=event["dscp"] << 2)))
        if event["dscp"] == 0x00:
            for switch, port in event["path"]:
                switch.send(of.ofp_flow_mod(command=of.OFPFC_DELETE,
                                            match=of.ofp_match(dl_type=0x0806,
                                                               nw_src=event["src"],
                                                               nw_dst=event["dst"])))

                switch.send(of.ofp_flow_mod(action=of.ofp_action_output(port=port),
                                            match=of.ofp_match(dl_type=0x0806,
                                                               nw_src=event["src"],
                                                               nw_dst=event["dst"])))

    def _handle_LinkEvent(self, event):
        """
        LinkEvent event callback.
        Handles addition and removal of links.
        Link parameters are taken from static_link_params.json.
        """

        src = "s%d" % event.link.dpid1
        dst = "s%d" % event.link.dpid2

        #Find this link in static_link_params.json
        link = [x for x in self.links if (x["src"], x["dst"]) == (src, dst) or (x["src"], x["dst"]) == (dst, src)]

        if len(link) > 0:
            if event.added:
                netgraph.add_link(src, event.link.port1, dst, event.link.port2, **link[0]["params"])
            elif event.removed:
                removed = netgraph.remove_link(src, dst)
                switch = netgraph.get_switch(src)

                #If there is a connection to the source switch, delete all flow entries for that link 
                switch and switch.send(of.ofp_flow_mod(command=of.OFPFC_DELETE, out_port=removed["src"]))

    def _handle_ConnectionUp(self, event):
        """
        ConnectionUp event callback.
        Registers a Switch when it connects.
        """

        netgraph.add_switch("s%d" % event.dpid, event.connection)

    def _handle_ConnectionDown(self, event):
        pass
        #netgraph.remove_switch("s%d" % event.dpid)

    def _handle_PacketIn(self, event):
        """
        PacketIn event callback.
        Handles ARP packets.
        Helps register hosts.
        Helps hosts discover each other.

        Hosts do not send any notifications to the Controller
        therefore it does not know whether they are connected to the network.

        A Host is registered everytime a switch receives an ARP packet from an unknown source.
        If the packets destination is unknown, it is sent out on all ports.
        """

        packet = event.parsed

        if packet.type == ethernet.ARP_TYPE:
            arp_packet = packet.next
            src = str(arp_packet.protosrc)
            dst = str(arp_packet.protodst)
            #print arp_packet, "s%d" % event.dpid

            if not netgraph.get_host(src):
                netgraph.add_host(src, "s%d" % event.dpid, event.port)

            if not netgraph.get_host(dst):
                msg = of.ofp_packet_out()
                msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
                msg.data = event.ofp
                msg.in_port = event.port
                event.connection.send(msg)

def launch():
    core.registerNew(Qos)