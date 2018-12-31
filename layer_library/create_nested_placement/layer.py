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
        return arg_list



    @classmethod
    def apply(cls, stack, model, feeders = [100], equipment_type=None, selection_list = [('Random',0,15)], seed = 0, placement_folder=''):
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
            if len(selection)==2:
                if selection[0]=='Random':
                    random.seed(seed)
                    subset = random.sample(all_equipment,math.floor(len(all_equipment)*float(selection[1])/100.0))
    
            if len(selection) == 3:
                if selection[0] == 'Random':
                    start_pos = math.floor(len(all_equipment)*float(selection[1])/100.0)
                    end_pos = math.floor(len(all_equipment)*float(selection[2])/100.0)
                    subset = all_equipment[start_pos:end_pos]


            file_name = str(feeders[cnt])+'_'+equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'-'+str(selection[2])+'_'+str(seed)+'.json'
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

    
