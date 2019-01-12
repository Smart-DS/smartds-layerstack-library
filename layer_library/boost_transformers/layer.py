from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import pandas as pd
import os

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.powertransformer import PowerTransformer
from ditto.models.winding import Winding

logger = logging.getLogger('layerstack.layers.Boost_Transformers')


class Boost_Transformers(DiTToLayerBase):
    name = "boost_transformers"
    uuid = UUID("447dbd65-5181-4c11-a8e9-8fe7b0676ce1")
    version = '0.1.0'
    desc = "Change transformer sizes and resistances/reactances from file specified"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('arg_name', description='', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['resistance'] = Kwarg(default=None, description='resistance for EACH separate winding of the transformer',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['reactance'] = Kwarg(default=None, description='reactance for transformer',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['mva'] = Kwarg(default=None, description='Mvar to set for the transformer',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['input_file'] = Kwarg(default=None, description='Location of input file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        resistance = None
        reactance = None
        mva = None
        input_file = None
        if 'transformer_from' in kwargs:
            transformer_from = kwargs['transformer_from']
        if 'transformer_to' in kwargs:
            transformer_to = kwargs['transformer_to']
        if 'resistance' in kwargs:
            resistance = kwargs['resistance']
        if 'reactance' in kwargs:
            reactance = kwargs['reactance']
        if 'mva' in kwargs:
            mva = kwargs['mva']
        if 'input_file' in kwargs:
            input_file = kwargs['input_file']

        if os.path.exists(input_file):
            transfomers_list = pd.read_csv(input_file)
            all_transformers = set()
            for k,v in transfomers_list.iterrows():
                print(v)
                all_transformers.add((v['from'].lower(),v['to'].lower()))
            for i in model.models:
                if isinstance(i,PowerTransformer):
                    if (i.from_element,i.to_element) in all_transformers: # These should only have two windings since they're at substations
                        i.windings[0].rated_power = mva*1000*1000 #stored in var
                        i.windings[1].rated_power = mva*1000*1000 #stored in var
                        i.windings[0].resistance = resistance #stored in var
                        i.windings[1].resistance = resistance #stored in var
                        i.reactances = [reactance]



        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Boost_Transformers.main()

    
