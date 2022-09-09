from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.line import Line
from ditto.models.capacitor import Capacitor

logger = logging.getLogger('layerstack.layers.Fix_Disconnected_Capacitors')


class Fix_Disconnected_Capacitors(DiTToLayerBase):
    name = "fix_disconnected_capacitors"
    uuid = UUID("ae3a650e-d0b1-497b-9b96-0994e28df483")
    version = '0.1.0'
    desc = "Fix capacitors which have the monitored element on another feeder or substation"

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

        all_bus_lines = {} # map from each node to the set of lines it's connected to
        for i in model.models:
            if isinstance(i,Line):
                if hasattr(i,'feeder_name') and i.feeder_name is not None and i.feeder_name!='':
                    if i.from_element is not None and i.to_element is not None:
                        if not i.from_element in all_bus_lines:
                            all_bus_lines[i.from_element] = set()
                        all_bus_lines[i.from_element].add(i.name)
                        if not i.to_element in all_bus_lines:
                            all_bus_lines[i.to_element] = set()
                        all_bus_lines[i.to_element].add(i.name)

        for i in model.models:
            if isinstance(i,Capacitor):
                feeder = i.feeder_name
                measuring_element = i.measuring_element
                connecting_element = i.connecting_element
                if model[i.measuring_element].feeder_name != feeder or type(model[i.measuring_element]) != Line:
                    if not connecting_element in all_bus_lines:
                        if model[measuring_element].from_element != connecting_element:
                            connecting_element = model[measuring_element].from_element
                        elif model[measuring_element].to_element != connecting_element:
                            connecting_element = model[measuring_element].to_element
                    for line in all_bus_lines[connecting_element]:
                        if model[line].feeder_name == feeder and type(model[line]) == Line:
                            i.measuring_element = line
                            break





        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Fix_Disconnected_Capacitors.main()

    
