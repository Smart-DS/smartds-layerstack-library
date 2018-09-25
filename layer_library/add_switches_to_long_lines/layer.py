from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.modify.modify import Modifier
from ditto.models.node import Node
from ditto.models.wire import Wire
from ditto.models.line import Line
from ditto.models.base import Unicode

logger = logging.getLogger('layerstack.layers.Add_Switches_To_Long_Lines')


class Add_Switches_To_Long_Lines(DiTToLayerBase):
    name = "add_switches_to_long_lines"
    uuid = UUID("f31d35d5-e05a-46d1-8ee8-1e6951b15bb3")
    version = '0.1.0'
    desc = "Add a switch for lines that are greater than 800 meters."

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['cutoff_length'] = Kwarg(default=800, description='length in meters at which the line must have switch added',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        cutoff_length = None
        if 'cutoff_length' in kwargs:
            cutoff_length = kwargs['cutoff_length']
        if cutoff_length is None:
            return model
        for i in model.models:
            if isinstance(i,Line) and i.length is not None and i.length >cutoff_length and i.feeder_name is not None and i.feeder_name != 'subtransmission':
                # Option 1: put a switch at one of the intermediate nodes 1/10 of the way down the line
                if i.positions is not None and len(i.positions) >10:
                    node1 = Node(model)
                    node2 = Node(model)
                    pos = int(len(i.positions)/10)

                    node1.is_substation_connection = 0
                    node1.feeder_name = i.feeder_name
                    node1.substation_name = i.substation_name
                    node1.nominal_voltage = i.nominal_voltage
                    node1.name = i.name+'_b1'
                    node1.positions = [i.positions[pos]]
                    node1_phases = []
                    for p in i.wires:
                        if p.phase is not None and p.phase in ['A','B','C','N']:
                            node1_phases.append(Unicode(p.phase))
                    node1.phases = node1_phases


                    node2.is_substation_connection = 0
                    node2.feeder_name = i.feeder_name
                    node2.substation_name = i.substation_name
                    node2.nominal_voltage = i.nominal_voltage
                    node2.name = i.name+'_b2'
                    node2.positions = [i.positions[pos+1]]
                    node2_phases = []
                    for p in i.wires:
                        if p.phase is not None and p.phase in ['A','B','C','N']:
                            node2_phases.append(Unicode(p.phase))
                    node2.phases = node2_phases

                    modifier = Modifier()
                    switch_break = modifier.copy(model,i)
                    switch_break.name = i.name+'_disconnect'
                    switch_break.length = 1 #1 meter
                    switch_break.positions = []
                    switch_break.from_element = node1.name
                    switch_break.to_element = node2.name
                    switch_break.is_switch = True
                    for wire in switch_break.wires:
                        wire.is_open=False

                    second_stretch = modifier.copy(model,i)
                    second_stretch.name = i.name+'_cont'
                    second_stretch.positions = i.positions[pos+2:]
                    second_stretch.from_element = node2.name
                    second_stretch.length = 9/10.0*i.length # rough estimate based on number of positions

                    i.to_element = node1.name
                    i.length = 1/10.0*i.length-1
                    if pos>0:
                        i.positions = i.positions[:pos-1]
                    else:
                        i.positions = []







                    


                    

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Add_Switches_To_Long_Lines.main()

    
