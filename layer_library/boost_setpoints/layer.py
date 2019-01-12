from __future__ import print_function, division, absolute_import

import os
import pandas as pd
from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.regulator import Regulator

logger = logging.getLogger('layerstack.layers.Boost_Setpoints')


class Boost_Setpoints(DiTToLayerBase):
    name = "boost_setpoints"
    uuid = UUID("ec0f5b2b-5e3f-4a70-9df0-8acb878c5d04")
    version = '0.1.0'
    desc = "Increase LTC setpoints for select regions"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['setpoint'] = Kwarg(default=None, description='p.u. setpoint for ltc',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['input_file'] = Kwarg(default=None, description='location of input file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        setpoint = None
        input_file = None
        if 'setpoint' in kwargs:
            setpoint = kwargs['setpoint']
        if 'input_file' in kwargs:
            input_file = kwargs['input_file']

        if os.path.exists(input_file):
            ltc_list = pd.read_csv(input_file)
            all_regs = set()
            for k,v in ltc_list.iterrows():
                print(v)
                all_regs.add((v['from'].lower(),v['to'].lower()))
            for i in model.models:
                if isinstance(i,Regulator) and hasattr(i,'ltc') and i.ltc is not None and i.ltc:
                    if (i.from_element,i.to_element) in all_regs: # These should only have two windings since they're at substations
                        i.setpoint = float(setpoint)
                        print(i.setpoint)


        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Boost_Setpoints.main()

    
