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
from ditto.models.line import Line
from ditto.models.load import Load

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
        arg_list.append(Arg('customer_file', description='', parser=None, choices=None, nargs=None))
        return arg_list



    @classmethod
    def apply(cls, stack, model, feeders = [100], equipment_type=None, selection_list = [('Random',0,15)], seed = 0, placement_folder='',placement_names=['default'],customer_file = None):
        if selection_list is None:
            return model

        print(placement_names)
        class_equipment_type = locate(equipment_type)
        all_equipment = []
        
        # TODO: Apply placements to feeders selectively. Currently applying to all equipment in the distribution system

        cust_types = {}
        if customer_file is not None:
            for row in open(customer_file,'r').readlines():
                sp_row = row.split(';')
                cust_type = sp_row[-3]
                name = sp_row[3].lower()
                cust_types[name] = cust_type
                

        sub_category = None
        if class_equipment_type == 'ditto.models.line.Line':
            class_equipment_type = 'ditto.models.line.Line'
            sub_category = 'line'
        elif class_equipment_type == 'ditto.models.line.Switch':
            class_equipment_type = 'ditto.models.line.Line'
            sub_category = 'switch'
        elif class_equipment_type == 'ditto.models.line.Breaker':
            class_equipment_type = 'ditto.models.line.Line'
            sub_category = 'breaker'
        elif class_equipment_type == 'ditto.models.line.Recloser':
            class_equipment_type = 'ditto.models.line.Line'
            sub_category = 'recloser'
        elif class_equipment_type == 'ditto.models.line.Fuse':
            class_equipment_type = 'ditto.models.line.Line'
            sub_category = 'fuse'

        for i in model.models:
            if isinstance(i,class_equipment_type):
                if sub_category == 'line':
                    if i.is_switch or (i.wires is not None and len(i.wires)>0 and i.wires[0].is_switch):
                        continue
                    if i.is_fuse or (i.wires is not None and len(i.wires)>0 and i.wires[0].is_fuse):
                        continue
                    if i.is_breaker or (i.wires is not None and len(i.wires)>0 and i.wires[0].is_breaker):
                        continue
                    if i.is_recloser or (i.wires is not None and len(i.wires)>0 and i.wires[0].is_recloser):
                        continue
                if customer_file is not None:
                    if selection_list[0][0] == 'Random_res':
                        base_name = i.name.lower().replace('load_','')
                        if base_name in cust_types and cust_types[base_name] == 'Res':
                            all_equipment.append(i.name)

                    if selection_list[0][0] == 'Random_com':
                        base_name = i.name.lower().replace('load_','')
                        if base_name in cust_types and cust_types[base_name] != 'Res':
                            all_equipment.append(i.name)
                else:
                    all_equipment.append(i.name)

        if not os.path.exists(placement_folder):
            os.makedirs(placement_folder)
        # Currently just including random selections. Need to also include and document other selection options
        random.seed(seed)
        all_equipment = sorted(all_equipment)
        random.shuffle(all_equipment) #all_equipment now in random order
        cnt = 0
        subset = {}
        for selection in selection_list:
            all_feeders = {}
            for i in all_equipment:
                i_model = model[i]
                i_name = i
                if isinstance(i_model,Line):
                    i_name = (i_model.from_element, i_model.to_element)
                if i_model.feeder_name != '' and i_model.feeder_name !='subtransmission': #i.e. we allow for sub-transmission lines to go down
                    if not i_model.feeder_name in all_feeders:
                        all_feeders[i_model.feeder_name] = [i_name]
                    else:
                        all_feeders[i_model.feeder_name].append(i_name)

            if 'Random' in selection[0]:
                if len(selection)==2:
                    random.seed(seed)
                    for feeder in all_feeders:
                        if not feeder in subset:
                            subset[feeder] = []
                        subset[feeder].extend(all_feeders[feeder][0:math.floor(len(all_feeders[feeder])*float(selection[1])/100.0)])
    
                if len(selection) == 3:
                    for feeder in all_feeders:
                        start_pos = math.floor(len(all_feeders[feeder])*float(selection[1])/100.0)
                        end_pos = math.floor(len(all_feeders[feeder])*float(selection[2])/100.0)
                        if not feeder in subset:
                            subset[feeder] = []
                        subset[feeder].extend(all_feeders[feeder][start_pos:end_pos])

            if selection[0] == 'Count':

                for feeder in all_feeders:
                    tmp_list = []
                    for i in range(min(len(all_feeders[feeder]),int(selection[1]))):
                        tmp_list.append(all_feeders[feeder][i])
                    if not feeder in subset:
                        subset[feeder] = []
                    subset[feeder].extend(tmp_list)

            if selection[0] == 'Sized_Loads': #Assuming that equipment type is load 
                for feeder in all_feeders:
                    sized_equipment = []
                    for i in all_feeders[feeder]:
                        i_model = model[i]
                        total_load = 0
                        if isinstance(i_model,Load) and i_model.phase_loads is not None:
                            for pl in i_model.phase_loads:
                                total_load+=pl.p
                        if total_load/1000 >= float(selection[1]):
                            sized_equipment.append(i)
                    if len(selection)==3: #(Sized_Loads,200,50) is 50% of all loads at least 200kW
                        if not feeder in subset:
                            subset[feeder] = []
                        subset[feeder].extend(random.sample(sized_equipment,math.floor(len(sized_equipment)*float(selection[2])/100.0)))
                    if len(selection)==4: #(Sized_Loads,200,20,50) is range of 20-50% of all loads at least 200kW
                        if not feeder in subset:
                            subset[feeder] = []
                        start_pos = math.floor(len(sized_equipment)*float(selection[2])/100.0)
                        end_pos = math.floor(len(sized_equipment)*float(selection[3])/100.0)
                        subset[feeder].extend(sized_equipment[start_pos:end_pos])





            #file_name = str(feeders[cnt])+'_'+equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'-'+str(selection[2])+'_'+str(seed)+'.json'
        file_name = placement_names
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

    
