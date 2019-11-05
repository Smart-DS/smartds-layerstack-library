from __future__ import print_function, division, absolute_import
import os

import json_tricks
from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.photovoltaic import Photovoltaic
from ditto.models.base import Unicode
from ditto.modify.system_structure import system_structure_modifier
from ditto.models.load import Load

logger = logging.getLogger('layerstack.layers.Add_Pv')


class Add_Pv(DiTToLayerBase):
    name = "add_PV"
    uuid = UUID("004096a7-c5b8-4b11-9b74-2d449a48d16b")
    version = 'v0.1.0'
    desc = "Layer for adding PV into DiTTO for a distribution model"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
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
        kwarg_dict['single_size'] = Kwarg(default=None, description='A single kW size to be applied to all placements',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['residential_sizes'] = Kwarg(default=None, description='Range of Kw sizes to be applied to different residential customers',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['commercial_sizes'] = Kwarg(default=None, description='Range of building areas in m^2 for partitioning commercial customers',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['residential_areas'] = Kwarg(default=None, description='Range of building areas in m^2 for partitioning residential customers',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['commercial_areas'] = Kwarg(default=None, description='Range of Kw sizes to be applied to different commercial customers',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['customer_file'] = Kwarg(default=None, description='Commercial file for distinguishing commerical and residential loads',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['max_feeder_sizing_percent'] = Kwarg(default=None, description='List of percentages of total load on the feeder that the total PV installed cannot exceed',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['power_factors'] = Kwarg(default=None, description='List of power factors for each placement',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['inverters'] = Kwarg(default=None, description='List of inverters for each placement',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['cutin'] = Kwarg(default=None, description='List of cutin values for each placement',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['cutout'] = Kwarg(default=None, description='List of cutout values for each placement',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['kvar_percent'] = Kwarg(default=None, description='Percentage of KVA as kvar limit',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['oversizing'] = Kwarg(default=None, description='Amount the inverter is oversized',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        return kwarg_dict


    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        placement_folder = kwargs['placement_folder']
        placements = kwargs['placement_names']
        if placements is None or placements == [None]:
            return model
        single_size = None
        residential_sizes = None
        commercial_sizes = None
        customer_file = None
        power_factors = None
        inverters = None
        cutin = None
        cutout = None
        kvar_percent = None
        oversizing = None

        if 'single_size' in kwargs:
            single_size = kwargs['single_size']

        if 'residential_sizes' in kwargs:
            residential_sizes = kwargs['residential_sizes']

        if 'commercial_sizes' in kwargs:
            commercial_sizes = kwargs['commercial_sizes']

        if 'residential_areas' in kwargs:
            residential_areas = kwargs['residential_areas']

        if 'commercial_areas' in kwargs:
            commercial_areas = kwargs['commercial_areas']

        if 'customer_file' in kwargs:
            customer_file = kwargs['customer_file']

        if 'max_feeder_sizing_percent' in kwargs:
            max_feeder_sizing_percent = kwargs['max_feeder_sizing_percent']

        if 'power_factors' in kwargs:
            power_factors = kwargs['power_factors']

        if 'inverters' in kwargs:
            inverters = kwargs['inverters']

        if 'cutin' in kwargs:
            cutin = kwargs['cutin']

        if 'cutout' in kwargs:
            cutout = kwargs['cutout']

        if 'kvar_percent' in kwargs:
            kvar_percent = kwargs['kvar_percent']

        if 'oversizing' in kwargs:
            oversizing = kwargs['oversizing']

        total_feeder_load = {}
        total_pv = {}
        for i in model.models:
            if isinstance(i,Load):
                local_load = 0
                for ph in i.phase_loads:
                    local_load+=ph.p
                if i.feeder_name is not None and i.substation_name is not None:
                    lookup = i.substation_name+"_"+i.feeder_name
                    if lookup in total_feeder_load:
                        total_feeder_load[lookup] = total_feeder_load[lookup]+ local_load
                    else:
                        total_feeder_load[lookup] = local_load


        all_load_kws = {}
        customer_classes = {}
        if residential_sizes is not None and commercial_sizes is not None and customer_file is not None and commercial_areas is not None and residential_areas is not None:
            for row in open(customer_file,'r').readlines():
                sp_row = row.split(';')
                area = float(sp_row[8])
                cust_type = sp_row[-3]
                name = sp_row[3]
                
                kw = None
                if cust_type == 'Res':
                    customer_classes['load_'+name.lower()] = 'residential'
                    if area < residential_areas[0]:
                        kw = residential_sizes[0]
                    elif area >= residential_areas[-1]:
                        kw = residential_sizes[-1]
                    else:
                        for i in range(1,len(residential_areas)):
                            if area < residential_areas[i]:
                                kw = residential_sizes[i] 

                else:
                    customer_classes['load_'+name.lower()] = 'commercial'
                    if area < commercial_areas[0]:
                        kw = commercial_sizes[0]
                    elif area >= commercial_areas[-1]:
                        kw = commercial_sizes[-1]
                    else:
                        for i in range(1,len(commercial_areas)):
                            if area < commercial_areas[i]:
                                kw = commercial_sizes[i] 
                all_load_kws['load_'+name.lower()] = kw




        placement_cnt = 0
        prev_placement_set = set() #assume at most one solar per location
        for placement in placements:
            locations = []
            with open(os.path.join(placement_folder,placement), "r") as f:
                locations_feeders = json_tricks.load(f)
                for key in locations_feeders:
                    locations.extend(locations_feeders[key])
            seen_elements = {}
            for location in locations:
                if location in prev_placement_set:
                    continue
                prev_placement_set.add(location)
                node_to_connect = model[location]
                if hasattr(node_to_connect,'connecting_element'):
                    connected_node = model[location].connecting_element
                    node_to_connect = model[connected_node] #Connect the PV to the upstream node not directly to the load
                feeder_name = None
                substation_name = None
                if hasattr(node_to_connect,'feeder_name'):
                    feeder_name = node_to_connect.feeder_name
                if hasattr(node_to_connect,'substation_name'):
                    substation_name = node_to_connect.substation_name

                kw = single_size # May be none
                if model[location].name in all_load_kws:
                    kw = all_load_kws[model[location].name]


                lookup = substation_name+"_"+feeder_name
                at_max = False
                if lookup in total_feeder_load:
                    total_pv_local = kw
                    if lookup in total_pv:
                        total_pv_local += total_pv[lookup]

                    if max_feeder_sizing_percent is not None and total_pv_local > max_feeder_sizing_percent*total_feeder_load[lookup]/100.0:
                        at_max = True
                    if not at_max:
                        total_pv[lookup] = total_pv_local

                if at_max:
                    print(model[location].name+ " not added to feeder. Adding "+ str(kw/1000)  +" kW would create "+str(round(total_pv_local/total_feeder_load[lookup]*100,3))+" % PV penetration on feeder "+lookup)
                    continue # Continue and not break since there might be smaller solar loads that can fit

                pv = Photovoltaic(model)

                if hasattr(node_to_connect,'feeder_name'):
                    pv.feeder_name = node_to_connect.feeder_name
                if hasattr(node_to_connect,'substation_name'):
                    pv.substation_name = node_to_connect.substation_name
                if hasattr(node_to_connect,'nominal_voltage'):
                    pv.nominal_voltage = node_to_connect.nominal_voltage
                pv.name = 'pv_'+model[location].name
                try:
                    pv.customer_class = customer_classes[model[location].name]
                except:
                    pv.customer_class = 'commercial'
                if pv.name in seen_elements:
                    seen_elements[pv.name] = seen_elements[pv.name]+1
                    pv.name = pv.name+'_'+str(seen_elements[pv.name])
                else:
                    seen_elements[pv.name] = 0

                pv.rated_power = kw #The size of the panel itself. Inverter defined through active and reactive
                pv.connecting_element = node_to_connect.name
                phases = []
                if hasattr(model[location],'phase_loads'):
                    for phase_load in model[location].phase_loads:
                        if phase_load.drop != 1:
                            phases.append(Unicode(phase_load.phase))
                else:
                    phases = node_to_connect.phases
                    # CHECK NO UNICODE PROBLEMS
                pv.phases = phases
                pv.power_factor = power_factors[placement_cnt]
                pv.cutout_percent = cutout[placement_cnt]
                pv.cutin_percent = cutin[placement_cnt]
                pv.control = inverters[placement_cnt]
                pv.active_rating = kw*oversizing[placement_cnt]
                if kvar_percent[placement_cnt] is None:
                    pv.reactive_rating = None
                else:
                    if pv.power_factor is not None and pv.power_factor !=0:
                        pv.reactive_rating = pv.active_rating/abs(pv.power_factor)*kvar_percent[placement_cnt]/100.0
                    else: #assume pf of 1
                        pv.reactive_rating = pv.active_rating*kvar_percent[placement_cnt]/100.0
                pv.temperature = 25
                #print(pv.name,pv.active_rating,pv.reactive_rating,pv.rated_power)
            placement_cnt+=1

        
        model.set_names()
        for key in total_feeder_load:
            if key in total_pv:
                print(key +" PV Penetration: "+str(round(total_pv[key]/float(total_feeder_load[key])*100,3))+'% PV: '+str(round(total_pv[key]/1000,3))+ " Load "+str(round(total_feeder_load[key]/1000,3)))
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    Add_Pv.main()

    
