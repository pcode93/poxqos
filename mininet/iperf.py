from time import sleep

from topo import start
from topo import iperf

mn = start()

print 'Starting iperf test'

iperf(mn, 'h1', 'h2', 0x01)
iperf(mn, 'h1', 'h2', 0x02)

print 'Stopping mininet'
mn.stop()