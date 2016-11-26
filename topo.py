import json

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.node import RemoteController

class QosTopo(Topo):
    def build(self, config):
        for host in config["hosts"]:
            self.addHost(host)
        for switch in config["switches"]:
            self.addSwitch(switch)
        for link in config["links"]:
            self.addLink(link["src"], link["dst"], **link["params"])

def start():
    with open('static_link_params.json') as config:
        mn = Mininet(topo=QosTopo(json.load(config)), link=TCLink, controller=lambda name: RemoteController( name, ip='127.0.0.1' , port=8000))
        mn.start()
        mn.pingAll()
        mn.stop()

if __name__ == '__main__':
    setLogLevel('info')
    start()