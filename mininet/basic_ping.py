from topo import start
from topo import ping

mn = start()

print 'Starting basic ping test'

for src, dst in [('h1', 'h2'), ('h1', 'h3'), ('h2', 'h3')]:
    ping(mn, src, dst)

print 'Stopping mininet'
mn.stop()