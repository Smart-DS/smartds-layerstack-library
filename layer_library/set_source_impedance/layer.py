from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.power_source import PowerSource

logger = logging.getLogger('layerstack.layers.Set_Source_Impedance')


class Set_Source_Impedance(DiTToLayerBase):
    name = "set_source_impedance"
    uuid = UUID("2448c5c6-6f1a-48f7-afc3-1558ed5898f5")
    version = '0.1.0'
    desc = "Set the source impedance and p.u. value for opendss"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['x1'] = Kwarg(default=None, description='x1 value to set',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['x0'] = Kwarg(default=None, description='x0 value to set',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['r1'] = Kwarg(default=None, description='r1 value to set',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['r0'] = Kwarg(default=None, description='r0 value to set',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['pu'] = Kwarg(default=None, description='pu value to set',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        x1 = None
        x0 = None
        r1 = None
        r0 = None
        pu = None
        if 'x1' in kwargs:
            x1 = kwargs['x1']
        if 'x0' in kwargs:
            x0 = kwargs['x0']
        if 'r1' in kwargs:
            r1 = kwargs['r1']
        if 'r0' in kwargs:
            r0 = kwargs['r0']
        if 'pu' in kwargs:
            pu = kwargs['pu']

        for i in model.models:
            if isinstance(i,PowerSource):
                if x1 is not None and r1 is not None:
                    i.positive_sequence_impedance = complex(r1,x1)
                if x0 is not None and r0 is not None:
                    i.zero_sequence_impedance = complex(r1,x1)
                if pu is not None:
                    i.per_unit = pu

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Zero_Source_Impedance.main()

    
