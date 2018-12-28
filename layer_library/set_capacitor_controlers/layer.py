from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.capacitor import Capacitor

logger = logging.getLogger('layerstack.layers.Set_Capacitor_Controlers')


class Set_Capacitor_Controlers(DiTToLayerBase):
    name = "set_capacitor_controlers"
    uuid = UUID("fdefef5b-f54a-4ed8-8cf7-99f033071590")
    version = '0.1.0'
    desc = "Set Capacitor controls"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['lowpoint'] = Kwarg(default=None, description='Voltage point in PT when the capacitor switches on',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['highpoint'] = Kwarg(default=None, description='Voltage point in PT when the capacitor switches off',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['delay'] = Kwarg(default=None, description='PT ratio of the element',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        lowpoint = None
        highpoint = None
        pt_ratio = None
        delay = None
        if 'lowpoint' in kwargs:
            lowpoint = kwargs['lowpoint']
        if 'highpoint' in kwargs:
            highpoint = kwargs['highpoint']
        if 'delay' in kwargs:
            delay = kwargs['delay']

        to_node_mapping = {}
        for i in model.models:
            if isinstance(i,Capacitor) and i.connecting_element is not None:
                i.low = lowpoint
                i.high = highpoint
                i.mode = "voltage"
                i.pt_ratio = float(i.nominal_voltage)/120/(3**0.5)
                i.ct_ratio = 100.0
                i.delay = delay
                if not i.connecting_element in to_node_mapping:
                    to_node_mapping[i.connecting_element] = [i.name]
                else:
                    to_node_mapping[i.connecting_element] = to_node_mapping[i.connecting_element].append(i.name)


        for i in model.models:
            if hasattr(i,'to_element') and i.to_element is not None and i.to_element in to_node_mapping:
                for element in to_node_mapping[i.to_element]:
                    model[element].measuring_element = i.name

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Capacitor_Controlers.main()

    
