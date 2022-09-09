from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

import math
import pyproj
import os
from ditto.models.line import Line
from ditto.models.capacitor import Capacitor
from ditto.models.phase_capacitor import PhaseCapacitor
from ditto.models.line import Line
from ditto.models.load import Load
from ditto.models.powertransformer import PowerTransformer
from ditto.modify.modify import Modifier

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.Set_Lat_Longs')


class Set_Lat_Longs(DiTToLayerBase):
    name = "set_lat_longs"
    uuid = UUID("99a7777f-e482-4e17-a39e-e5cc9644b076")
    version = '0.1.0'
    desc = "Replace stateplane coordinates within the ditto model to be lat/long instead"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['dataset'] = Kwarg(default=None, description='Dataset area being used',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['region'] = Kwarg(default=None, description='Region',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        dataset = None
        if 'dataset' in kwargs:
            dataset = kwargs['dataset']
        if 'region' in kwargs:
            region = kwargs['region']

        node_lines = {} # a map from a node (which is adjacent to a fuse) to a list of all non-fuse lines that it connects to
        min_node_ampacity = {} # a map from a node to the minimum ampacity of all non-fuse lines that it connects to
        # Initialize the nodes which are adjacent to a fuse (as an empty list)
        for i in model.models:
            if isinstance(i,Line) and i.is_fuse:
                node_lines[i.to_element] =[]
                node_lines[i.from_element] =[]

        # Find lines next to the nodes of the fuse
        for i in model.models:
            if isinstance(i,Line) and not i.is_fuse:
                if i.from_element in node_lines:
                    node_lines[i.from_element].append(i.name)
                if i.to_element in node_lines:
                    node_lines[i.to_element].append(i.name)


        if region == 'P10U':
            modifier = Modifier()
            all_capacitors = []
            for i in model.models:
                if isinstance(i,Capacitor) and len(i.phase_capacitors) == 3:
                    all_capacitors.append(i.name)
                    

                if hasattr(i,'pt_ratio') and i.pt_ratio is not None: 
                    i.pt_ratio = i.pt_ratio*(3**0.5)
                if isinstance(i,Line):
                    if i.from_element in model.model_names and model[i.from_element].nominal_voltage is not None:
                        if model[i.from_element].nominal_voltage < 30000 and model[i.from_element].nominal_voltage > 600 and len(i.wires)==2:
                            replacement_cap_matrix = i.capacitance_matrix
                            for cap_i in range(len(replacement_cap_matrix)):
                                for cap_j in range(len(replacement_cap_matrix[0])):
                                    replacement_cap_matrix[cap_i][cap_j] = replacement_cap_matrix[cap_i][cap_j]/(3**0.5)*0
                            i.capacitance_matrix = replacement_cap_matrix
    
                    elif i.to_element in model.model_names and model[i.to_element].nominal_voltage is not None:
                        if model[i.to_element].nominal_voltage < 30000 and model[i.to_element].nominal_voltage > 600 and len(i.wires) == 2:
                            replacement_cap_matrix = i.capacitance_matrix
                            for cap_i in range(len(replacement_cap_matrix)):
                                for cap_j in range(len(replacement_cap_matrix[0])):
                                    replacement_cap_matrix[cap_i][cap_j] = replacement_cap_matrix[cap_i][cap_j]/(3**0.5)*0
                            i.capacitance_matrix = replacement_cap_matrix


                if isinstance(i,PowerTransformer) and len(i.windings) == 2:
                    if i.windings[1].nominal_voltage < 30000:
                        i.windings[1].connection_type = 'D'

                if isinstance(i,Load) and len(i.phase_loads) == 2:
                    i.connection_type = 'Y'

            for capacitor in all_capacitors:
                    i = model[capacitor]
                    i.connection_type = 'D'
                    cap_var = i.phase_capacitors[0].var
                    for phase_capacitor in i.phase_capacitors:
                        modifier.delete_element(model,phase_capacitor)
                    i.phase_capacitors = []
                    cap2 = modifier.copy(model,i)
                    cap3 = modifier.copy(model,i)
                    i.name = i.name+'_1'
                    cap2.name = cap2.name+'_2'
                    cap3.name = cap3.name+'_3'

                    phase_cap1a = PhaseCapacitor(model)
                    phase_cap1a.phase = 'A'
                    phase_cap1a.var = cap_var/2
                    phase_cap1b = PhaseCapacitor(model)
                    phase_cap1b.phase = 'B'
                    phase_cap1b.var = cap_var/2
                    i.phase_capacitors = [phase_cap1a,phase_cap1b]

                    phase_cap2b = PhaseCapacitor(model)
                    phase_cap2b.phase = 'B'
                    phase_cap2b.var = cap_var/2
                    phase_cap2c = PhaseCapacitor(model)
                    phase_cap2c.phase = 'C'
                    phase_cap2c.var = cap_var/2
                    cap2.phase_capacitors = [phase_cap2b,phase_cap2c]
                        
                    phase_cap3c = PhaseCapacitor(model)
                    phase_cap3c.phase = 'C'
                    phase_cap3c.var = cap_var/2
                    phase_cap3a = PhaseCapacitor(model)
                    phase_cap3a.phase = 'A'
                    phase_cap3a.var = cap_var/2
                    cap3.phase_capacitors = [phase_cap3c,phase_cap3a]
                    

        # For each node, find the minimum ampacity of all the non-fuse lines that it connects to
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



        print('adjusting co-ordinate system')
        projection = {'dataset_4':'epsg:32610', 'dataset_3':'epsg:32617', 'dataset_2':'epsg:32613','t_and_d':'epsg:32614','houston':'epsg:32614','texas_rural':'epsg:32614','South_Texas':'epsg:32614','texas_test':'epsg:32614','Full_Texas':'epsg:32614'}
        invproj = pyproj.Proj(init=projection[dataset],preserve_units=True) 
        for i in model.models:
            if isinstance(i,Line) and hasattr (i,'is_fuse') and i.is_fuse and hasattr(i,'wires') and i.wires is not None:
                for wire in i.wires:
                    if wire.interrupting_rating == 100:
                        min_adjacent_ampacity = min(min_node_ampacity[i.from_element],min_node_ampacity[i.to_element])
                        #print(min_adjacent_ampacity,len(i.wires))
                        if min_adjacent_ampacity/len(i.wires) > wire.interrupting_rating:
                            wire.interrupting_rating = min_adjacent_ampacity/(len(i.wires))

            if hasattr(i,"positions") and i.positions is not None and len(i.positions) >0:
                for pos in i.positions:
                    x = pos.long
                    y = pos.lat
                    lat_long = invproj(x,y,inverse=True)
                    i_lat = lat_long[1]
                    i_long = lat_long[0]
                    pos.long = i_long
                    pos.lat = i_lat

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Lat_Longs.main()

    
