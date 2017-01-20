from time import sleep

from topo import start
from topo import ping

mn = start()

print 'Starting ping with failed link test'

ping(mn, 'h1', 'h2')

print 'Turning off link between s1 and s2'
mn.get('s1').cmd('ifconfig s1-eth2 down')
sleep(7)
print 'Done'

ping(mn, 'h1', 'h2')

print 'Stopping mininet'
mn.stop()