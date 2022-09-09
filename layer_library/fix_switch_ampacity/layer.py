from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.line import Line

logger = logging.getLogger('layerstack.layers.Fix_Switch_Ampacity')


class Fix_Switch_Ampacity(DiTToLayerBase):
    name = "fix_switch_ampacity"
    uuid = UUID("67a9d0f8-5a9b-4f4b-859f-4a0da2a0203d")
    version = '0.1.0'
    desc = "Switch ampacities seem to be low. Replace them with the lowest ampacity of neighboring lines if possible"

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
        model.set_names()
        node_lines = {} # a map from a node (which is adjacent to a switch) to a list of all non-switch lines that it connects to
        min_node_ampacity = {} # a map from a node to the minimum ampacity of all non-switch lines that it connects to

        # Initialize the nodes which are adjacent to a switch (as an empty list)
        for i in model.models:
            if isinstance(i,Line) and i.is_switch:
                node_lines[i.to_element] =[]
                node_lines[i.from_element] =[]

        # Find lines next to the nodes of the switch
        for i in model.models:
            if isinstance(i,Line) and not i.is_switch:
                if i.from_element in node_lines:
                    node_lines[i.from_element].append(i.name)
                if i.to_element in node_lines:
                    node_lines[i.to_element].append(i.name)

        # For each node, find the minimum ampacity of all the non-switch lines that it connects to
        # Firstly determine  the maximum ampacity of all the wires on a line. Then compute the mimimum ampacity of those lines
        for node in node_lines:
            min_ampacity = 1000000000
            for line in node_lines[node]:
                max_ampacity = -1
                for wire in model[line].wires:
                    max_ampacity = max(wire.ampacity,max_ampacity)
                if max_ampacity == -1:
                    max_ampacity = 1000000000
                min_ampacity = min(min_ampacity,max_ampacity)
            if min_ampacity != 1000000000:
                min_node_ampacity[node] = min_ampacity
            else:
                min_node_ampacity[node] = -1 #i.e. no adjacent lines to the node

        # Update the ampacity of the switches        
        for i in model.models:
            if isinstance(i,Line) and i.is_switch:
                current_ampacity = -1
                for wire in i.wires:
                    current_ampacity = max(wire.ampacity,current_ampacity)
                min_adjacent_ampacity = min(min_node_ampacity[i.from_element],min_node_ampacity[i.to_element])
                if min_adjacent_ampacity > current_ampacity:
                    for wire in i.wires:
                        wire.ampacity = min_adjacent_ampacity
                else:
                    print( i.name, i.wires[0].ampacity, min_adjacent_ampacity)
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Fix_Switch_Ampacity.main()

    
