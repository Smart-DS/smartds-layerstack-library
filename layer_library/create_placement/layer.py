from __future__ import print_function, division, absolute_import

import os
import math
from builtins import super
from pydoc import locate
import logging
from uuid import UUID

import random
import json
from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

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
        arg_list.append(Arg('file_name', description='', parser=None, choices=None, nargs=None))
        return arg_list


    @classmethod
    def apply(cls, stack, model, feeders = 'all', equipment_type=None, selection = ('Random',15), seed = 0, placement_folder='', file_name=''):
        class_equipment_type = locate(equipment_type)
        all_equipment = []
        subset = []
        selection_name = ''
        
        # TODO: Apply placements to feeders selectively. Currently applying to all equipment in the distribution system

        for i in model.models:
            if isinstance(i,class_equipment_type):
                all_equipment.append(i.name)

        # Currently just including random selections. Need to also include and document other selection options
        if len(selection)==2:
            if selection[0]=='Random':
                random.seed(seed)
                subset = random.sample(all_equipment,math.floor(len(all_equipment)*float(selection[1])/100.0))


        with open(os.path.join(placement_folder,file_name),'w') as outfile:
            json.dump(subset, outfile)


        
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    Create_Placement.main()

    
