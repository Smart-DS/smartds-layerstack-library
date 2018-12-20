from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import os

from layerstack.args import Arg, Kwarg
import pandas as pd
from ditto.dittolayers import DiTToLayerBase
from ditto.models.node import Node
from ditto.models.regulator import Regulator
from ditto.models.winding import Winding
from ditto.models.phase_winding import PhaseWinding

logger = logging.getLogger('layerstack.layers.Add_Additional_Regulators')


class Add_Additional_Regulators(DiTToLayerBase):
    name = "add_additional_regulators"
    uuid = UUID("434e878b-e876-4377-bfd4-330d3cd9ce9e")
    version = '0.1.0'
    desc = "Connect additional regulators from csv file based on additional analysis"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['file_location'] = Kwarg(default=None, description='csv file location for list of lines that need regulators added to the end of them',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['setpoint'] = Kwarg(default=None, description='The regulator setpoint',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        file_location = None
        setpoint = None
        if 'file_location' in kwargs:
            file_location = kwargs['file_location']
        if 'setpoint' in kwargs:
            setpoint = kwargs['setpoint']

        if not os.path.exists(file_location):
            return model
        lines = pd.read_csv(file_location)
        model.set_names()
        for index,row in lines.iterrows():
            line = row['name'].lower() #csv file has a single column with heading of 'name'
            split_line = line.split('_')
            from_element = '_'.join(split_line[:-1])
            to_element = split_line[-1]
            for m in model.models:
                if hasattr(m,'from_element') and hasattr(m,'to_element') and m.from_element == from_element and m.to_element == to_element:
                    line_name = m.name
                    print(line_name)
                    obj = model[line_name]
                    if hasattr(obj,'to_element') and obj.to_element is not None:
                        to_element = obj.to_element
                        end_node = model[to_element]
                        int_node = Node(model)
                        int_node.phases = end_node.phases
                        int_node.positions = end_node.positions
                        int_node.substation_name = end_node.substation_name
                        int_node.feeder_name = end_node.feeder_name
                        int_node.nominal_voltage = end_node.nominal_voltage
                        int_node.is_substation_connection = end_node.is_substation_connection
    
                        int_node.name = end_node.name+"_reg"
                        obj.to_element = int_node.name
    
                        reg = Regulator(model)
                        reg.name = 'addreg_'+end_node.name
                        reg.from_element = int_node.name
                        reg.to_element = end_node.name
                        reg.feeder_name = end_node.feeder_name
                        reg.substation_name = end_node.substation_name
                        reg.positions = end_node.positions
                        windings = []
                        for i in range(2):
                            winding1 = Winding(model)
                            winding1.nominal_voltage = end_node.nominal_voltage
                            winding1.rated_power = 10000000 #stored in VA not KVA
                            winding1.voltage_type = i
                            phase_windings1 = []
                            for p in end_node.phases:
                                phase_winding = PhaseWinding(model)
                                phase_winding.phase = p.default_value
                                phase_windings1.append(phase_winding)
                            winding1.phase_windings = phase_windings1
                            windings.append(winding1)
                        reg.windings = windings
                        reg.ltc=0
                        reg.is_subtation = 0
                        reg.pt_ratio = float(obj.nominal_voltage)/120.0/(3**0.5)
                        reg.ct_ratio = 100.0
                        reg.bandwidth = 2.0
                        if setpoint is not None:
                            reg.setpoint = setpoint

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Add_Additional_Regulators.main()

    
