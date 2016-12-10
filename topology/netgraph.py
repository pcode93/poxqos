switches = {}
hosts = {}
network = {}

def add_link(src, src_port, dst, dst_port, **params):
    network[src][dst] = {"src": src_port, "dst": dst_port, "params": params}
    network[dst][src] = {"src": dst_port, "dst": src_port, "params": params}
    print network

def find_path(src, dst, **params):
    pass

def add_switch(dpid, connection):
    switches[dpid] = connection
    network[dpid] = {}

def add_host(ip, switch_dpid, switch_port):
    hosts[ip] = {"switch": switch_dpid, "port": switch_port}
    network[ip] = {}
    network[ip][switch_dpid] = {"src": '', "dst": switch_port, "params": ''}
    network[switch_dpid][ip] = {"src": switch_port, "dst": '', "params": ''}

def get_host(ip):
    return hosts[ip]

def get_switch(dpid):
    return switches[dpid]

def get_all_switches():
    return switches