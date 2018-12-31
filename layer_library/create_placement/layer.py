from __future__ import print_function, division, absolute_import

import os
import math
from builtins import super
from pydoc import locate
import logging
from uuid import UUID
import numpy as np
import networkx as nx

import random
import json_tricks
from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.network.network import Network
from ditto.models.line import Line

logger = logging.getLogger('layerstack.layers.Create_Placement')


class Create_Placement(DiTToLayerBase):
    name = "create_placement"
    uuid = UUID("a9440343-3a0b-4922-9d05-81af35b228da")
    version = 'v0.1.0'
    desc = "Layer for selecting a placement set from a DiTTO model and writing to a json file"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('feeders', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('equipment_type', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('selection', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('seed', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('placement_folder', description='', parser=None, choices=None, nargs=None))
        return arg_list


    @classmethod
    def apply(cls, stack, model, feeders = 100, equipment_type=None, selection = ('Random',15), seed = 0, placement_folder=''):
        subset = []
        if selection is None:
            return model
        
        # TODO: Apply placements to feeders selectively. Currently applying to all equipment in the distribution system

        # Currently just including random selections. Need to also include and document other selection options
        if selection[0] == 'Reclosers':
            # Get a subset of nodes at the end of Reclosers. This algorithm finds to closest goabs to the feeder head (in topological order)
            # without common ancestry. i.e. no goab should be upstream of another goab. If this is not possible,
            # the number of reclosers is decreased


            # Percentage of feeders that each Reclosers number is used for e.g. if selection[1] = 4 and feeders = [50,40,30,20], 50% of feedes have 1st goab, 40% of feeders have second etc.
            feeders_str = str(feeders)
            if isinstance(feeders,list):
                feeders_str = ''
                for f in feeders:
                    feeders_str = feeders_str+str(f)+'-'
                feeders_str = feeders_str.strip('-')
    
            file_name = str(feeders_str)+'_Node_'+selection[0]+'-'+str(selection[1])+'-'+str(selection[2])+'.json'
            all_goabs = {}
            random.seed(seed)

            tmp_network = Network()
            tmp_network.build(model,'st_mat')
            tmp_network.set_attributes(model)
            tmp_network.remove_open_switches(model)
            tmp_network.rebuild_digraph(model,'st_mat')
            sorted_elements =  []
            for element in nx.topological_sort(tmp_network.digraph):
                sorted_elements.append(element)
            for i in model.models:
                if isinstance(i,Line) and i.is_recloser is not None and i.is_recloser: 
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
    
            goab_key_list = list(all_goabs.keys())
            random.seed(seed)
            random.shuffle(goab_key_list)
            goab_counter = 0
            for key in goab_key_list:
                goab_counter+=1
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
                    goab1 = feeder_goab_ends[i]
                    for j in range(i+1,len(feeder_goabs)):
                        goab2 = feeder_goab_ends[j]
                        if goab1 == goab2:
                            continue
                        connected = nx.has_path(tmp_network.digraph,goab1,goab2)
                        connectivity_matrix[i][j] = connected
                        if connected:
                            connectivity_matrix[j][i] = connected

    
                selected_goabs = []
                num_goabs = selection[2]
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

                for i in range(min(len(selected_goabs),selection[1])):
                    if goab_counter/float(len(goab_key_list))*100 < feeders[i]:
                        subset.append(model[selected_goabs[i]].to_element)


        if selection[0] == 'Random':
            class_equipment_type = locate(equipment_type)
            all_equipment = []
            for i in model.models:
                if isinstance(i,class_equipment_type):
                    all_equipment.append(i.name)

            if len(selection) == 3:
                random.seed(seed)
                random.shuffle(all_equipment)
                start_pos = math.floor(len(all_equipment)*float(selection[1])/100.0)
                end_pos = math.floor(len(all_equipment)*float(selection[2])/100.0)
                subset = all_equipment[start_pos:end_pos]
                file_name = str(feeders)+'_'+equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'-'+str(selection[2])+'_'+str(seed)+'.json'
            if len(selection)==2:
                random.seed(seed)
                subset = random.sample(all_equipment,math.floor(len(all_equipment)*float(selection[1])/100.0))
                file_name = str(feeders)+'_'+equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'_'+str(seed)+'.json'



        if not os.path.exists(placement_folder):
            os.makedirs(placement_folder)

        with open(os.path.join(placement_folder,file_name), "w") as f:
            f.write(
                json_tricks.dumps(subset, sort_keys=True, indent=4)
            )


        
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    Create_Placement.main()

    
