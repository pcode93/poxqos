from __future__ import division

import json
import re

from functools import partial

from pox.lib.addresses import IPAddr

_DSCP_CONFIG = 'pox_modules/netgraph/dscp.json' if __name__ == '__main__' else 'ext/netgraph/dscp.json'

_switches = {}
_hosts = {}

_network = {}
"""
A dictionary holding information about links in the network.
"""

_dscps = {}
_known_paths = {}

_obs = []
"""
List of observers that need to be notified 
whenever there is a new path added.
"""

_DEFUALT_PARAMS = {
    "bw": float('inf'),
    "delay": 0,
    "loss": 0
}

_NORMALIZE_MAX = 1
_NORMALIZE_MIN = 0

_DEFAULT_NORMALIZE = lambda min, max, val: _NORMALIZE_MAX if val > max else (val - min) / (max - min)
_DEFAULT_NORMALIZE_INVERSE = lambda min, max, val: _NORMALIZE_MIN if val > max else (max - val) / (max - min)

_WEIGHTS_CONFIG = {
    "bw": {
        "best": 1000,
        "worst": 0,
        "normalize": partial(_DEFAULT_NORMALIZE, 0, 1000),
        "next_val": lambda prev, current: min(prev, current)
    },
    "delay": {
        "best": 0,
        "worst": 300,
        "normalize": partial(_DEFAULT_NORMALIZE_INVERSE, 0, 300),
        "next_val": lambda prev, current: prev + current
    },
    "loss": {
        "best": 0,
        "worst": 30,
        "normalize": partial(_DEFAULT_NORMALIZE_INVERSE, 0, 30),
        "next_val": lambda prev, current: prev + current
    }
}
"""
An object holding configuration for all parameters.
Every parameter must have a maximum and minimum value
as well as a normalizing function and a function
which calculates the next step in the shortest path algorithm.
"""

_DEFUALT_SUM_WEIGHT = -float('inf')

#Load path parameters for DSCP values
with open(_DSCP_CONFIG) as _DSCP_CONFIG:
    _dscps = json.load(_DSCP_CONFIG)

def _sum_weights(weights, multipliers):
    return sum([weights[param] * multipliers[param] for param in weights])

def _normalize(params):
    """
    Applies a normalizing function to every parameter.
    Every parameter has its own normalizing function.
    Returns a new dictionary with normalized parameters.
    """

    return {k: _WEIGHTS_CONFIG[k]["normalize"](v) for k, v in params.iteritems()}

def _dijkstra(graph, src, dst, weight_multipliers, visited=None, predecessors=None, weights=None):
    """
    Shortest path algorithm where links have multiple weights.
    Weights to include are specified by @weight_multipliers.
    """

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
                weights[k][src] = _WEIGHTS_CONFIG[k]["best"]

        for neighbor in graph[src]:
            if neighbor not in visited:
                new_weights = {k: _WEIGHTS_CONFIG[k]["next_val"](
                                      weights[k].get(src, _WEIGHTS_CONFIG[k]["best"]),
                                      graph[src][neighbor]['params'][k]
                                  ) for k in weight_multipliers}

                new_sum = _sum_weights(_normalize(new_weights), weight_multipliers)

                if new_sum > weights["sum"].get(neighbor, _DEFUALT_SUM_WEIGHT):
                    for k in weight_multipliers:
                        weights[k][neighbor] = new_weights[k]
                    weights["sum"][neighbor] = new_sum

                    predecessors[neighbor] = (src, graph[src][neighbor]['src'])

        visited.append(src)

        unvisited = {}
        for k in graph:
            if k not in visited:
                unvisited[k] = weights["sum"].get(k, _DEFUALT_SUM_WEIGHT)
  
        next = max(unvisited, key=unvisited.get)

        return _dijkstra(graph, next, dst, weight_multipliers, visited, predecessors, weights)

def _find_path(src, dst, dscp):
    """
    Finds a path between src and dst for parameters specified by the dscp value.
    Path parameters are taken from the dscp config file.

    Returns a list of (switch connection, switch output port).
    """

    print 'Finding path between %s and %s for dscp = %s' % (src, dst, dscp)

    return [(_switches[switch[0]], switch[1]) 
                for switch 
                in _dijkstra(_network, src, dst, _dscps[str(dscp)]) 
                if not re.match('(\d+\\.){3}\d+', switch[0])]

def _recalculate_paths():
    """
    Calculates paths between all hosts for all dscp values.
    If a new path is found, it is remember and all observers get notified. 
    """

    for src in _hosts:
        for dst in _hosts:
            for dscp in _dscps:
                if src != dst:
                    path = _find_path(src, dst, dscp)
                    if path != _known_paths.get((src, dst, dscp), None):
                        _known_paths[(src, dst, dscp)] = path
                        for o in _obs:
                            o({
                                "src": IPAddr(src),
                                "dst": IPAddr(dst),
                                "path": path,
                                "dscp": int(dscp)
                            })

def add_link(src, src_port, dst, dst_port, **params):
    """
    Adds a new link and recalculates all paths.
    """

    print 'Added link between %s and %s with params: %s' % (src, dst, params)

    params = {k: v if k != 'delay' else int(re.search('\d+', str(v)).group(0)) for k,v in params.iteritems()}
    _network[src][dst] = {"src": src_port, "dst": dst_port, "params": params}

    _recalculate_paths()

def add_switch(dpid, connection):
    _switches[dpid] = connection
    _network[dpid] = {}

def add_host(ip, switch_dpid, switch_port):
    _hosts[ip] = {"switch": switch_dpid, "port": switch_port}
    _network[ip] = {}

    add_link(ip, 0, switch_dpid, switch_port, **_DEFUALT_PARAMS)
    add_link(switch_dpid, switch_port, ip, 0, **_DEFUALT_PARAMS)

def remove_link(src, dst):
    """
    Removes a link and recalculates all paths.
    """

    print 'Removed link between %s and %s' % (src, dst)

    if src in _network and dst in _network[src]:
        link = _network[src].pop(dst)
        _recalculate_paths()
        return link

def remove_switch(dpid):
    del _switches[dpid]
    del _network[dpid]

    for k in _network.keys():
        remove_link(k, dpid)

def get_host(ip):
    return _hosts.get(ip, None)

def get_switch(dpid):
    return _switches.get(dpid, None)

def get_all_switches():
    return _switches.iteritems()

def get_links(src):
    return _network.get(src, None)

def get_link(src, dst):
    links = get_links(src)
    return links and links.get(dst, None)

def observe(cb):
    """
    Adds a new callback to the list of observers.
    """
    _obs.append(cb)

#TEST
if __name__ == "__main__":
    _network = {  
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
             'params': _DEFUALT_PARAMS
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
             'params': _DEFUALT_PARAMS
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
             'params': _DEFUALT_PARAMS
          }
       },
       '10.0.0.1': {
            's1': {
                'src': 0,
                'dst': 3,
                'params': _DEFUALT_PARAMS
            }
       },
       '10.0.0.2': {
            's2': {
                'src': 0,
                'dst': 3,
                'params': _DEFUALT_PARAMS
            }
       },
       '10.0.0.3': {
            's3': {
                'src': 0,
                'dst': 3,
                'params': _DEFUALT_PARAMS
            }
       }
    }
    _switches = {
        's1': 'Switch 1 connection',
        's2': 'Switch 2 connection',
        's3': 'Switch 3 connection'
    }
    print _find_path('s1','s3', 0x02)
    print _find_path('10.0.0.1', '10.0.0.2', 0x02)
    print _find_path('10.0.0.1', '10.0.0.3', 0x02)