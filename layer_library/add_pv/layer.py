from __future__ import print_function, division, absolute_import

import json
from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.photovoltaic import Photovoltaic
from ditto.models.base import Unicode
from ditto.modify.system_structure import system_structure_modifier

logger = logging.getLogger('layerstack.layers.Add_Pv')


class Add_Pv(DiTToLayerBase):
    name = "add_PV"
    uuid = UUID("004096a7-c5b8-4b11-9b74-2d449a48d16b")
    version = 'v0.1.0'
    desc = "Layer for adding PV into DiTTO for a distribution model"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('placement', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('rated_power', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('power_factor', description='', parser=None, choices=None, nargs=None))
        return arg_list

    @classmethod
    def apply(cls, stack, model, placement,rated_power,power_factor):
        loads = json.load(open(placement))
        for load in loads:
            connected_node = model[load].connecting_element
            upstream_node = model[connected_node] #Connect the PV to the upstream node not directly to the load
            ps = Photovoltaic(model)
            ps.name = 'pv_'+load
            ps.connecting_element = upstream_node.name
            ps.rated_power = rated_power
            ps.active_rating = rated_power
            ps.reactive_rating = rated_power
            ps.power_factor = power_factor
            if hasattr(upstream_node,'feeder_name'):
                ps.feeder_name = upstream_node.feeder_name
            if hasattr(upstream_node,'substation_name'):
                ps.substation_name = upstream_node.substation_name
            phases = []
            for phase_load in model[load].phase_loads:
                if phase_load.drop != 1:
                    phases.append(Unicode(phase_load.phase))
            ps.phases = phases
        
        model.set_names()
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    Add_Pv.main()

    
