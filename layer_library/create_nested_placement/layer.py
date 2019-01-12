from __future__ import print_function, division, absolute_import

import os
import math
from builtins import super
from pydoc import locate
import random
import json_tricks

import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.Create_Nested_Placement')


class Create_Nested_Placement(DiTToLayerBase):
    name = "create_nested_placement"
    uuid = UUID("16a23fa2-dfc8-40f7-a3be-70d3d9856c6f")
    version = '0.1.0'
    desc = "Create placements that fit inside each other"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('feeders', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('equipment_type', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('selection_list', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('seed', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('placement_folder', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('placement_names', description='', parser=None, choices=None, nargs=None))
        return arg_list



    @classmethod
    def apply(cls, stack, model, feeders = [100], equipment_type=None, selection_list = [('Random',0,15)], seed = 0, placement_folder='',placement_names=['default']):
        if selection_list is None:
            return model

        class_equipment_type = locate(equipment_type)
        all_equipment = []
        
        # TODO: Apply placements to feeders selectively. Currently applying to all equipment in the distribution system

        for i in model.models:
            if isinstance(i,class_equipment_type):
                all_equipment.append(i.name)

        if not os.path.exists(placement_folder):
            os.makedirs(placement_folder)
        # Currently just including random selections. Need to also include and document other selection options
        random.seed(seed)
        random.shuffle(all_equipment) #all_equipment now in random order
        cnt = 0
        for selection in selection_list:
            subset = []
            if selection[0]=='Random':
                if len(selection)==2:
                    random.seed(seed)
                    subset = random.sample(all_equipment,math.floor(len(all_equipment)*float(selection[1])/100.0))
    
                if len(selection) == 3:
                    start_pos = math.floor(len(all_equipment)*float(selection[1])/100.0)
                    end_pos = math.floor(len(all_equipment)*float(selection[2])/100.0)
                    subset = all_equipment[start_pos:end_pos]
            if selection[0] == 'Sized_Loads': #Assuming that equipment type is load 
                sized_equipment = []
                for i in all_equipment:
                    i_model = model[i]
                    total_load = 0
                    if isinstance(i_model,Load) and i.phase_loads is not None:
                        for pl in i.phase_loads:
                            total_load+=pl.p
                    if pl/1000 >= float(selection[1]):
                        sized_equipment.append(i)
                if len(selection)==3: #(Sized_Loads,200,50) is 50% of all loads at least 200kW
                    subset = random.sample(sized_equipment,math.floor(len(sized_equipment)*float(selection[2])/100.0)),
                if len(selection)==4: #(Sized_Loads,200,20,50) is range of 20-50% of all loads at least 200kW
                    start_pos = math.floor(len(sized_equipment)*float(selection[2])/100.0)
                    end_pos = math.floor(len(sized_equipment)*float(selection[3])/100.0)
                    subset = sized_equipment[start_pos:end_pos]





            #file_name = str(feeders[cnt])+'_'+equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'-'+str(selection[2])+'_'+str(seed)+'.json'
            file_name = placement_names[cnt]
            with open(os.path.join(placement_folder,file_name), "w") as f:
                f.write(
                    json_tricks.dumps(subset, sort_keys=True, indent=4)
                )
            cnt+=1



        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Create_Nested_Placement.main()

    
