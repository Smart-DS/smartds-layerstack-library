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
import sys
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

        kwarg_dict['write_cyme_file'] = Kwarg(default=True, description='write the cyme timeseries file', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['write_opendss_file'] = Kwarg(default=True, description='write the many opendss timeseries files', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

     # Select timeseries with the largest peak value less than the P of the DiTTo load 
    @classmethod
    def apply(cls, stack, model, residential_load_data=None, residential_load_metadata=None, commercial_load_data=None, commercial_load_metadata=None, customer_file=None, output_folder=None, write_cyme_file = True, write_opendss_file= True):
        if residential_load_data is None or residential_load_metadata is None or commercial_load_data is None or commercial_load_metadata is None or customer_file is None:
            logging.warning("Load data not attached")
            return model
        if output_folder is None:
            output_folder = '.'

        customer_file_headers = ['X', 'Y', 'Z','Identifier', 'voltage level', 'peak active power', 'peak reactive power', 'phases', 'area', 'height', 'energy', 'coincident active power', 'coincident reactive power', 'equivalent users', 'building type', 'Value', 'Year', 'PV capacity', 'Class', 'Rural/Urban','Zone']
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

        commercial_mapping = {
                              'com__FullServiceRestaurant': 'restaurant',
                              'com__Hospital': 'hospital',
                              'com__LargeHotel': 'hotel',
                              'com__LargeOffice': 'office',
                              'com__MediumOffice': 'office',
                              'com__MidriseApartment': 'multi-family',
                              'com__Outpatient': 'outpatient_healthcare',
                              'com__PrimarySchool': 'education',
                              'com__QuickServiceRestaurant': 'restaurant',
                              'com__StandaloneRetail': 'stand-alone_retail',
                              'com__SecondarySchool': 'education',
                              'com__SmallHotel': 'hotel',
                              'com__SmallOffice': 'office',
                              'com__StripMall': 'strip_mall',
                              'com__Warehouse': 'warehouse'
                              }




        commercial_categories = {}
        for i in commercial_mapping:
            if commercial_mapping[i] in commercial_categories:
                commercial_categories[commercial_mapping[i]].append(i)
            else:
                commercial_categories[commercial_mapping[i]] = [i]
        commercial_categories['industrial'] ='com__Warehouse'
        commercial_categories['supermarket'] ='com__StandaloneRetail'
        commercial_categories['NA'] ='com__MidriseApartment' #Use this as defualt for missing data




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

        data_commercial = {}
        data_shape_commercial = {}
        peak_loads_commercial = {}
        metadata_commercial = pd.read_csv(commercial_load_metadata)
        for key in commercial_mapping.keys():
            data_commercial[key] = hf_com['data'][key]['data'] 
            data_shape_commercial[key] = data_commercial[key].shape # (load_id, enduse, hour)
            peak_loads_commercial[key] = [0 for j in range(data_shape_commercial[key][0])]

        for profile in range(data_shape_residential[0]):
            d1 = data_residential[profile][:][:]
            electricity = sum(d1[i][:] for i in range(len(d1))) # Sum over all electricity enduses
            for hour in range(data_shape_residential[2]):
                peak_loads_residential[profile] = max(peak_loads_residential[profile],electricity[hour])

        sorted_peaks_residential = []
        for i in range(len(peak_loads_residential)):
            sorted_peaks_residential.append((peak_loads_residential[i],i,'res__SingleFamilyDetached'))
        sorted_peaks_residential = sorted(sorted_peaks_residential)


        # TODO: Scale commercial loads by building footprint.
        sorted_peaks_commercial = {} #Indexed by the customer classes seen in the RNM customer file.
        for key in commercial_categories.keys():
            sorted_peaks_commercial[key] = []
        for building_code in data_commercial.keys():
            for profile in range(data_shape_commercial[building_code][0]):
                d1 = data_commercial[building_code][profile][:][:]
                electricity = sum(d1[i][:] for i in range(len(d1)))
                for hour in range(data_shape_commercial[building_code][2]):
                    peak_loads_commercial[building_code][profile] = max(peak_loads_commercial[building_code][profile],electricity[hour])

                sorted_peaks_commercial[commercial_mapping[building_code]].append((peak_loads_commercial[building_code][profile],profile,building_code))
        for key in sorted_peaks_commercial:
            sorted_peaks_commercial[key] = sorted(sorted_peaks_commercial[key])
        sorted_peaks_commercial['industrial'] = sorted_peaks_commercial['warehouse']
        sorted_peaks_commercial['supermarket'] = sorted_peaks_commercial['stand-alone_retail']
        sorted_peaks_commercial['NA'] = sorted_peaks_commercial['multi-family']

        timeseries_map = {}
        timeseries_category = {}
        timeseries_type = {}

        for row in open(customer_file,'r'):
            split_row = row.split(';') # A csv file delimited by ;
            load_name = split_row[customer_file_headers_index['Identifier']].lower()
            total_p = float(split_row[customer_file_headers_index['peak active power']])
            customer_type = building_types[int(split_row[customer_file_headers_index['building type']])]

            if total_p >0 and customer_type == 'single-family':
                selected_timeseries = 0
                selected_timeseries = sorted_peaks_residential[0][1]
                for i in range(len(sorted_peaks_residential)):
                    if total_p<sorted_peaks_residential[i][0]:
                        break
                    selected_timeseries = sorted_peaks_residential[i][1]
                timeseries_map[load_name] = selected_timeseries
                timeseries_category[load_name] = 'res__SingleFamilyDetached'
                timeseries_type[load_name] = 'residential'
            elif total_p>0 and customer_type in sorted_peaks_commercial:
                selected_timeseries = sorted_peaks_commercial[customer_type][0][1] 
                selected_category = sorted_peaks_commercial[customer_type][0][2]
                for i in range(len(sorted_peaks_commercial[customer_type])):
                    if total_p<sorted_peaks_commercial[customer_type][i][0]:
                        break
                    selected_timeseries = sorted_peaks_commercial[customer_type][i][1] 
                    selected_category = sorted_peaks_commercial[customer_type][i][2]
                timeseries_map[load_name] = selected_timeseries
                timeseries_category[load_name] = selected_category
                timeseries_type[load_name] = 'commercial'


            else:
               logging.warning("Warning - no load type for {name}".format(name=load_name))
               print("Warning - no load type for {name}".format(name=load_name))

        timestamp = hf_res['enumerations']['time'][:]
        written_timeseries = set()
        # Only the loads that are non-zero in the customers_ext files and are single-family or multi-family buildings attach the timeseries
        if write_cyme_file:
            cyme_output = open(os.path.join(output_folder,'cyme_timeseries.txt'),'w')
            cyme_output.write('[PROFILE_VALUES]\n\n')
            cyme_output.write('FORMAT=ID,PROFILETYPE,INTERVALFORMAT,TIMEINTERVAL,GLOBALUNIT,NETWORKID,YEAR,MONTH,DAY,UNIT,PHASE,VALUES\n')

        for load in timeseries_map:

            if 'load_'+load not in model.model_names:
                print(load)
                continue

            profile = timeseries_map[load]
            uuid = metadata_residential['_id'].iloc[timeseries_map[load]]
            timeseries = Timeseries(model)
            timeseries.data_label=timeseries_type[load]+'_'+str(profile)+ '_'+str(timeseries_category[load])
            timeseries.interval = 3600 #Hourly data = 60*60 seconds
            timeseries.data_type = 'float'
            timeseries.scale_factor = 1
            timeseries.data_location = os.path.join(output_folder,timeseries.data_label+'.csv')
            category = timeseries_category[load]

            model['load_'+load].timeseries = [timeseries]
            
            if timeseries.data_label in written_timeseries:
                continue
            if timeseries_type[load] == 'residential':
                d1 = data_residential[profile][:][:]
                timeseries_data = sum(d1[i][:] for i in range(len(d1)))
            if timeseries_type[load] == 'commercial':
                d1 = data_commercial[category][profile][:][:]
                timeseries_data = sum(d1[i][:] for i in range(len(d1)))

            written_timeseries.add(timeseries.data_label)

            # Need to check that datetimes and timeseries_data are the same length
            datetimes = pd.date_range('2012-01-01','2013-01-01',freq='15T')[:-1]
            if write_opendss_file:
                output = pd.DataFrame({'kW':timeseries_data}) #Not including the timestamp in the output
                output.to_csv(timeseries.data_location,header=False,index=False)
            curr_day = -1
            cyme_str = ''
            if write_cyme_file:
                for i in range(len(datetimes)):
                    if curr_day != datetimes[i].day:
                        if curr_day != -1:
                            cyme_str+='\n'
                            cyme_output.write(cyme_str)
                        curr_day = datetimes[i].day
                        cyme_str = ''
                        cyme_str +=timeseries.data_label+','
                        cyme_str+='CUSTOMERTYPE,365DAYS,15MINUTES,%,ALL,'
                        cyme_str+=str(datetimes[i].year)+','
                        cyme_str+=str(datetimes[i].strftime("%B").upper())+','
                        cyme_str+=str(datetimes[i].day)+','
                        cyme_str+='AVERAGEKW,'
                        cyme_str+='TOTAL'
                    cyme_str+=','+str(timeseries_data[i])
    
                cyme_str+='\n'
                cyme_output.write(cyme_str)

        if write_cyme_file:
            cyme_output.close()    

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

    
