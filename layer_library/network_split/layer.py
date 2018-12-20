from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import numpy as np
import networkx as nx

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

from ditto.models.line import Line
from ditto.metrics.network_analysis import NetworkAnalyzer
from ditto.modify.system_structure import system_structure_modifier
from ditto.models.power_source import PowerSource
from ditto.network.network import Network

logger = logging.getLogger('layerstack.layers.Network_Split')


class Network_Split(DiTToLayerBase):
    name = "network_split"
    uuid = UUID("5e2849d9-7f25-499b-a5f7-b1f85e97dde9")
    version = '0.1.0'
    desc = "Use information from feeder.txt to split the network into different feeders"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['path_to_feeder_file'] = Kwarg(default=None, description='Path to feeder.txt',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['path_to_no_feeder_file'] = Kwarg(default=None, description='Path to nofeeder.txt',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['compute_metrics'] = Kwarg(default=False, description='Triggers the metrics computation if set to True',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['excel_output'] = Kwarg(default=None, description='path to the output file for xlsx export',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['json_output'] = Kwarg(default=None, description='path to the output file for json export',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['compute_kva_density_with_transformers'] = Kwarg(default=None, description='Flag to use transformers or loads to compute the kva density metric',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        if 'path_to_feeder_file' in kwargs:
            path_to_feeder_file = kwargs['path_to_feeder_file']

        path_to_no_feeder_file = None
        if 'path_to_no_feeder_file' in kwargs:
            path_to_no_feeder_file = kwargs['path_to_no_feeder_file']

        if 'compute_metrics' in kwargs:
            compute_metrics = kwargs['compute_metrics']
        else:
            compute_metrics = False

        if 'compute_kva_density_with_transformers' in kwargs:
            compute_kva_density_with_transformers = kwargs['compute_kva_density_with_transformers']
        else:
            compute_kva_density_with_transformers = True

        if compute_metrics:
            if 'excel_output' in kwargs:
                excel_output = kwargs['excel_output']
            else:
                raise ValueError('Missing output file name for excel')

            if 'json_output' in kwargs:
                json_output = kwargs['json_output']
            else:
                raise ValueError('Missing output file name for json')       

        #Open and read feeder.txt
        with open(path_to_feeder_file, 'r') as f:
            lines = f.readlines()
    
        #Parse feeder.txt to have the feeder structure of the network
        feeders = {}
        substations = {}
        substation_transformers = {}

        for line in lines[1:]:
    
            #Parse the line
            node,sub,feed,sub_trans = map(lambda x:x.strip().lower(), line.split(' '))
    
            #If feeder is new, then add it to the feeders dict
            if feed not in feeders:
        
                #Initialize with a list holding the node
                feeders[feed] = [node.lower().replace('.','')]
		
            #Othewise, just append the node
            else:
                feeders[feed].append(node.lower().replace('.',''))
        
            #Same thing for the substation
            if feed not in substations:
                substations[feed] = sub.lower().replace('.','')
        
            #Same thing for substation_transformers
            if feed not in substation_transformers:
                substation_transformers[feed] = sub.lower().replace('.','')

        if path_to_no_feeder_file is not None:
            with open(path_to_no_feeder_file, 'r') as f:
                lines = f.readlines()
            for line in lines[1:]:
                node,feed = map(lambda x:x.strip().lower(), line.split(' '))
                if feed != 'mv-mesh':
                    if 'subtransmission' not in feeders:
                        feeders['subtransmission'] = [node.lower().replace('.','')]
                    else:
                        feeders['subtransmission'].append(node.lower().replace('.',''))
                    if 'subtransmission' not in substations:
                        substations['subtransmission'] = ''
            

        #Create a network analyzer object
        network_analyst = NetworkAnalyzer(model)

        #Add the feeder information to the network analyzer
        network_analyst.add_feeder_information(list(feeders.keys()),
        	                                   list(feeders.values()),
                    	                       substations,
                            	               '') #TODO find a way to get the feeder type

        #Split the network into feeders
        network_analyst.split_network_into_feeders()

        #Tag the objects
        network_analyst.tag_objects()

        #Set the names
        network_analyst.model.set_names()



        # Set reclosers. This algorithm finds to closest 1/3 of goabs to the feeder head (in topological order)
        # without common ancestry. i.e. no recloser should be upstream of another recloser. If this is not possible,
        # the number of reclosers is decreased

        recloser_proportion = 0.33
        all_goabs = {}
        np.random.seed(0)
        tmp_network = Network()
        tmp_network.build(network_analyst.model,'st_mat')
        tmp_network.set_attributes(network_analyst.model)
        tmp_network.remove_open_switches(network_analyst.model)
        tmp_network.rebuild_digraph(network_analyst.model,'st_mat')
        sorted_elements =  []
        for element in nx.topological_sort(tmp_network.digraph):
            sorted_elements.append(element)
        for i in network_analyst.model.models:
            if isinstance(i,Line) and i.is_switch is not None and i.is_switch and i.name is not None and 'goab' in i.name.lower(): 
                is_open = False
                for wire in i.wires:
                    if wire.is_open:
                        is_open = True
                if is_open:
                    continue
                if hasattr(i,'feeder_name') and i.feeder_name is not None and i.feeder_name != 'subtransmission':
                    if i.feeder_name in all_goabs:
                        all_goabs[i.feeder_name].append(i.name)
                    else:
                        all_goabs[i.feeder_name] = [i.name]

        for key in list(all_goabs.keys()):
            feeder_goabs_dic = {} # Topological sorting done by node. This matches goabs to their end-node
            for goab in all_goabs[key]:
                feeder_goabs_dic[model[goab].to_element] = goab # shouldn't have multiple switches ending at the same node
            feeder_goabs = []
            feeder_goab_ends= []
            for element in sorted_elements:
                if element in feeder_goabs_dic:
                    feeder_goabs.append(feeder_goabs_dic[element])
                    feeder_goab_ends.append(element)
            connectivity_matrix = [[False for i in range(len(feeder_goabs))] for j in range(len(feeder_goabs))]
            for i in range(len(feeder_goabs)):
                recloser1 = feeder_goab_ends[i]
                for j in range(i+1,len(feeder_goabs)):
                    recloser2 = feeder_goab_ends[j]
                    if recloser2 == recloser1:
                        continue
                    connected = nx.has_path(tmp_network.digraph,recloser1,recloser2)
                    connectivity_matrix[i][j] = connected
                    if connected:
                        connectivity_matrix[j][i] = connected


            selected_goabs = []
            num_goabs = int(len(feeder_goabs)*float(recloser_proportion))
            finished = False
            if num_goabs == 0:
                finished = True
            while not finished:
                for i in range(len(feeder_goabs)):
                    current_set = set([i])
                    for j in range(i+1,len(feeder_goabs)):
                        skip_this_one = False
                        for k in current_set:
                            if connectivity_matrix[j][k]: #i.e. see if the candidate node has common anything upstream or downstream
                                skip_this_one = True
                                break
                        if skip_this_one:
                            continue
                        current_set.add(j)
                        if len(current_set) == num_goabs:
                            break
                    if len(current_set) == num_goabs:
                        finished = True
                        for k in current_set:
                            selected_goabs.append(feeder_goabs[k])
                        break
                if not finished:
                    num_goabs -=1


            #selected_goabs = np.random.choice(feeder_goabs,int(len(feeder_goabs)*float(recloser_proportion)))

            for recloser in selected_goabs:
                network_analyst.model[recloser].is_switch = False
                network_analyst.model[recloser].is_recloser = True
                if network_analyst.model[recloser].wires is not None:
                    for wire in network_analyst.model[recloser].wires:
                        wire.is_switch = False
                        wire.is_recloser = True
                network_analyst.model[recloser].name = network_analyst.model[recloser].name.replace('goab','recloser')
                network_analyst.model[recloser].nameclass= 'recloser'
        network_analyst.model.set_names()



        #Compute the metrics if needed
        if compute_metrics:

            #Compute metrics
            network_analyst.compute_all_metrics_per_feeder(compute_kva_density_with_transformers=compute_kva_density_with_transformers)

            #Export metrics to Excel
            network_analyst.export(excel_output)

            #Export metrics to JSON
            network_analyst.export_json(json_output)


        #Return the model
        return network_analyst.model

if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Network_Split.main()

    
