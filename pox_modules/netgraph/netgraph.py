import json
import re

__DSCP_CONFIG = 'pox_modules/netgraph/dscp.json' if __name__ == '__main__' else 'ext/netgraph/dscp.json'

__switches = {}
__hosts = {}
__network = {}
__dscps = {}
__DEFUALT_PARAMS = {
    "bw": float('inf'),
    "delay": 0,
    "loss": 0
}
__WEIGHTS_CONFIG = {
    "bw": {
        "init": float('inf'),
        "next_val": lambda prev, current: min(prev, current)
    },
    "delay": {
        "init": 0,
        "next_val": lambda prev, current: prev + current
    },
    "loss": {
        "init": 0,
        "next_val": lambda prev, current: prev + current
    }
}
__DEFUALT_SUM_WEIGHT = -float('inf')

#Load path parameters for DSCP values
with open(__DSCP_CONFIG) as __DSCP_CONFIG:
    __dscps = json.load(__DSCP_CONFIG)

def __sum_weights(weights, multipliers):
    return sum([weights[param] * multipliers[param] for param in weights])

def __normalize(params):
    return params

def dijkstra(graph, src, dst, weight_multipliers, visited=None, predecessors=None, weights=None):
    if visited is None:
        visited = []
    if predecessors is None:
        predecessors = {}
    if weights is None:
        weights = {k: {} for k in weight_multipliers}
        weights["sum"] = {}

    if src == dst:
        path = []
        pred = (dst, 0)

        while pred != None:
            path.append(pred)
            pred = predecessors.get(pred[0], None)

        print 'Found path: ', path
        print ''
        return path
    else :     
        if not visited:
            for k in weight_multipliers:
                weights[k][src] = __WEIGHTS_CONFIG[k]["init"]
            weights["sum"][src] = __DEFUALT_SUM_WEIGHT

        for neighbor in graph[src]:
            if neighbor not in visited:
                new_weights = {k: __WEIGHTS_CONFIG[k]["next_val"](
                                      weights[k].get(src, __WEIGHTS_CONFIG[k]["init"]),
                                      graph[src][neighbor]['params'][k]
                                  ) for k in weight_multipliers}

                new_sum = __sum_weights(new_weights, weight_multipliers)

                if new_sum > weights["sum"].get(neighbor, __DEFUALT_SUM_WEIGHT):
                    for k in weight_multipliers:
                        weights[k][neighbor] = new_weights[k]
                    weights["sum"][neighbor] = new_sum

                    predecessors[neighbor] = (src, graph[src][neighbor]['src'])

        visited.append(src)

        unvisited = {}
        for k in graph:
            if k not in visited:
                unvisited[k] = weights["sum"].get(k, __DEFUALT_SUM_WEIGHT)    
  
        next = max(unvisited, key=unvisited.get)

        return dijkstra(graph, next, dst, weight_multipliers, visited, predecessors, weights)

def find_path(src, dst, dscp):
    """
    Finds a path between src and dst for parameters specified by the dscp value.
    Path parameters are taken from __DSCP_CONFIG.

    Returns a list of (switch connection, switch output port).
    """
    print 'Finding path between %s and %s for dscp = %d' % (src, dst, dscp)
    return [(__switches[switch[0]], switch[1]) 
                for switch 
                in dijkstra(__network, src, dst, __dscps[str(dscp)]) 
                if not re.match('(\d+\\.){3}\d+', switch[0])]

def add_switch(dpid, connection):
    __switches[dpid] = connection
    __network[dpid] = {}

def add_host(ip, switch_dpid, switch_port):
    __hosts[ip] = {"switch": switch_dpid, "port": switch_port}
    __network[ip] = {}
    __network[ip][switch_dpid] = {"src": 0, "dst": switch_port, "params": __normalize(__DEFUALT_PARAMS)}
    __network[switch_dpid][ip] = {"src": switch_port, "dst": 0, "params": __normalize(__DEFUALT_PARAMS)}

def add_link(src, src_port, dst, dst_port, **params):
    params = {k: v if k != 'delay' else int(re.search('\d+', v).group(0)) for k,v in params.iteritems()}
    __network[src][dst] = {"src": src_port, "dst": dst_port, "params": __normalize(params)}

def remove_link(src, dst):
    if src in __network and dst in __network[src]:
        return __network[src].pop(dst)

def remove_switch(dpid):
    del __switches[dpid]
    del __network[dpid]
    for k in __network.keys():
        remove_link(k, dpid)

def get_host(ip):
    return __hosts.get(ip, None)

def get_switch(dpid):
    return __switches.get(dpid, None)

def get_all_switches():
    return __switches.iteritems()

def get_links(src):
    return __network.get(src, None)

def get_link(src, dst):
    links = get_links(src)
    return links and links.get(dst, None)

#TEST
if __name__ == "__main__":
    __network = {  
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
             'params': __DEFUALT_PARAMS
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
                'bw':5
             }
          },
          '10.0.0.2': {
             'src': 3,
             'dst': 0,
             'params': __DEFUALT_PARAMS
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
                'bw':5
             }
          },
          '10.0.0.1': {
             'src': 3,
             'dst': 0,
             'params': __DEFUALT_PARAMS
          }
       },
       '10.0.0.1': {
            's1': {
                'src': 0,
                'dst': 3,
                'params': __DEFUALT_PARAMS
            }
       },
       '10.0.0.2': {
            's2': {
                'src': 0,
                'dst': 3,
                'params': __DEFUALT_PARAMS
            }
       },
       '10.0.0.3': {
            's3': {
                'src': 0,
                'dst': 3,
                'params': __DEFUALT_PARAMS
            }
       }
    }
    __switches = {
        's1': 'Switch 1 connection',
        's2': 'Switch 2 connection',
        's3': 'Switch 3 connection'
    }
    print find_path('s1','s3', 0x02)
    print find_path('10.0.0.1', '10.0.0.2', 0x02)
    print find_path('10.0.0.1', '10.0.0.3', 0x02)