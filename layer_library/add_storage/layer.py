from __future__ import print_function, division, absolute_import

import os
import json_tricks
from builtins import super
import logging
from uuid import UUID
from ditto.models.storage import Storage
from ditto.models.photovoltaic import Photovoltaic
from ditto.models.phase_storage import PhaseStorage

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.base import Unicode
import json

logger = logging.getLogger('layerstack.layers.Add_Storage')


class Add_Storage(DiTToLayerBase):
    name = "add_storage"
    uuid = UUID("ceae532c-7fce-4674-b7aa-eaa69e219c9c")
    version = 'v0.1.0'
    desc = "Layer for adding static storage to a model"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('placement', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('rated_power', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('rated_kWh', description='', parser=None, choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['placement_folder'] = Kwarg(default=None, description='Location of placement folder',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['placement_names'] = Kwarg(default=None, description='A list of placements to be applied',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['single_kw'] = Kwarg(default=None, description='A single kW size to be applied to all placements',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['single_kwh'] = Kwarg(default=None, description='A single kWh size to be applied to all placements',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['kw_values'] = Kwarg(default=None, description='Range of Kw sizes to be applied to different customers',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['kwh_values'] = Kwarg(default=None, description='Range of kWh values to be applied to different customers',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['connected_pv_threshold'] = Kwarg(default=None, description='Threshold of connected Pv when transition between sizes',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['max_feeder_sizing_percent'] = Kwarg(default=None, description='List of percentages of total load on the feeder that the total Storage installed cannot exceed',
                                         parser=None, choices=None,
                                         nargs=None, action=None) #Unused at this point
        kwarg_dict['starting_percentage'] = Kwarg(default=None, description='Percentage of kWh the battery starts with',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['charge_efficiency'] = Kwarg(default=None, description='Percentage efficiency of charging',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['discharge_efficiency'] = Kwarg(default=None, description='Percentage efficiency of discharging',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['oversizing'] = Kwarg(default=None, description='Amount the inverter is oversized',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['kvar_percent'] = Kwarg(default=None, description='Percentage of KVA as kvar limit',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['power_factor'] = Kwarg(default=None, description='Kw power factor',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['is_substation'] = Kwarg(default=None, description='Whether or not its located in a sub',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict




    @classmethod
    def apply(cls, stack, model, *args, **kwargs):

        placement_folder = kwargs['placement_folder']
        placements = kwargs['placement_names']
        if placements is None or placements == [None]:
            return model

        single_kw = None
        if 'single_kw' in kwargs:
            single_kw = kwargs['single_kw']
        single_kwh = None
        if 'single_kwh' in kwargs:
            single_kwh = kwargs['single_kwh']
        kw_values = None
        if 'kw_values' in kwargs:
            kw_values = kwargs['kw_values']
        kwh_values = None
        if 'kwh_values' in kwargs:
            kwh_values = kwargs['kwh_values']
        connected_pv_threshold = None
        if 'connected_pv_threshold' in kwargs:
            connected_pv_threshold = kwargs['connected_pv_threshold']
        max_feeder_sizing_percent = None
        if 'max_feeder_sizing_percent' in kwargs:
            max_feeder_sizing_percent = kwargs['max_feeder_sizing_percent']
        starting_percentage = None
        if 'starting_percentage' in kwargs:
            starting_percentage = kwargs['starting_percentage']
        charge_efficiency = None
        if 'charge_efficiency' in kwargs:
            charge_efficiency = kwargs['charge_efficiency']
        discharge_efficiency = None
        if 'discharge_efficiency' in kwargs:
            discharge_efficiency = kwargs['discharge_efficiency']
        oversizing = None
        if 'oversizing' in kwargs:
            oversizing = kwargs['oversizing']
        kvar_percent = None
        if 'kvar_percent' in kwargs:
            kvar_percent = kwargs['kvar_percent']
        power_factor = None
        if 'power_factor' in kwargs:
            power_factor = kwargs['power_factor']
        is_substation = False
        if 'is_substation' in kwargs:
            is_substation = kwargs['is_substation']


        pv_capacities = {}
        if connected_pv_threshold is not None:
            for i in model.models:
                if isinstance(i,Photovoltaic):
                    if i.connecting_element is not None and i.rated_power is not None:
                        if i.connecting_element in pv_capacities:
                            pv_capacities[i.connecting_element] = pv_capacities[i.connecting_element]+i.rated_power
                        else:
                            pv_capacities[i.connecting_element] = i.rated_power


        placement_cnt = 0 #Currently parameters are the same for all placements so this isn't used
        seen_elements = {}
        for placement in placements:
            connecting_elements = []
            if not os.path.exists(os.path.join(placement_folder,placement)):
                print('Skipping placement '+placement+'...')
                continue
            with open(os.path.join(placement_folder,placement), "r") as f_input:
                locations_feeders = json_tricks.load(f_input)
                for key in locations_feeders:
                    connecting_elements.extend(locations_feeders[key])

            for location in connecting_elements:
                node_to_connect = model[location]
                if hasattr(node_to_connect,'connecting_element'):
                    attachpoint = model[location].connecting_element
                else:
                    attachpoint = location
                ps = Storage(model)
                ps.name = 'storage_'+attachpoint
                if ps.name in seen_elements:
                    seen_elements[ps.name] = seen_elements[ps.name]+1
                    ps.name = ps.name+'_'+str(seen_elements[ps.name])
                else:
                    seen_elements[ps.name] = 0

                if is_substation:
                    ps.is_substation = True
                else:
                    ps.is_substation = False

                ps.connecting_element = attachpoint
                ps.state = "IDLING"
                ps.rated_kWh = single_kwh*1000
                ps.rated_power = single_kw*1000
                if attachpoint in model.model_names and model[attachpoint].feeder_name is not None:
                    ps.feeder_name = model[attachpoint].feeder_name
                if attachpoint in model.model_names and model[attachpoint].substation_name is not None:
                    ps.substation_name = model[attachpoint].substation_name
                phases = []
                if hasattr(model[location],'phase_loads'):
                    for phase_load in model[location].phase_loads:
                        if phase_load.drop != 1:
                            phases.append(Unicode(phase_load.phase))
                else:
                    phases = model[attachpoint].phases
    
                if len(phases) ==0: #problems upstream...
                    for i in ['A','B','C']:
                        phases.append(Unicode(i))
                if kwh_values is not None:
                    kw = None
                    kwh = None
                    if attachpoint in pv_capacities:
                        attached_pv = pv_capacities[attachpoint]
                        if attached_pv < connected_pv_threshold[0]:
                            kwh= kwh_values[0]
                            kw = kw_values[0]
                        elif attached_pv >= connected_pv_threshold[-1]:
                            kw = kw_values[-1]
                            kwh = kwh_values[-1]
                        else:
                            for i in range(1,len(connected_pv_threshold)):
                                if attached_pv < residential_areas[i]:
                                    kw = kw_values[i] 
                                    kwh = kwh_values[i] 
                ps.power_factor = power_factor
                ps.active_rating = ps.rated_power*oversizing
                if kvar_percent is None:
                    ps.reactive_rating = None
                else:
                    if ps.power_factor is not None and ps.power_factor !=0:
                        ps.reactive_rating = ps.active_rating/abs(ps.power_factor)*kvar_percent/100.0
                    else: #assume pf of 1
                        ps.reactive_rating = ps.active_rating*kvar_percent/100.0
    
    

    
                ps.stored_kWh = starting_percentage*ps.rated_kWh/100.0
                ps.discharging_efficiency = discharge_efficiency
                ps.charging_efficiency = charge_efficiency
    
                phase_storages = []
                for phase in phases:
                    phase_storage = PhaseStorage(model)
                    phase_storage.phase = phase.default_value
                    phase_storages.append(phase_storage)
                ps.phase_storages = phase_storages
    
    
        model.set_names()
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    Add_Storage.main()

    
