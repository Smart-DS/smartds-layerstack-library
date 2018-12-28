from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import os
import pandas as pd

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.powertransformer import PowerTransformer
from ditto.models.load import Load

logger = logging.getLogger('layerstack.layers.Set_Delta_Systems')


class Set_Delta_Systems(DiTToLayerBase):
    name = "set_delta_systems"
    uuid = UUID("b98f5143-6cd1-4ea9-ab1b-890fefea60c0")
    version = '0.1.0'
    desc = "Set loads and transformers to be delta for delta systems"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['readme_location'] = Kwarg(default=None, description='Location of readme file (if it exists) describing the type of system i.e. delta or wye',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        readme_location = None
        if 'readme_location' in kwargs:
            readme_location = kwargs['readme_location']

        if readme_location is not None and os.path.exists(readme_location):
            f = open(readme_location,'r')
            info = f.readline().split()
            suffix = info[1][:-2]
            config = info[5]
            if config == 'delta-delta':
                for i in model.models:
                    if isinstance(i,Load):
                        if not i.is_center_tap:
                            i.connection_type = 'D'

                    if isinstance(i,PowerTransformer) and i.windings is not None and len(i.windings)>1:
                        winding1 = i.windings[0]
                        winding2 = i.windings[1]
                        if hasattr(winding1,'phase_windings') and winding1.phase_windings is not None:
                            n_phases = len(winding1.phase_windings)
                            if n_phases ==3:
                                winding1.connection_type = 'D'
                                winding2.connection_type = 'D'
                            else:
                                winding1.connection_type = 'D'
                                winding2.connection_type = 'Y'



        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Delta_Systems.main()

    
