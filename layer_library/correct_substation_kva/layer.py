from __future__ import print_function, division, absolute_import

import os
from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.powertransformer import PowerTransformer

logger = logging.getLogger('layerstack.layers.Correct_Substation_Kva')


class Correct_Substation_Kva(DiTToLayerBase):
    name = "correct_substation_kva"
    uuid = UUID("127d6f96-f440-4721-920f-d2625be5623c")
    version = '0.1.0'
    desc = "Fix and error that means that substation transformer sizes dont match RNM"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['base_rnm_folder'] = Kwarg(default=None, description='Location where to get the correct RNM transformer sizing',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        base_rnm_folder = kwargs.get('base_rnm_folder',None) #assume this is the something like /projects/smartds/SMARTDS/dataset_4_20201120/P1U
        transformer_file = os.path.join(base_rnm_folder,'OpenDSS','Transformers.dss')
        all_substation_transformers = [i for i in model.models if isinstance(i,PowerTransformer) and i.is_substation]
        substation_names = set()
        substation_totals = {}
        substation_breakdowns = {}
        count = 0
        rnm_xfmr_map={}
        for xfmr in all_substation_transformers:
            if xfmr.name.startswith('sb'):
                sub = xfmr.name.split('_')[1] #Assume naming convention from when substations were attached
                rated_power_kva = xfmr.windings[0].rated_power/1000 
                low_voltage = xfmr.windings[1].nominal_voltage/1000
                substation_names.add(sub)
                if not sub in substation_totals:
                    substation_totals[sub] = 0
                substation_totals[sub]+= rated_power_kva
                substation_breakdowns[count] = (rated_power_kva,sub,low_voltage) #index by position in array. Save rated power and name
            count+=1
        with open(transformer_file,'r') as input_file:
            for row in input_file.readlines():
                split_row = row.split()
                kva = None
                bus_name = None
                is_sub = False
                for token in split_row:
                    if token.startswith('bus='):
                        bus_name = token.split('=')[1].split('-')[0].split('_')[0] #Doesn't fail if no - character
                        bus_name = bus_name.lower()
                        if bus_name in substation_names:
                            is_sub=True
                        else:
                            break
                    if token.startswith('kva='):
                        kva = token.split('=')[1]
                if is_sub:
                    rnm_xfmr_map[bus_name] = float(kva)

        for count in substation_breakdowns:
            kva,sub,low_voltage = substation_breakdowns[count]
            ratio = kva/substation_totals[sub]
            new_value = ratio*rnm_xfmr_map[sub]
            new_value = min(new_value,40000)
            # Hardcode resistance values in
            resistance = 0
            if new_value<=10000:
                resistance = 0.4808326112068523
            elif new_value < 30000:
                resistance = 0.370153834758116
            elif low_voltage > 20:
                resistance = 0.39801487608399566
            else:
                resistance = 0.33831264
            for winding_count in range(len(all_substation_transformers[count].windings)):
                all_substation_transformers[count].windings[winding_count].rated_power = new_value*1000
                all_substation_transformers[count].windings[winding_count].resistance = resistance
        


        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Correct_Substation_Kva.main()

    
