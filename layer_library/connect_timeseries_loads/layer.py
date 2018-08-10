from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.load import Load
from ditto.models.timeseries import Timeseries

import h5py
import pandas as pd
import os
logger = logging.getLogger('layerstack.layers.Connect_Timeseries_Loads')


class Connect_Timeseries_Loads(DiTToLayerBase):
    name = "connect_timeseries_loads"
    uuid = UUID("bfdfb90d-677d-4f9d-affd-d129ce7fc108")
    version = '0.1.0'
    desc = "Layer to attach timeseries loads to a DiTTo model using the extended customer file and load profiles"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['customer_file'] = Kwarg(default=None, description='location of the customer infomration file. Header format of "X, Y, Z, Identifier, voltage level, peak active power, peak reactive power, phases, area, height, energy, coincident active power, coincident reactive power, equivalent users, building type, PV capacity, (empty), (empty), (empty)"', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['residential_load_data'] = Kwarg(default=None, description='location of the h5 file defining the total timeseries load information for residential customers (not divided by enduse)', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['residential_load_metadata'] = Kwarg(default=None, description='location of the csv file defining the residential timeseries load metadata', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['commercial_load_data'] = Kwarg(default=None, description='location of the h5 file defining the total timeseries load information for commercial customers (not divided by enduse)', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['commercial_load_metadata'] = Kwarg(default=None, description='location of the csv file defining the commercial timeseries load metadata', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['output_folder'] = Kwarg(default=None, description='location of the csv files to be attached to timeseries models', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

     # Select timeseries with the largest peak value less than the P of the DiTTo load 
    @classmethod
    def apply(cls, stack, model, residential_load_data=None, residential_load_metadata=None, commercial_load_data=None, commercial_load_metadata=None, customer_file=None, output_folder=None):
        if residential_load_data is None or residential_load_metadata is None or commercial_load_data is None or commercial_load_metadata is None or customer_file is None:
            logging.warning("Load data not attached")
            return model
        if output_folder is None:
            output_folder = '.'

        customer_file_headers = ['X', 'Y', 'Z','Identifier', 'voltage level', 'peak active power', 'peak reactive power', 'phases', 'area', 'height', 'energy', 'coincident active power', 'coincident reactive power', 'equivalent users', 'building type', 'PV capacity', '', '','']
        building_types = {
                           1:'single-family',
                           2:'multi-family',
                           3:'stand-alone_retail',
                           4:'strip_mall',
                           5:'supermarket',
                           6:'warehouse',
                           7:'hotel',
                           8:'education',
                           9:'office',
                           10:'restaurant',
                           11:'outpatient_healthcare',
                           12:'hospital',
                           13:'industrial',
                           14:'NA'
        }

        commercial_mapping = {
                              'Industrial_Service': 'industrial',
                              'Retail_Freestanding': 'stand-alone_retail',
                              'HealthCare_AssistedLiving': 'multi-family',
                              'Office_Medical': 'outpatient_healthcare',
                              'Industrial_Warehouse': 'warehouse',
                              'Multi_Family_Apartments': 'multi-family',
                              'Retail_Bar': 'restaurant',
                              'Retail_FastFood': 'restaurant',
                              'Office_IndustrialLive_WorkUnit': 'office',
                              'Retail_Storefront': 'supermarket',
                              'Industrial_Distribution': 'warehouse',
                              'Hospitality_Hotel': 'hotel',
                              'Retail_Restaurant': 'restaurant',
                              'Retail_StorefrontRetail_Residential': 'strip_mall',
                              'Retail_Bank': 'office',
                              'Flex_LightDistribution': 'warehouse',
                              'Specialty_Schools': 'education',
                              'Retail_DayCareCenter': 'education',
                              'Industrial_TruckTerminal': 'warehouse',
                              'Retail_StorefrontRetail_Office': 'strip_mall',
                              'HealthCare_Hospital': 'hospital',
                              'Office_Loft_CreativeSpace': 'office',
                              'Flex_LightManufacturing': 'industrial',
                              'Multi_Family_Dormitory': 'multi-family',
                              'Specialty_Self_Storage': 'warehouse',
                              'Industrial_Showroom': 'warehouse',
                              'Retail_GardenCenter': 'stand-alone_retail',
                              'Hospitality_Motel': 'hotel',
                              'Specialty_PostOffice': 'strip_mall',
                              'Flex_Showroom': 'strip_mall',
                              'HealthCare_RehabilitationCenter': 'outpatient_healthcare',
                              'Office_OfficeLive_WorkUnit': 'office',
                              'HealthCare_ContinuingCareRetirementCommunity': 'multi-family',
                              'Specialty_AirplaneHangar': 'warehouse',
                              'Retail_DepartmentStore': 'stand-alone_retail',
                              'Office_Office_Residential': 'office'
        }

        commercial_categories = {}
        for i in commercial_mapping:
            if commercial_mapping[i] in commercial_categories:
                commercial_categories[commercial_mapping[i]].append(i)
            else:
                commercial_categories[commercial_mapping[i]] = [i]




        customer_file_headers_index = {}
        for i in range(len(customer_file_headers)):
            customer_file_headers_index[customer_file_headers[i]] = i


        hf_res = h5py.File(residential_load_data,'r')
        hf_com = h5py.File(commercial_load_data,'r')
        cnt = 0


        """
        TODO: Apply this for enduses
        electricity_map = {}
        all_enduses = list(hf['enumerations']['enduse'][:])

        for entry in all_enduses:
            if entry[2].decode('UTF-8')=='electricity':
                electricity_map[cnt] = entry[0].decode('UTF-8')
            cnt+=1
        """

        data_residential = hf_res['data']['res__SingleFamilyDetached']['data']
        metadata_residential = pd.read_csv(residential_load_metadata)
        data_shape_residential =data_residential.shape # (load_id, enduse, hour)
        peak_loads_residential = [0 for i in range(data_shape_residential[0])]

        data_commercial = hf_com['data']['res__SingleFamilyDetached']['data']
        metadata_commercial = pd.read_csv(commercial_load_metadata)
        data_shape_commercial =data_commercial.shape # (load_id, enduse, hour)
        peak_loads_commercial = [0 for i in range(data_shape_commercial[0])]

        for profile in range(data_shape_residential[0]):
            d1 = data_residential[profile][:][:]
            for hour in range(data_shape_residential[2]):
                electricity = d1[0][hour]
                peak_loads_residential[profile] = max(peak_loads_residential[profile],electricity)

        sorted_peaks_residential = []
        for i in range(len(peak_loads_residential)):
            sorted_peaks_residential.append((peak_loads_residential[i],i))
        sorted_peaks_residential = sorted(sorted_peaks_residential)


        # TODO: Scale commercial loads by building footprint.
        for profile in range(data_shape_commercial[0]):
            d1 = data_commercial[profile][:][:]
            costar_bldg_type[profile] = metadata_residential['costar_bldg_type'].iloc[profile]
            profile_building_map[profile] = commercial_mapping[costar_bldg_type]
            for hour in range(data_shape_commercial[2]):
                electricity = d1[0][hour]
                peak_loads_commercial[profile] = max(peak_loads_commercial[profile],electricity)

        sorted_peaks_commercial = []
        for i in range(len(peak_loads_commercial)):
            sorted_peaks_commercial.append((peak_loads_commercial[i],i))
        sorted_peaks_commercial = sorted(sorted_peaks_commercial)
        sorted_peaks_commercial_segmented = {}
        for i in sorted_peaks_commercial:
            commercial_type = profile_building_map[i[1]]
            if commercial_type in sorted_peaks_commercial_segmented:
                sorted_peaks_commercial_segmented[commercial_type].append(i)
            else:
                sorted_peaks_commercial_segmented[commercial_type] = [i]

        timeseries_map = {}
        timeseries_type = {}

        for row in open(customer_file,'r'):
            split_row = row.split(';') # A csv file delimited by ;
            load_name = split_row[customer_file_headers_index['Identifier']].lower()
            total_p = float(split_row[customer_file_headers_index['peak active power']])
            customer_type = building_types[int(split_row[customer_file_headers_index['building type']])]

            if total_p >0 and customer_type == 'single-family':
                selected_timeseries = 0
                for i in range(len(sorted_peaks_residential)):
                    if total_p<sorted_peaks_residential[i][0]:
                        break
                    selected_timeseries = sorted_peaks_residential[i][1]
                timeseries_map[load_name] = selected_timeseries
                timeseries_type[load_name] = 'residential'
            elif total_p>0 and customer_type in sorted_peaks_commercial_segmented:
                selected_timeseries = 0
                for i in range(len(sorted_peaks_commercial_segmented[customer_type])):
                    if total_p<sorted_peaks_commercial_segmented[customer_type][i][0]:
                        break
                    selected_timeseries = sorted_peaks_commercial_segmented[customer_type][i][1] 
                timeseries_map[load_name] = selected_timeseries
                timeseries_type[load_name] = 'commercial'


            else:
               logging.warning("Warning - no load type for {name}".format(name=load_name))
               print("Warning - no load type for {name}".format(name=load_name))

#import pdb;pdb.set_trace()
        timestamp = hf_res['enumerations']['time'][:]
        written_timeseries = set()
        # Only the loads that are non-zero in the customers_ext files and are single-family or multi-family buildings attach the timeseries
        for load in timeseries_map:

            if 'load_'+load not in model.model_names:
                print(load)
                continue

            uuid = metadata_residential['_id'].iloc[timeseries_map[load]]
            timeseries = Timeseries(model)
            timeseries.data_label='residential_'+str(timeseries_map[load])
            timeseries.interval = 3600 #Hourly data = 60*60
            timeseries.data_type = 'float'
            timeseries.scale_factor = 1
            timeseries.data_location = os.path.join(output_folder,uuid+'.csv')
            profile = timeseries_map[load]

            model['load_'+load].timeseries = [timeseries]
            
            if profile in written_timeseries:
                continue
            if timeseries_type[load] == 'residential':
                timeseries = data_residential[profile][0][:]
            if timeseries_type[load] == 'commercial':
                timeseries = data_commercial[profile][0][:]

            written_timeseries.add(profile)
            output = pd.DataFrame([timestamp,timeseries])
            output.to_csv(os.path.join(output_folder,uuid+'.csv'))

        return model
        

"""

        for element in model.models:
            if isinstance(element,Load) and hasattr(element,'phase_loads') and element.phase_loads is not None and element.name is not None:
            load_name = element.name
            total_p = 0
            for phase_load in element.phase_loads:
                if hasattr(phase_load,'p') and phase_load.p is not None:
                    total_p+=phase_load.p

            # Select timeseries with the largest peak value less than the P of the DiTTo load 

            if total_p >0:
                # TODO: Check customer class 
                selected_timeseries = 0
                for i in range(len(sorted_peaks)):
                    if p>sorted_peaks[i][0]:
                        break
                    selected_timeseries = i
                timeseries_map[load_name] = selected_timeseries
                
"""               
               



if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Connect_Timeseries_Loads.main()

    
