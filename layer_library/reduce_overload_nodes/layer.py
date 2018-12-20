from __future__ import print_function, division, absolute_import

import os
from builtins import super
import logging
from uuid import UUID
import pandas as pd

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.load import Load
from ditto.models.phase_load import PhaseLoad

logger = logging.getLogger('layerstack.layers.Reduce_Overload_Nodes')


class Reduce_Overload_Nodes(DiTToLayerBase):
    name = "reduce_overload_nodes"
    uuid = UUID("26280b75-3643-48e2-bb23-6ba1fc12c4f2")
    version = '0.1.0'
    desc = "Reduce the peak load of nodes which are overloaded"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['powerflow_file'] = Kwarg(default=None, description='list of powerflow values for each node in the network',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['threshold'] = Kwarg(default=None, description='threshold below which the load value needs to be reduced',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['scale_factor'] = Kwarg(default=None, description='Amount to divide the load by when reducing',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        threshold =0.94
        powerflow_file = None
        scale_factor = 2.0
        if 'scale_factor' in kwargs:
            scale_factor = float(kwargs['scale_factor'])
        if 'threshold' in kwargs:
            threshold = float(kwargs['threshold'])
        if 'powerflow_file' in kwargs:
            powerflow_file = kwargs['powerflow_file']

        if not os.path.exists(powerflow_file):
            return model
        lines = pd.read_csv(powerflow_file)
        for index,row in lines.iterrows():
            name = row['Node'].lower()
            value = float(row['P.U. Voltage'])
            if value < threshold:
                print(name)
                if 'load_'+name in model.model_names:
                    obj = model['load_'+name]
                    print(obj.name+' reduced')
                    if isinstance(obj,Load) and obj.phase_loads is not None and len(obj.phase_loads)>0:
                        for pl in obj.phase_loads:
                            if hasattr(pl,'p') and pl.p is not None:
                                pl.p = pl.p/scale_factor
                            if hasattr(pl,'q') and pl.q is not None:
                                pl.q = pl.q/scale_factor





        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Reduce_Overload_Nodes.main()

    
