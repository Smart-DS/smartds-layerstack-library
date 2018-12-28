from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.power_source import PowerSource

logger = logging.getLogger('layerstack.layers.Set_Source_Voltage')


class Set_Source_Voltage(DiTToLayerBase):
    name = "set_source_voltage"
    uuid = UUID("e699f1f9-e227-4438-a354-bf81e276f399")
    version = '0.1.0'
    desc = "Set Source voltage value"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['source_kv'] = Kwarg(default=None, description='kv value for any PowerSource objects',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['source_names'] = Kwarg(default=None, description='Names of element to additionally set. Expecting a list',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        source_names = None
        source_names_set = set()
        source_kv = None
        if 'source_name' in kwargs:
            source_names = kwargs['source_name']
        if source_names is not None:
            for i in source_names:
                source_names_set.add(i)
        if 'source_kv' in kwargs:
            source_kv = kwargs['source_kv']
            for obj in model.models:
                if isinstance(obj,PowerSource):
                    obj.nominal_voltage = source_kv*1000
                if hasattr(obj,'name') and hasattr(obj,'nominal_voltage') and obj.name is not None and obj.name in source_names_set:
                    obj.nominal_voltage = source_kv*1000
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Source_Voltage.main()

    
