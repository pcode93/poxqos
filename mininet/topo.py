import json

from time import sleep

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.cli import CLI

LOG_FILE = '/tmp/test.out'

class QosTopo(Topo):
    def build(self, config):
        for host in config["hosts"]:
            self.addHost(host)
        for switch in config["switches"]:
            self.addSwitch(switch)
        for link in config["links"]:
            self.addLink(link["src"], link["dst"], **link["params"])

def print_log():
    f = open(LOG_FILE)
    for line in f.readlines():
        print "%s" % line.strip()
    f.close()

def ping(mn, src, dst):
    print 'Ping from %s to %s' % (src, dst)

    mn.get(src).cmd('ping %s > %s &' % (mn.get(dst).IP(), LOG_FILE))
    sleep(5)
    mn.get(src).cmd('kill %ping')

    print_log()

    print 'Done'

def iperf(mn, src, dst, dscp):
    print 'Generating traffic for dscp = 0x%02x' % dscp

    mn.get(dst).cmd('iperf -p 10000 -s &')
    sleep(2)
    mn.get(src).cmd('iperf -p 10000 -c %s -S 0x%02x > %s &' % (mn.get(dst).IP(), dscp << 2, LOG_FILE))
    sleep(5)
    mn.get(src).cmd('kill %iperf')
    sleep(1)
    mn.get(dst).cmd('kill %iperf')
    sleep(1)
    print_log()

    print 'Done'

def start():
    #The topology is loaded from static_link_params.json
    with open('static_link_params.json') as config:
        print 'Starting mininet'
        mn = Mininet(topo=QosTopo(json.load(config)),
                     link=TCLink,
                     controller=lambda name: RemoteController(name, ip='127.0.0.1', port=8000))
        mn.start()
        sleep(10)
        return mn

if __name__ == '__main__':
    mn = start()
    CLI(mn)
    mn.stop()