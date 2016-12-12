import json

switches = {}
hosts = {}
network = {}
dscps = {}

with open('ext/netgraph/dscp.json') as dscp_config:
    dscps = json.load(dscp_config)

def add_link(src, src_port, dst, dst_port, **params):
    network[src][dst] = {"src": src_port, "dst": dst_port, "params": params}
    network[dst][src] = {"src": dst_port, "dst": src_port, "params": params}
    #print network

def find_path(src, dst, dscp):
    if dscp == 0x00:
        if src == "s1" or src == "10.0.0.1":
            if dst == "10.0.0.1":
                return [(switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s1'], 1), (switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s1'], 1), (switches['s2'], 2), (switches['s3'], 3)]
        elif src == "s2" or src == "10.0.0.2":
            if dst == "10.0.0.1":
                return [(switches['s2'], 1), (switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s2'], 2), (switches['s3'], 3)]
        elif src == "s3" or src == "10.0.0.3":
            if dst == "10.0.0.1":
                return [(switches['s3'], 2), (switches['s2'], 1), (switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s3'], 2), (switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s3'], 3)]
    elif dscp == 0x01:
        if src == "s1" or src == "10.0.0.1":
            if dst == "10.0.0.1":
                return [(switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s1'], 2), (switches['s3'], 2), (switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s1'], 2), (switches['s3'], 3)]
        elif src == "s2" or src == "10.0.0.2":
            if dst == "10.0.0.1":
                return [(switches['s2'], 2), (switches['s3'], 1), (switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s2'], 2), (switches['s3'], 3)]
        elif src == "s3" or src == "10.0.0.3":
            if dst == "10.0.0.1":
                return [ (switches['s3'], 1), (switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s3'], 2), (switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s3'], 3)]
    elif dscp == 0x02:
        if src == "s1" or src == "10.0.0.1":
            if dst == "10.0.0.1":
                return [(switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s1'], 1), (switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s1'], 1), (switches['s2'], 2), (switches['s3'], 3)]
        elif src == "s2" or src == "10.0.0.2":
            if dst == "10.0.0.1":
                return [(switches['s2'], 1), (switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s2'], 2), (switches['s3'], 3)]
        elif src == "s3" or src == "10.0.0.3":
            if dst == "10.0.0.1":
                return [(switches['s3'], 2), (switches['s2'], 1), (switches['s1'], 3)]
            elif dst == "10.0.0.2":
                return [(switches['s3'], 2), (switches['s2'], 3)]
            elif dst == "10.0.0.3":
                return [(switches['s3'], 3)]

def add_switch(dpid, connection):
    switches[dpid] = connection
    network[dpid] = {}

def add_host(ip, switch_dpid, switch_port):
    hosts[ip] = {"switch": switch_dpid, "port": switch_port}
    network[ip] = {}
    network[ip][switch_dpid] = {"src": '', "dst": switch_port, "params": ''}
    network[switch_dpid][ip] = {"src": switch_port, "dst": '', "params": ''}

def get_host(ip):
    return hosts.get(ip, False)

def get_switch(dpid):
    return switches.get(dpid, False)

def get_all_switches():
    return switches.iteritems()