from __future__ import print_function, division, absolute_import

from builtins import super
import os
import math
import pandas as pd
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.load import Load

logger = logging.getLogger('layerstack.layers.Reduce_Lv_Loads')


class Reduce_Lv_Loads(DiTToLayerBase):
    name = "reduce_lv_loads"
    uuid = UUID("ce5b4b6d-4dc1-4364-9cce-08840cd6aca8")
    version = '0.1.0'
    desc = "Half the loads on select nodes which are overloaded"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['input_file'] = Kwarg(default=None, description='location of input file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['scale_factor'] = Kwarg(default=None, description='amount to divide the kw load by',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        scale_factor = 2.0
        input_file = None
        if 'scale_factor' in kwargs:
            scale_factor = float(kwargs['scale_factor'])
        if 'input_file' in kwargs:
            input_file = kwargs['input_file']

        if os.path.exists(input_file):
            lv_list = pd.read_csv(input_file)
            all_loads = set()
            for k,v in lv_list.iterrows():
                print(v)
                all_loads.add(v['name'].lower())
            for i in model.models:
                if isinstance(i,Load) and i.connecting_element is not None and i.connecting_element in all_loads and i.phase_loads is not None:
                    for pl in i.phase_loads:
                        if pl.p is not None:
                            pf = math.sqrt(pl.p**2/(pl.p**2+pl.q**2))
                            pl.p = pl.p /scale_factor
                            pl.q = math.sqrt((pl.p/pf)**2 - pl.p**2)
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Reduce_Lv_Loads.main()

    
