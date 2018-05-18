from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import os
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

import networkx as nx
import numpy as np
from ditto.models.line import Line
from ditto.network.network import Network
from ditto.metrics.network_analysis import network_analyzer


logger = logging.getLogger('layerstack.layers.Compute_Metrics_From_Duke')


class Compute_Metrics_From_Duke(DiTToLayerBase):
    name = "compute_metrics_from_duke"
    uuid = UUID("cc8c7460-bb10-4968-9265-f4ea0b50d147")
    version = '0.1.0'
    desc = "compute metrics from duke feeders"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('arg_name', description='', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['data_folder_path'] = Kwarg(default=None, description='Path to the folder holding the cyme files',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['network_filename'] = Kwarg(default=None, description='Name of the network file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['equipment_filename'] = Kwarg(default=None, description='Name of the equipment file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['excel_output_filename'] = Kwarg(default=None, description='Path to the excel output metric file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['json_output_filename'] = Kwarg(default=None, description='Path to the excel output metric file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['compute_kva_density_with_transformers'] = Kwarg(default=None, description='Flag to use transformers or loads to compute the kva density metric',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, *args, **kwargs):

        m = stack.model
  
        data_folder_path = kwargs['data_folder_path']      
        network_filename = kwargs['network_filename']
        equipment_filename = kwargs['equipment_filename']  
        excel_output_filename = kwargs['excel_output_filename']  
        json_output_filename = kwargs['json_output_filename']   
        compute_kva_density_with_transformers = kwargs['compute_kva_density_with_transformers'] 
           
        #Instanciate the feeder parser to get the feeder metadata 
        _f = feeder_parser( os.path.join(data_folder_path,network_filename),
                            os.path.join(data_folder_path,equipment_filename)
                          )
        #Parse...
        _f.parse()

        #Parse the source voltages to set the nominal voltages later
        _f.parse_src_voltage()

        #Since the data are really noisy, we get disconnected components when using the
        #Network_analyzer module directly. Instead, we build the graph "manually" and
        #remove disconnected components
        #
        #Create an empty graph, edge set, and node set
        graph = nx.Graph()
        graph_edges = set()
        graph_nodes = set()

        #Build the graph from the DiTTo model using connection information
        for i in m.models:
            
            if hasattr(i, 'name') and i.name is not None:
                object_type = type(i).__name__
            if hasattr(i, 'from_element') and i.from_element is not None and hasattr(i, 'to_element') and i.to_element is not None:
                if hasattr(i, 'length') and i.length is not None:
                    length = i.length
                else:
                    length = 0 
                a = len(graph_nodes)
                graph_nodes.add(i.to_element)
                b = len(graph_nodes)
                if b == a + 1:
                    graph.add_node(i.to_element)
                a = len(graph_nodes)
                graph_nodes.add(i.from_element)
                b = len(graph_nodes)
                if b == a + 1:
                    graph.add_node(i.from_element)
                graph.add_edge(i.from_element, i.to_element, equipment=object_type, 
                               equipment_name=i.name, length=length)
                graph_edges.add((i.from_element, i.to_element))
            if hasattr(i, 'connecting_element') and i.connecting_element is not None:
                a = len(graph_nodes)
                graph_nodes.add(i.connecting_element)
                b = len(graph_nodes)
                if b == a + 1:
                    graph.add_node(i.connecting_element)
                a = len(graph_nodes)
                graph_nodes.add(i.name)
                b = len(graph_nodes)
                if b == a + 1:
                    graph.add_node(i.name)
                a = len(graph_edges)
                graph_edges.add((i.connecting_element, i.name))
                b = len(graph_edges)
                if b == a + 1:
                    graph.add_edge(*(i.connecting_element, i.name))

        #Create a dictionary of the edge equipment type
        edge_equipment = nx.get_edge_attributes(graph, 'equipment')

        #Create a dictionary of the edge equipment name
        edge_equipment_name = nx.get_edge_attributes(graph, 'equipment_name')

        #Create a "fake" source that we connect to all other sources in the graph
        mega_source='mega_source'
        graph.add_node(mega_source)
        for f_name,source in _f.mapp_feeder_source.items():
            head_node = _f.mapp_feeder_headnode[f_name]
            graph.add_edge(mega_source,head_node,length=0)
    
        #Grab the giant component of the graph
        giant = list(nx.connected_component_subgraphs(graph))[0]

        #Create the directed graph from the giant connected component
        digraph = nx.DiGraph()
        digraph.add_edges_from(list(bfs_order(giant, source=mega_source)))

        #Add the edge data to the directed graph
        for edge in edge_equipment:
            if digraph.has_edge(*edge):
                digraph[edge[0]][edge[1]]['equipment'] = edge_equipment[edge]
            elif digraph.has_edge(*edge[::-1]):
                digraph[edge[1]][edge[0]]['equipment'] = edge_equipment[edge]

        for edge in edge_equipment_name:
            if digraph.has_edge(*edge):
                digraph[edge[0]][edge[1]]['equipment_name'] = edge_equipment_name[edge]
            elif digraph.has_edge(*edge[::-1]):
                digraph[edge[1]][edge[0]]['equipment_name'] = edge_equipment_name[edge]

        
        #Set the nominal voltages using the mapping
        for src in nx.neighbors(giant,mega_source):
            try:
                m=set_nominal_voltages_recur(m, mega_source, edge_equipment, edge_equipment_name, digraph, src,
                                       _f.mapp_source_voltage[_f.mapp_headnode_source[src]],
                                       src)
                m=set_nominal_voltages_recur_line(m)
            except:
                pass

    
        #Create an empty Network object
        netw=Network()

        #and add the networks we just built...
        netw.provide_graphs(giant.copy(), digraph.copy())
        netw.set_attributes(m)

        #Create an empty network analyzer
        _net_analyzer=network_analyzer(m,False,mega_source)

        #and provide the Network object we just created
        _net_analyzer.provide_network(netw)

        #Add the feeder information we have parsed
        _net_analyzer.add_feeder_information(list(_f.mapp_feeder_nodes.keys()),
                                             list(_f.mapp_feeder_nodes.values()),
                                             _f.mapp_feeder_headnode,
                                                'unknown')

        #Split the network into feeders
        _net_analyzer.split_network_into_feeders()

        #Tage the objects with their respective feeder names
        _net_analyzer.tag_objects()

        #Set the model names
        _net_analyzer.model.set_names()

        #At this point we should be able to run the metric extraction...
        _net_analyzer.compute_all_metrics_per_feeder(compute_kva_density_with_transformers=compute_kva_density_with_transformers)
        
        #Finally, export the results to JSON
        _net_analyzer.export_json(json_output_filename)

        #...and to excel
        _net_analyzer.export(excel_output_filename)

        return _net_analyzer.model



class feeder_parser:
    '''
        This class parses the CYME network ASCII file of the model.
        It uses the sections to provide usefull mappings:
            - mapp_feeder_section: 
                - keys = feeder names 
                - values = section IDs in this feeder
            - mapp_section_nodes: 
                - keys = section IDs
                - values = Node IDs of the section as a tuple
            - mapp_feeder_nodes:
                - keys = feeder names
                - values = Node Ids in this feeder
            - mapp_node_feeder:
                - keys = Node IDs
                - values = Name of the feeder containing this node
    '''
    
    def __init__(self, network_file,equipment_file):
        '''
            Class CONSTRUCTOR
        '''
        self.network_file=network_file
        self.equipment_file=equipment_file
        self.mapp_feeder_section={}
        self.mapp_section_nodes={}
        self.mapp_feeder_nodes={}
        self.mapp_node_feeder={}
        self.mapp_feeder_headnode={}
        self.mapp_feeder_source={}
        self.mapp_headnode_source={}
        self.mapp_source_headode={}
        self.mapp_source_voltage={}
        
    def parse_src_voltage(self):
        '''
            Parse the [SOURCE] section of the network file and 
            the [SUBSTATION] section of the equipment file.
            Create the following mapping:
                - mapp_headnode_source: mapp node IDs to source IDs
                - 
        '''
        with open(self.network_file,'r') as f:
            lines=iter(f.readlines())
        line=next(lines)
        while '[SOURCE]' not in line:
            line=next(lines)
        raw_format_source=next(lines)
        format_source=raw_format_source.split('=')[1].split(',')
        while True:
            line=next(lines)
            if len(line)<=3:
                break
            sourceID,nodeID=np.array(line.split(','))[[0,2]]
            self.mapp_headnode_source[nodeID]=sourceID
            self.mapp_source_headode[sourceID]=nodeID
            
        with open(self.equipment_file,'r') as f:
            lines=iter(f.readlines())
        line=next(lines)
        while '[SUBSTATION]' not in line:
            line=next(lines)
        raw_format_substation=next(lines)
        format_substation=raw_format_substation.split('=')[1].split(',')
        while True:
            line=next(lines)
            if len(line)<=3:
                break
            sourceID,voltage=np.array(line.split(','))[[0,6]]
            self.mapp_source_voltage[sourceID]=float(voltage)*10**3
        
    def parse(self):
        '''
            Parse the ASCII file.
        '''
        with open(self.network_file,'r') as f:
            lines=iter(f.readlines())
        line=next(lines)
        while '[SECTION]' not in line:
            line=next(lines)
        raw_format_section=next(lines)
        format_section=raw_format_section.split('=')[1].split(',')
        raw_format_feeder=next(lines)
        format_feeder=raw_format_feeder.split('=')[1].split(',')
        while True:
            line=next(lines)
            if len(line)<=3:
                break
            if 'FEEDER=' in line:
                feeder_name=line.split('=')[1].split(',')[0]
                headnode_name=line.split('=')[1].split(',')[1]
                source_name=headnode_name+'_src'
                self.mapp_feeder_source[feeder_name]=source_name
                if feeder_name in self.mapp_feeder_section:
                    raise ValueError('.')
                if feeder_name in self.mapp_feeder_headnode:
                    raise ValueError('.')
                self.mapp_feeder_headnode[feeder_name]=headnode_name
                self.mapp_feeder_section[feeder_name]=[]
                self.mapp_feeder_nodes[feeder_name]=[]
                self.mapp_feeder_nodes[feeder_name].append(headnode_name)
                self.mapp_feeder_nodes[feeder_name].append(source_name)
            else:
                section_id,from_node_id,to_node_id=np.array(line.split(','))[[0,1,3]]
                section_id=section_id.lower()
                self.mapp_feeder_section[feeder_name].append(section_id)

                self.mapp_feeder_nodes[feeder_name].append(from_node_id)
                self.mapp_node_feeder[from_node_id]=feeder_name

                self.mapp_feeder_nodes[feeder_name].append(to_node_id)
                self.mapp_node_feeder[to_node_id]=feeder_name
                if section_id in self.mapp_section_nodes:
                    raise ValueError('..')
                self.mapp_section_nodes[section_id]=(from_node_id,
                                                     to_node_id)
                
def set_nominal_voltages_recur(m, mega_source, edge_equipment, edge_equipment_name, digraph, *args):
    if not args:
        node = mega_source
        voltage = 10**6
        previous = mega_source
    else:
        node, voltage, previous = args
    if (previous, node) in edge_equipment and edge_equipment[(previous, node)] == 'PowerTransformer':
        trans_name = edge_equipment_name[(previous, node)]
        new_value = min([w.nominal_voltage for w in m[trans_name].windings if w.nominal_voltage is not None])
    elif (node, previous) in edge_equipment and edge_equipment[(node, previous)] == 'PowerTransformer':
        trans_name = edge_equipment_name[(node, previous)]
        new_value = min([w.nominal_voltage for w in m[trans_name].windings if w.nominal_voltage is not None])
    else:
        new_value = voltage
    if hasattr(m[node], 'nominal_voltage'):
        m[node].nominal_voltage = new_value
    for child in digraph.successors(node):
        set_nominal_voltages_recur(m, mega_source, edge_equipment, edge_equipment_name, digraph, child, new_value, node)
    return m

def set_nominal_voltages_recur_line(m):
    for obj in m.models:
        #If we get a line
        if isinstance(obj, Line) and obj.nominal_voltage is None:
            #Get the from node
            if hasattr(obj, 'from_element') and obj.from_element is not None:
                node_from_object = m[obj.from_element]

                #If the from node has a known nominal voltage, then use this value
                if hasattr(node_from_object, 'nominal_voltage') and node_from_object.nominal_voltage is not None:
                    obj.nominal_voltage = node_from_object.nominal_voltage
    return m
              
def bfs_order(graph, source='sourcebus'):
    start_node = graph[source]
    return (set(nx.bfs_edges(graph, source)))



if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Compute_Metrics_From_Duke.main()

    
