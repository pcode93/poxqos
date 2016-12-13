import json
import re

DSCP_CONFIG = 'pox_modules/netgraph/dscp.json' if __name__ == '__main__' else 'ext/netgraph/dscp.json'

switches = {}
hosts = {}
network = {}
dscps = {}
default_params = {
    "bw": 10,
    "delay": 50,
    "loss": 0
}

with open(DSCP_CONFIG) as dscp_config:
    dscps = json.load(dscp_config)

def dijkstra(graph,src,dest,bw_w,delay_w,loss_w,visited=[],predecessors={},bw={},delay={},loss={}, weight={}):
    if src == dest:
        path = []
        pred = (dest, 0)
        while pred != None:
            path.append(pred)
            pred = predecessors.get(pred[0],None)
        return path
    else :     
        if not visited: 
            bw[src] = 0
            delay[src] = 0
            loss[src] = 0
            weight[src] = 0

        for neighbor in graph[src] :
            if neighbor not in visited:
                new_bw = min(bw[src], graph[src][neighbor]['params']['bw'] )
                new_loss = loss[src] + graph[src][neighbor]['params']['loss']
                new_delay = delay[src] + graph[src][neighbor]['params']['delay']
                new_weight = bw_w * new_bw + delay_w * new_delay + loss_w * new_loss

                if new_weight > weight.get(neighbor,-float('inf')):
                    weight[neighbor] = new_weight
                    loss[neighbor] = new_loss
                    delay[neighbor] = new_delay
                    bw[neighbor] = new_bw
                    predecessors[neighbor] = (src, graph[src][neighbor]['src'])

        visited.append(src)

        unvisited = {}
        for k in graph:
            if k not in visited:
                unvisited[k] = weight.get(k,-float('inf'))    
  
        next = max(unvisited, key=unvisited.get)

        return dijkstra(graph,next,dest,bw_w, delay_w, loss_w,visited,predecessors,bw,delay,loss, weight)

def add_link(src, src_port, dst, dst_port, **params):
    params = {k: v if k != 'delay' else int(re.search('\d+', v).group(0)) for k,v in params.iteritems()}
    network[src][dst] = {"src": src_port, "dst": dst_port, "params": params}
    network[dst][src] = {"src": dst_port, "dst": src_port, "params": params}

    #print network
def find_path(src, dst, dscp):
    return map(lambda switch: (switches[switch[0]], switch[1]), 
                filter(lambda node: not re.match('(\d+\\.){3}\d+', node[0]), 
                        dijkstra(network, src, dst, *dscps[str(dscp)].values())))

def find_path_temp(src, dst, dscp):
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
    network[ip][switch_dpid] = {"src": 0, "dst": switch_port, "params": default_params}
    network[switch_dpid][ip] = {"src": switch_port, "dst": 0, "params": default_params}

def get_host(ip):
    return hosts.get(ip, False)

def get_switch(dpid):
    return switches.get(dpid, False)

def get_all_switches():
    return switches.iteritems()

if __name__ == "__main__":
    network = {  
       's3':{  
          's2':{  
             'src':2,
             'dst':2,
             'params':{  
                'delay':150,
                'loss':3,
                'bw':50
             }
          },
          's1':{  
             'src':1,
             'dst':2,
             'params':{  
                'delay':10,
                'loss':0,
                'bw':10
             }
          },
          '10.0.0.3': {
             'src': 3,
             'dst': 0,
             'params': default_params
          }
       },
       's2':{  
          's3':{  
             'src':2,
             'dst':2,
             'params':{  
                'delay':150,
                'loss':3,
                'bw':50
             }
          },
          's1':{  
             'src':1,
             'dst':1,
             'params':{  
                'delay':100,
                'loss':5,
                'bw':100
             }
          },
          '10.0.0.2': {
             'src': 3,
             'dst': 0,
             'params': default_params
          }
       },
       's1':{  
          's3':{  
             'src':2,
             'dst':1,
             'params':{  
                'delay':10,
                'loss':0,
                'bw':10
             }
          },
          's2':{  
             'src':1,
             'dst':1,
             'params':{  
                'delay':100,
                'loss':5,
                'bw':100
             }
          },
          '10.0.0.1': {
             'src': 3,
             'dst': 0,
             'params': default_params
          }
       },
       '10.0.0.1': {
            's1': {
                'src': 0,
                'dst': 3,
                'params': default_params
            }
       },
       '10.0.0.2': {
            's2': {
                'src': 0,
                'dst': 3,
                'params': default_params
            }
       },
       '10.0.0.3': {
            's3': {
                'src': 0,
                'dst': 3,
                'params': default_params
            }
       }
    }
    switches = {
        's1': 'Switch 1 connection',
        's2': 'Switch 2 connection',
        's3': 'Switch 3 connection'
    }
    print find_path('s1','s3', '0x02')
    print find_path('10.0.0.1', '10.0.0.2', '0x02')
    print find_path('10.0.0.1', '10.0.0.3', '0x02')