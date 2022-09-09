from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.modify.system_structure import system_structure_modifier

logger = logging.getLogger('layerstack.layers.Find_Missing_Coords')


class Find_Missing_Coords(DiTToLayerBase):
    name = "find_missing_coords"
    uuid = UUID("a7605902-8508-4e73-b4e9-b4e42c4ac6a5")
    version = '0.1.0'
    desc = "Layer to compute the values of the missing coordinates in DiTTo"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):

        all_substations = ['st_mat'] # when running for all regions
        # Added for Texas case where we don't use subtransmission
        all_substations = []
        for i in model.models:
            if hasattr(i,'is_substation_connection') and i.is_substation_connection:
                if i.nominal_voltage > 30000: #69 kv or 138 kv
                    all_substations.append(i.name)

        for substation in all_substations:
            #Create the modifier object
            modifier=system_structure_modifier(model,substation)
            
            # Set missing coordinates
            modifier.set_missing_coords_recur()

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Find_Missing_Coords.main()

    
