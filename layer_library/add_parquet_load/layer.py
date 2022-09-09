from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
from pyathena import connect
from pyathena.pandas_cursor import PandasCursor
import os
import pandas as pd
import random
import multiprocessing
from multiprocessing import Manager
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed, wait
import json

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.load import Load
from ditto.models.phase_load import PhaseLoad
from ditto.models.powertransformer import PowerTransformer
from ditto.models.timeseries import Timeseries
from concurrent.futures import ProcessPoolExecutor, as_completed, wait
import random
import multiprocessing

logger = logging.getLogger('layerstack.layers.Add_Athena_Load')


class Add_Athena_Load(DiTToLayerBase):
    name = "add_athena_load"
    uuid = UUID("1d9885d1-8049-44bd-a1ea-550fa7ab6630")
    version = '0.1.0'
    desc = "Attach timeseries loads from the athena database"

    @classmethod
    def read_parquet(cls, input_arg):
        file_path = input_arg[0]
        count = input_arg[1]

#        name = multiprocessing.current_process().name
#        print(name, 'Starting data read...')
        parquet_data = pd.read_parquet(file_path)
        parquet_data = parquet_data.reset_index()
        res = parquet_data['total_site_electricity_kwh']*4*count #These are stored as kWh loads in the reduced_timeseries parquet files so times by 4
        #print(max(res), file_path)
        return res

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
        kwarg_dict['customer_type_file'] = Kwarg(default=None, description='Detailed breakdown of the customer types from parcel data',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['output_folder'] = Kwarg(default=None, description='location of the csv files to be attached to timeseries models', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['enduse_folder'] = Kwarg(default=None, description='location of the parquet files to be attached to timeseries models', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['cyme_folder'] = Kwarg(default=None, description='location where the cyme file gets written', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['write_cyme_file'] = Kwarg(default=True, description='write the cyme timeseries file', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['write_opendss_file'] = Kwarg(default=True, description='write the many opendss timeseries files', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['residential_folder'] = Kwarg(default=None, description='location of the residential base folder', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['commercial_folder'] = Kwarg(default=None, description='location of the commercial base folder', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['mesh_folder'] = Kwarg(default=None, description='location of the mesh secondary base folder', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['dataset'] = Kwarg(default=None, description='Name of the dataset ( eg. dataset_2,dataset_3 dataset_4) that is being generated',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['year'] = Kwarg(default=None, description='Year from 2016-2018 that is being run',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['copy_files'] = Kwarg(default=True, description='Boolean of whether or not to copy the timeseries profiles for opendss to the output folder',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['scaling_factor_file'] = Kwarg(default=None, description='File used to set tolerances for both res and com. Used mostly for Texas or regions which are overloaded',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['overload_file'] = Kwarg(default=None, description='File used to list nodes which have unacceptable overvoltages which should be reduced',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['region'] = Kwarg(default=None, description='Region that this is for (e.g. P1U). Used for scaling',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    

                

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        residential_folder = kwargs.get('residential_folder',None)
        mesh_folder = kwargs.get('mesh_folder',None)
        commercial_folder = kwargs.get('commercial_folder',None)
        customer_file = kwargs.get('customer_file',None)
        customer_type_file = kwargs.get('customer_type_file',None)
        write_cyme_file = kwargs.get('write_cyme_file',True)
        write_opendss_file = kwargs.get('write_opendss_file',True)
        output_folder = kwargs.get('output_folder','.')
        enduse_folder = kwargs.get('enduse_folder','.')
        cyme_folder = kwargs.get('cyme_folder','.')
        dataset = kwargs.get('dataset',None)
        year = kwargs.get('year',None)
        copy_files = kwargs.get('copy_files',True)
        scaling_factor_file = kwargs.get('scaling_factor_file',None)
        overload_file = kwargs.get('overload_file',None)
        region = kwargs.get('region',None)
        commercial_dataset = 'smartds-multiyear-'+str(year)[-2:]
        commercial_profiles = 'smartds-multiyear-'+str(year)[-2:]
        mesh_profiles = str(year)
        residential_dataset = None
        residential_profiles = None
        all_counties = set()
        all_counties_reduced = set()
        customer_type_map = {}
        peak_season_res = 2
        peak_season_com = 2
        random_seed = 0
        random.seed(0) # for consistency
        expected_kw_cutoff = 2.5
        maximum_kw_cutoff = 5.0

        ###
        # Find the upstream transformer names
        to_element_map = {}
        from_element_map = {}
        for i in model.models:
            if hasattr(i,'from_element'):
                from_element_map[i.from_element] = i
            if hasattr(i,'to_element'):
                to_element_map[i.to_element] = i
        for i in model.models:
            if isinstance(i,Load) and i.nominal_voltage < 1000: #voltage check added to deal with MV loads
                curr_element = i
                to_element = i.connecting_element
                seen = set()
                while not isinstance(curr_element,PowerTransformer):
                    seen.add(to_element)
                    curr_element = to_element_map[to_element]
                    to_element = curr_element.from_element
                    if to_element in seen:
                        to_element = curr_element.to_element
                    if to_element is None or to_element in seen:
                        print('problem with load '+i.name)
                        break
                if isinstance(curr_element,PowerTransformer):
                    i.upstream_transformer_name = curr_element.name
        ####
        
        if dataset == 'dataset_2':
            county = 'NM,SantaFeCounty'
            county_reduced = 'SantaFeCounty'
            residential_dataset = 'SAF_GSO_'+str(year)
            residential_profiles = os.path.join(residential_dataset,'NM')
            all_counties.add(county)
            all_counties_reduced.add(county_reduced)
            peak_season_res = 2
            peak_season_com = 2
        elif dataset == 'dataset_3':
            county = 'NC,GuilfordCounty'
            county_reduced = 'GuilfordCounty'
            residential_dataset = 'SAF_GSO_'+str(year)
            residential_profiles = os.path.join(residential_dataset,'NC')
            all_counties.add(county)
            all_counties_reduced.add(county_reduced)
            peak_season_res = 0 #Peak winter heating loads
            peak_season_com = 2
        elif dataset == 'dataset_4':
            residential_dataset = 'SFO_'+str(year)
            residential_profiles = os.path.join(residential_dataset,'CA')
            for row in open(customer_file,'r'):
                split_row = row.split(';') # A csv file delimited by ;
                county = 'CA,'+split_row[-1].replace('\n','').replace(' ','')+'County'
                county_reduced = split_row[-1].replace('\n','').replace(' ','')+'County'
                all_counties.add(county)
                all_counties_reduced.add(county_reduced)
            peak_season_res = 2
            peak_season_com = 2
        elif dataset == 'Full_Texas' or dataset == 't_and_d':
            residential_dataset = 'TX_'+str(year)
            residential_profiles = os.path.join(residential_dataset,'TX')
            for row in open(customer_file,'r'):
                split_row = row.split(';') # A csv file delimited by ;
                county = 'TX,'+split_row[-1].replace('\n','').replace(' ','')+'County'
                county_reduced = split_row[-1].replace('\n','').replace(' ','')+'County'
                all_counties.add(county)
                all_counties_reduced.add(county_reduced)
            if dataset=='Full_Texas' and customer_type_file is not None:
                for row in open(customer_type_file,'r'):
                    split_row = row.split(';') # A csv file delimited by ;
                    customer_type_name = split_row[0].lower()
                    customer_type_value = split_row[1].lower()
                    customer_type_map[customer_type_name] = customer_type_value

            peak_season_res = 2
            peak_season_com = 2

        counties = list(all_counties)
        counties_reduced= list(all_counties_reduced)

        ercot_data = pd.read_csv(os.path.join(commercial_folder,'texas_mapping.csv'),header=0)
        ercot_counties = set()
        ercot_zone = None
        for idx,row in ercot_data.iterrows():
            if row[0] == region and dataset == 'Full_Texas':
                ercot_zone = row[1].replace(' ','-')
            for i in range(2,len(row)):
                ercot_counties.add(row[i])

        all_states = {'dataset_2':35,'dataset_3': 37,'dataset_4':6,'t_and_d':48,'texas_test':48,'Full_Texas':48}
        fips_data = pd.read_csv(os.path.join(commercial_folder,'all-geocodes-v2016.csv'),header=0,encoding='latin-1')
        fips_data['Area Name']= fips_data['Area Name'].str.replace(' ','')
        reduced_fips = fips_data[fips_data['State Code'] == all_states[dataset]]
        fips_raw = reduced_fips[reduced_fips['Area Name'].isin(counties_reduced)]

        if dataset=='dataset_4':
            fips_raw=reduced_fips #i.e. for Bay area dataset we can use all the California counties (only the SFO ones were generated). For GSO we use only Guilford
#TODO: For Texas counties decide how far away we can use profiles
        fips = []
        for r in fips_raw.iterrows():
            fips.append('G{:02d}0{:03d}0'.format(r[1]['State Code'],r[1]['County Code']))
        fips = set(fips)

        if dataset == 'Full_Texas':
            number_counties = 16
            if region.lower() == 'p5r':
                number_counties = 22 # special case
            centroids = pd.read_csv(os.path.join(commercial_folder,'texas_centroids.csv'),header=0)
            coords = []
            closest_counties = [] # Counties that we'll use
            for county in all_counties_reduced:
                entry = centroids[centroids['County Name'].str.replace(' ','') == county.replace('County','')]
                coords.append( (entry['Longitude'].iloc[0],entry['Latitude'].iloc[0]))
            for idx,row in centroids.iterrows():
                if row['County Name'] not in ercot_counties:
                    continue
                closest_distance = 10000000000000000000000
                closest_county  = None
                closest_gid  = None
                for coord in coords:
                    distance = ((coord[0] - row['Longitude'])**2 + (coord[1] - row['Latitude'])**2)**0.5
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_county = row['County Name']
                        closest_gid = str(row['GID'])
                closest_counties.append((closest_distance,closest_gid,closest_county))
                closest_counties = sorted(closest_counties)
                if len(closest_counties)>number_counties:
                    closest_counties = closest_counties[:number_counties]
            fips = set()
            for entry in closest_counties:
                fips.add('G'+entry[1][:2]+'0'+entry[1][2:]+'0')






        customer_file_headers = ['X', 'Y', 'Z','Identifier', 'voltage level', 'peak active power', 'peak reactive power', 'phases', 'area', 'height', 'energy', 'coincident active power', 'coincident reactive power', 'equivalent users', 'building type', 'Value', 'Year', 'PV capacity', 'Class', 'Rural/Urban','Zone']
        # supermarket, industrial and NA are not supported by ComStock
        building_types = {
                           #0:'industrial', #A HV load
                           0:'warehouse', #A HV load
                           1:'single-family',
                           2:'multi-family',
                           3:'stand-alone_retail',
                           4:'strip_mall',
                           #5:'supermarket',
                           5:'stand-alone_retail',
                           6:'warehouse',
                           7:'hotel',
                           8:'education',
                           9:'office',
                           10:'restaurant',
                           11:'outpatient_healthcare',
                           12:'hospital',
                           #13:'industrial',
                           13:'warehouse',
                           #14:'NA'
                           14:'office'
        }

        residential_mapping = {
                'Multi-Family with 2 - 4 Units':'multi-family',
                'Multi-Family with 5+ Units': 'multi-family',
                'Single-Family Attached':'single-family',
                'Mobile Home': 'single-family',
                'Single-Family Detached':'single-family'
        }

        residential_categories = ['single-family','multi-family']


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
                'full_service_restaurant':'restaurant',
                'hospital':'hospital',
                'large_hotel':'hotel',
                'large_office':'office',
                'medium_office':'office',
                'outpatient':'outpatient_healthcare',
                'primary_school':'education',
                'quick_service_restaurant':'restaurant',
                'retail':'stand-alone_retail',
                'secondary_school':'education',
                'small_hotel':'hotel',
                'small_office':'office',
                'strip_mall':'strip_mall',
                'warehouse':'warehouse'
         }

        commercial_categories = ['industrial','stand-alone_retail','strip_mall','supermarket','warehouse','hotel','education','office','restaurant','outpatient_healthcare','hospital']

        """
        residential_mapping = {
                'single-family':'Single-Family Detached',
                'multi-family':'Multi-Family with 5+ Units'

        }

        commercial_mapping = {
                              'full_service_resteraunt': 'restaurant',
                              'hospital': 'hospital',
                              'large_hotel': 'hotel',
                              'large_office': 'office',
                              'medium_office': 'office',
                              'outpatient': 'outpatient_healthcare',
                              'primary_school': 'education',
                              'quick_service_restaurant': 'restaurant',
                              'retail': 'stand-alone_retail',
                              'secondary_school': 'education',
                              'small_hotel': 'hotel',
                              'small_office': 'office',
                              'strip_mall': 'strip_mall',
                              'warehouse': 'warehouse'
                              }

        """

        model.set_names()
        customer_file_headers_index = {}
        for i in range(len(customer_file_headers)):
            customer_file_headers_index[customer_file_headers[i]] = i

        res_baseline = pd.read_parquet(os.path.join(residential_folder,'raw_data',residential_dataset,'baseline','results_up00.parquet'),engine='pyarrow')
        if dataset != 'dataset_4': #Had problems with counties not having enough variety
            res_baseline = res_baseline[res_baseline['build_existing_model.county'].str.replace(' ','').isin(counties)]
        res_baseline = res_baseline[['building_id','build_existing_model.geometry_building_type_recs']]
        res_peak_loads = None
        res_building_map = None
        res_peak_times = None
        with open(os.path.join(residential_folder,'raw_data',residential_profiles,'building_max.json')) as json_file:
            res_peak_loads = json.load(json_file)
        with open(os.path.join(residential_folder,'raw_data',residential_profiles,'building_peak_times.json')) as json_file:
            res_peak_times = json.load(json_file)
        print('read residential load types')

        com_baseline = pd.read_parquet(os.path.join(commercial_folder,'raw_data',commercial_dataset,'results','parquet','baseline','results_up00.parquet'),engine='pyarrow')
        com_baseline = com_baseline[com_baseline['build_existing_model.county_id'].isin(fips)]
        com_baseline = com_baseline[['building_id','build_existing_model.building_type']]
        com_peak_loads = None
        com_building_map = None
        com_peak_times = None
        with open(os.path.join(commercial_folder,'raw_data',commercial_dataset,'building_max.json')) as json_file:
            com_peak_loads = json.load(json_file)
        with open(os.path.join(commercial_folder,'raw_data',commercial_dataset,'building_peak_times.json')) as json_file:
            com_peak_times = json.load(json_file)
        print('read commercial load types')

        time_periods = 365*24*4

        sorted_peak_loads_residential = {}
        sorted_peak_loads_commercial = {}
        sorted_peak_ratio_abs_exp_residential = {}
        sorted_peak_ratio_abs_exp_commercial = {}

        total_peak = {}
        total_peak_kvar = {}
        timeseries_map = {}
        timeseries_category = {}
        timeseries_type = {}
        seasonal_jsons_com = {}
        seasonal_jsons_res = {}
        for season in range(4):
            with open(os.path.join(residential_folder,'raw_data',residential_profiles,f'season_peak_fortnight_{season}.json')) as json_file:
                seasonal_jsons_res[season] = json.load(json_file)
            with open(os.path.join(commercial_folder,'raw_data',commercial_profiles,f'season_peak_fortnight_{season}.json')) as json_file:
                seasonal_jsons_com[season] = json.load(json_file)

        print('read seasonal information')

        for idx,row in res_baseline.iterrows():
            if not str(row['building_id']) in res_peak_loads or row['build_existing_model.geometry_building_type_recs'] is None :
#                print('None type or no peak load for res '+str(row['building_id']))
                continue
            category = residential_mapping[row['build_existing_model.geometry_building_type_recs']]

            max_load = -1 
            max_skew = -1
            absolute_max_load = res_peak_loads[str(row['building_id'])][0]
            absolute_max_kvar = res_peak_loads[str(row['building_id'])][1]
            max_time_value = res_peak_times[str(row['building_id'])][1]
            for season in range(4):
#                if seasonal_jsons_res[season]['Max day skew expectation'][str(row['building_id'])][1] > max_load:
#                    max_load = seasonal_jsons_res[season]['Max day skew expectation'][str(row['building_id'])][1]
                if seasonal_jsons_res[season]['Max day skew expectation'][str(row['building_id'])][0] > max_skew:
                    max_skew = seasonal_jsons_res[season]['Max day skew expectation'][str(row['building_id'])][0]
            max_load = seasonal_jsons_res[peak_season_res]['Max day skew expectation'][str(row['building_id'])][1] #try using max load from known peak season
            # Add (expected value, skew, absolute max, building_id, absolute max kvar) considering largest skew and largest load even if they're not in the same season (ie being overly careful)
            if category in sorted_peak_loads_residential:
                sorted_peak_loads_residential[category].append((max_load,max_skew,absolute_max_load,row['building_id'],absolute_max_kvar,max_time_value))
                sorted_peak_ratio_abs_exp_residential[category].append(absolute_max_load/max_load)
            else:
                sorted_peak_loads_residential[category] = [(max_load,max_skew,absolute_max_load,row['building_id'],absolute_max_kvar,max_time_value)]
                sorted_peak_ratio_abs_exp_residential[category]=[absolute_max_load/max_load]

        for idx,row in com_baseline.iterrows():
            if not str(row['building_id']) in com_peak_loads or row['build_existing_model.building_type'] is None:
#                print('None type no peak load for com '+str(row['building_id']))
                continue
            category = commercial_mapping[row['build_existing_model.building_type']]
            max_load = -1
            max_skew = -1
            absolute_max_load = com_peak_loads[str(row['building_id'])][0]
            absolute_max_kvar = com_peak_loads[str(row['building_id'])][1]
            max_time_value = com_peak_times[str(row['building_id'])][1]
            for season in range(4):
#                if seasonal_jsons_com[season]['Max day skew expectation'][str(row['building_id'])][1] > max_load:
#                    max_load = seasonal_jsons_com[season]['Max day skew expectation'][str(row['building_id'])][1]
                if seasonal_jsons_com[season]['Max day skew expectation'][str(row['building_id'])][0] > max_skew:
                    max_skew = seasonal_jsons_com[season]['Max day skew expectation'][str(row['building_id'])][0]

            max_load = seasonal_jsons_com[peak_season_com]['Max day skew expectation'][str(row['building_id'])][1] # Try using max load from known peak season
            # Add (expected value, skew, absolute max, building_id, absolute max kvar) considering largest skew and largest load even if they're not in the same season (ie being overly careful)
            if category in sorted_peak_loads_commercial:
                sorted_peak_loads_commercial[category].append((max_time_value,max_skew,absolute_max_load,row['building_id'],absolute_max_kvar,max_load))
                sorted_peak_ratio_abs_exp_commercial[category].append(absolute_max_load/max_load)
            else:
                sorted_peak_loads_commercial[category] = [(max_time_value,max_skew,absolute_max_load,row['building_id'],absolute_max_kvar,max_load)]
                sorted_peak_ratio_abs_exp_commercial[category]=[absolute_max_load/max_load]

        for key in sorted_peak_loads_residential.keys():
            sorted_peak_loads_residential[key] = sorted(sorted_peak_loads_residential[key])
            sorted_peak_ratio_abs_exp_residential[key] = sorted(sorted_peak_ratio_abs_exp_residential[key])

        for key in sorted_peak_loads_commercial.keys():
            sorted_peak_loads_commercial[key] = sorted(sorted_peak_loads_commercial[key])
            sorted_peak_ratio_abs_exp_residential[key] = sorted(sorted_peak_ratio_abs_exp_commercial[key])

       
        #select small commercial loads which have max value less than 5 kW
        small = []
        for key in sorted_peak_loads_commercial:
            for entry in sorted_peak_loads_commercial[key]:
                if entry[0] <= maximum_kw_cutoff or entry[2] <=maximum_kw_cutoff: #if maximum is less than 5kW we assume it's ok to use for "small" commercial
                    small.append(entry)
        if len(small) == 0:
            maximum_kw_cutoff = 11 # increase to 11kW if no small values found
            for key in sorted_peak_loads_commercial:
                for entry in sorted_peak_loads_commercial[key]:
                    if entry[0] <= maximum_kw_cutoff or entry[2] <=maximum_kw_cutoff: #if maximum is less than 5kW we assume it's ok to use for "small" commercial
                        small.append(entry)
        sorted_peak_loads_commercial['small'] = sorted(small)

        peak_res_com = {'Res':0, 'Com':0}
        tolerance = {'Res': 1.0, 'Com': 1.0}# Multiplicative value that residential/commercial loads can exceed planned residential/commercial loads
        if scaling_factor_file is not None and os.path.exists(scaling_factor_file):
            all_scaling_factors = pd.read_csv(scaling_factor_file,header=0)
            scaling_factor = all_scaling_factors[all_scaling_factors['region'] == region]['scaling_factor']
            if len(scaling_factor) ==1:
                print(f'Setting scaling factor to be {scaling_factor.iloc[0]}')
                tolerance = {'Res':scaling_factor.iloc[0], 'Com': scaling_factor.iloc[0]}
        #tolerance = {'Res': 1.05, 'Com': 1.05}# Multiplicative value that residential/commercial loads can exceed planned residential/commercial loads

        all_overloaded_elements = {}
        if overload_file is not None and os.path.exists(overload_file):
            all_overloaded_df = pd.read_csv(overload_file,header=0)
            if len(all_overloaded_df) > 0:
                for idx,row in all_overloaded_df.iterrows():
                    all_overloaded_elements[row['Node']] = row['OpenDSS Value']



        for row in open(customer_file,'r'):
            split_row = row.split(';') # A csv file delimited by ;
            load_name = split_row[customer_file_headers_index['Identifier']].lower()
            model_load_name = 'load_'+load_name
            if model_load_name not in model.model_names:
                print('skipping load of '+load_name+' - not in model')
                continue

            if 'ums' in model_load_name:
                continue
            load_voltage = float(split_row[customer_file_headers_index['voltage level']])
            if load_voltage > 30 and dataset == 'Full_Texas': #Not adding HV loads in distribution
                continue
            coincident_p = float(split_row[customer_file_headers_index['coincident active power']])
            #res_com = split_row[customer_file_headers_index['Class']]

            if dataset != 'dataset_2':
                customer_type = building_types[int(split_row[customer_file_headers_index['building type']])]
            else:
                customer_type = 'single-family' #Don't have any info for dataset 2 so assume they're all residential for now

            if customer_type!='single-family' and customer_type!='multi-family':
                res_com = 'Com'
                if load_name in customer_type_map and ('agricultural'in customer_type_map[load_name] or 'vacant' in customer_type_map[load_name]):
                    res_com = 'Res' # Agricultural uses residential profiles
            else:
                res_com = 'Res'

            if res_com in peak_res_com:
                peak_res_com[res_com] += coincident_p
            else:
                print(f'warning load isnt residential or commercial for {load_name} - value{res_com}')

        for load_type in ['Res','Com']:
            done = False
            multiplicative_factor = 3.05
            while not done:
                if multiplicative_factor<=0.05:
                    multiplicative_factor-=0.01
                elif multiplicative_factor<=0.5:
                    multiplicative_factor-=0.03
                else:
                    multiplicative_factor -= 0.05
                iterative_total = 0 
                coincident_peak_tmp = {}
                timeseries_map_tmp = {}
                timeseries_type_tmp = {}
                total_peak_tmp = {}
                total_peak_kvar_tmp = {}
                expected_transformer_loading = {}

                print(f'mult: {multiplicative_factor} for {load_type}')
                for row in open(customer_file,'r'):
                    split_row = row.split(';') # A csv file delimited by ;
                    load_name = split_row[customer_file_headers_index['Identifier']].lower()
                    model_load_name = 'load_'+load_name
                    if model_load_name not in model.model_names:
                        print('skipping load of '+load_name+' - not in model')
                        continue

                    overload_multiplier = 1.0
                    load_connecting_element = model[model_load_name].connecting_element
                    if 'ums' in model_load_name:
                        timeseries_map_tmp[load_name] = ''
                        timeseries_type_tmp[load_name] = 'mesh'
                        continue
                    load_voltage = float(split_row[customer_file_headers_index['voltage level']])
                    if load_voltage > 30 and dataset == 'Full_Texas': #Not adding HV loads in distribution
                        continue
                    total_p = float(split_row[customer_file_headers_index['peak active power']])
                    coincident_p = float(split_row[customer_file_headers_index['coincident active power']])
                    #res_com = split_row[customer_file_headers_index['Class']]
                    if dataset != 'dataset_2':
                        customer_type = building_types[int(split_row[customer_file_headers_index['building type']])]
                    else:
                        customer_type = 'single-family' #Don't have any info for dataset 2 so assume they're all residential for now
                    if customer_type!='single-family' and customer_type!='multi-family':
                        res_com = 'Com'
                        if load_name in customer_type_map and ('agricultural'in customer_type_map[load_name] or 'vacant' in customer_type_map[load_name]):
                            res_com = 'Res' # Agricultural and vacant types use residential profiles
                            customer_type = 'single-family'
                    else:
                        res_com = 'Res'

                    if load_connecting_element is not None and load_connecting_element in all_overloaded_elements:
                        overload_multiplier = 0.5
                        if res_com == 'Com' and coincident_p<maximum_kw_cutoff:
                            res_com = 'Res' # Smallest commercial loads not small enough
                            customer_type = 'single-family'

                    if res_com != load_type:
                        continue
                    sorted_lookup = None
                    sorted_ratio_lookup = None
                    peak_to_target = None
                    maximum_value_type = None
                    if load_type == 'Res':
                        sorted_lookup = sorted_peak_loads_residential
                        sorted_ratio_lookup = sorted_peak_ratio_abs_exp_residential
                        peak_to_target = coincident_p * overload_multiplier
                        maximum_value_type = 0 # match global peak for each load on absolute maximum if 2 and on expected value if 5 and on load at the peak time if 0
                    elif load_type == 'Com':
                        sorted_lookup = sorted_peak_loads_commercial
                        sorted_ratio_lookup = sorted_peak_ratio_abs_exp_commercial
                        peak_to_target=coincident_p * overload_multiplier
                        maximum_value_type = 0 # match global peak for each load on absolute maximum if 2 and on expected value if 5 and on load at the peak time if 0
                    else:
                        logging.warning("Warning - no load type for {name}".format(name=load_name))
                        print("Warning - no load type for {name}".format(name=load_name))

                    if sorted_lookup is not None:
                        timeseries_index = 0
                        if customer_type in sorted_lookup.keys(): #Should always be true, unless there's a smaller number (eg debugging)
                            i=0
                            reverse_mode=False
                            final_try = False
                            maxed_out = True
                            first_iteration = True #in case this customer class is too big.

                            # Go through timeseries until the expected load exceeds the co-incident load
                            # If the load is skewed and there's already a skewed load on the transformer, 
                            # OR if the load is skewed at the absolute maximum load + expected non-skewed load is greater than the transformer rating
                            # Then go back through the loads until a "safe" load is found
                            # TODO: potential issue if a large skew node gets added first and then lots of non-skew elements get added causing the worst-case loading to be too high
                            while i < len(sorted_lookup[customer_type]):
                                if i<0 and reverse_mode:
                                    if final_try:
                                        i=0
                                        timeseries_index=i
                                        # If peak is less than 2.5 it will be handled elsewhere
                                        if peak_to_target*multiplicative_factor>expected_kw_cutoff:
                                            print(f'Transformer {upstream_transformer} with capacity {transformer_kva} is overloaded or is small with big skew. Using lowest loadshape')
                                            print(f'Problem load is {load_name}: {sorted_lookup[customer_type][i]} of customer class {customer_type} targeting {coincident_p}')
                                            if load_type =='Com':
                                                customer_type = 'office' #These have the lowest values so less risk of problems if it's a hospital
                                        if load_type == 'Res':
                                            print(f'Transformer {upstream_transformer} with capacity {transformer_kva} is overloaded or is small with big skew. Using lowest loadshape')
                                            print(f'Problem load is {load_name}: {sorted_lookup[customer_type][i]} of customer class {customer_type} targeting {coincident_p}')
                                        maxed_out = False
                                        break
                                    else:
                                        final_try = True 
                                        first_iteration = False

                                        #To deal with small loads that have big skews. Because we're in reverse mode it will be allowed to pass the < condition below
                                        i = min(15,len(sorted_lookup[customer_type])-1)
                                        continue


                                load_target = peak_to_target*multiplicative_factor
                                if load_target < sorted_lookup[customer_type][i][maximum_value_type] or reverse_mode:
                                    #if load_name in all_overloaded_elements:
                                    #    import pdb;pdb.set_trace()
                                    nominal_voltage = model['load_'+load_name].nominal_voltage
                                    safe_to_add_c1 = True
                                    safe_to_add_c2 = True
                                    safe_to_add_c3 = True
                                    safe_to_add_c4 = True
                                    safe_to_add_c5 = True
                                    if nominal_voltage < 1000:
                                        upstream_transformer = model['load_'+load_name].upstream_transformer_name
                                        transformer_kva = model[upstream_transformer].windings[0].rated_power/1000
                                        if not upstream_transformer in expected_transformer_loading:
                                            expected_transformer_loading[upstream_transformer] = []
                                        already_skewed = False
                                        transformer_loading = 0
                                        for entry in expected_transformer_loading[upstream_transformer]:
                                            if abs(entry[1]) > 2:
                                                already_skewed = True
                                            transformer_loading += entry[0]
        
                                        # It's safe to add if the following two criterian are met:
                                        # 1) The maximum load + sum of expected loads already attached won't exceed the transformer rating
                                        # 2) There aren't two skewed loads attached to the transformer
                                        # Unused: 3) The multiplicative_factor is less than 0.2 and the skew is greater than 2
                                        # Unused: 4) The multiplicative_factor is less than 0.1 and the skew is greater than 1.3
                                        # 5) The ratio of absolute maximum to expected maximum isn't in the top 5% of ratios over all the profiles 

                                        skew_value = sorted_lookup[customer_type][i][1]
                                        safe_to_add_c1 = transformer_loading + sorted_lookup[customer_type][i][2] <= transformer_kva 

                                        # If we're oversizing the system, we have to allow the transformers to be overloaded
                                        # The find_line_overloads layer will then upgrade the transformers
                                        if multiplicative_factor > 1.15: 
                                            safe_to_add_c1 = True
                                        safe_to_add_c2 = not (already_skewed and skew_value > 2) 
                                        safe_to_add_c3 = not (multiplicative_factor <=0.2 and skew_value > 2)
                                        safe_to_add_c4 = not (multiplicative_factor <=0.1 and skew_value > 1)
                                        if customer_type == 'small':
                                            safe_to_add_c5 = True
                                        else:
                                            safe_to_add_c5 = sorted_lookup[customer_type][i][2]/sorted_lookup[customer_type][i][0] <sorted_ratio_lookup[customer_type][int(len(sorted_ratio_lookup[customer_type])*0.95)]
        
                                    # Medium voltage loads always added since there's no transformer to worry about
                                    if safe_to_add_c1 and safe_to_add_c2 and safe_to_add_c5: 
                                        if nominal_voltage < 1000:
                                            expected_transformer_loading[upstream_transformer].append(sorted_lookup[customer_type][i]) # Add the (expected load,skew,max_load,name, max_load_kvar) to the transformer loading
                                        maxed_out = False
                                        timeseries_index = i
                                        break
                                    elif first_iteration and load_type =='Com':
                                        first_iteration = False
                                        i=0
                                        customer_type = 'office'
                                        #print(f'Problem load of {load_name}: {sorted_lookup[customer_type][i]} of customer class {customer_type} targeting {coincident_p} is reassigned to office')

                                        continue
                                    else:
                                        reverse_mode = True
                                        i -=1
                                        first_iteration = False
                                        continue
                                i+=1
                                first_iteration = False
                            if maxed_out:
                                timeseries_index = len(sorted_lookup[customer_type]) -1

                            #if load_name == 'p2ulv34417':
                            #    import pdb;pdb.set_trace()
                            if load_type == 'Com' and peak_to_target*multiplicative_factor <= expected_kw_cutoff:
                                customer_type='small'
                                timeseries_index = random.randint(0,len(sorted_lookup[customer_type])-1)
                            coincident_peak_tmp[load_name] = coincident_p
                            timeseries_map_tmp[load_name] = sorted_lookup[customer_type][timeseries_index][3] #link unique RNM load name to the building_id of the timeseries we're mapping the load to
                            timeseries_type_tmp[load_name] = load_type.lower()
                            total_peak_tmp[load_name] = sorted_lookup[customer_type][timeseries_index][2] #i.e. the maximum load that occurs at all
                            total_peak_kvar_tmp[load_name] = sorted_lookup[customer_type][timeseries_index][4] #i.e. the maximum load that occurs at all
                            iterative_total+=total_peak_tmp[load_name]
#                            if total_peak[load_name] > coincident_p*1.3:
#                                print(f'Max timeseries load of {total_peak[load_name]} exceeds static planning load of {coincident_p} for customer {load_name} of type {customer_type}')
                        else:
                            print('Customer type ', customer_type,' missing for load ',load_name)
                            raise Exception('Not enough counties')

                total_parquet = None
                building_cnt = {}
                all_names = []
                for load_name in timeseries_map_tmp:
                    if timeseries_map_tmp[load_name] == '':
                        continue
                    if timeseries_map_tmp[load_name] in building_cnt:
                        building_cnt[timeseries_map_tmp[load_name]] +=1
                    else:
                        building_cnt[timeseries_map_tmp[load_name]] =1
                        all_names.append(load_name)

                tst_cnt = 0
                inputs = []
                for building_name in building_cnt:
                    tst_cnt+=1
                    path = None
                    if load_type == 'Res':
                        path = os.path.join(residential_folder,'raw_data',residential_profiles,'reduced_timeseries',f'{building_name}.parquet')
                    if load_type == 'Com':
                        path = os.path.join(commercial_folder,'raw_data',commercial_profiles,'reduced_timeseries',f'{building_name}.parquet')
                    inputs.append((path,building_cnt[building_name])) # Use multiprocessing

                nprocs = int(multiprocessing.cpu_count()*3/4)
                nprocs = 3
                pool = multiprocessing.Pool(processes=nprocs)
                result = pool.map(cls.read_parquet, inputs)
                pool.close()
                pool.join()
                """
                result = []
                for pool_input in inputs:
                    result.append(cls.read_parquet(pool_input))
                """


                max_parquet = 0
                if len(result)>0:
                    total_parquet = result[0]
                    for i in range(1,len(result)):
                        total_parquet+=result[i]
    
                    max_parquet = max(total_parquet) #Mesh secondary excluded

                print(f'{load_type} multiplicative_factor of {multiplicative_factor:.3f} of expected loads')
                print(f'Maximum for type {load_type}: {max_parquet/1000:.3f} MW')
                print(f'Static peak for type {load_type}: {peak_res_com[load_type]/1000:.3f} MW',flush=True)
                if max_parquet <= tolerance[load_type] * peak_res_com[load_type] or multiplicative_factor <= 0.01:
                    if multiplicative_factor < 0.2:
                        print('Multiplicative factor too low. Using what we have')
                    timeseries_map.update(timeseries_map_tmp)
                    timeseries_type.update(timeseries_type_tmp)
                    total_peak.update(total_peak_tmp)
                    total_peak_kvar.update(total_peak_kvar_tmp)
                    print(f'{load_type} multiplicative_factor of {multiplicative_factor:.3f} of expected loads')
                    print(f'Maximum for type {load_type}: {max_parquet/1000:.3f} MW')
                    print(f'Static peak for type {load_type}: {peak_res_com[load_type]/1000:.3f} MW')
                    done = True
                # NOTE: in this version of the model we are NOT including the customer classes in the output since this would idenfity individual information provided in the parcel data about customer type and category
                # The only real way to back out whether it's a commercial or residential customer is based on the load and/or solar pattern. But we're not providing that explicitly

        if write_cyme_file:
            cyme_output = open(os.path.join(cyme_folder,'cyme_load_timeseries.txt'),'w')
            cyme_output.write('[PROFILE_VALUES]\n\n')
            cyme_output.write('FORMAT=ID,PROFILETYPE,INTERVALFORMAT,TIMEINTERVAL,GLOBALUNIT,NETWORKID,YEAR,MONTH,DAY,UNIT,PHASE,VALUES\n')

            
        written_timeseries = set()

        print('Starting to copy files to output location')
        all_timeseries_profiles = {} #used for writing to CYME
        for load in timeseries_map:

            if 'load_'+load not in model.model_names:
                print('problem connecting '+load)
                continue

            profile = timeseries_map[load]
            if profile !='':
                profile = '_'+str(profile)

            profile_with_zone = profile
            if ercot_zone is not None and dataset == 'Full_Texas':
                profile_with_zone = profile +'-'+ercot_zone

            timeseries = Timeseries(model)
            timeseries.feeder_name = model['load_'+load].feeder_name
            timeseries.substation_name = model['load_'+load].substation_name
            timeseries.data_label=timeseries_type[load]+str(profile_with_zone) #Previous version also added the category here as well
            timeseries.interval = 0.25 #15 minute data provided - need to specify (modified from previous version)
            timeseries.data_type = 'float'
            timeseries.scale_factor = 1
            kw_location = timeseries_type[load]+'_kw'+str(profile_with_zone)
            kvar_location = timeseries_type[load]+'_kvar'+str(profile_with_zone)
            timeseries.data_location = os.path.join(output_folder,kw_location+'_pu.csv')
            timeseries.data_location_kvar = os.path.join(output_folder,kvar_location+'_pu.csv')
            unscaled_location = os.path.join(output_folder,kw_location+'.csv') 

            

            model['load_'+load].timeseries = [timeseries]

            
            res_com = None
            res_com_folder = None
            res_com_enduses = None
            if timeseries_type[load] == 'res':
                res_com = 'res'
                res_com_folder = os.path.join(residential_folder,'residential_profiles',residential_profiles)
                res_com_enduses = os.path.join(residential_folder, 'raw_data',residential_profiles,'enduses')
            if timeseries_type[load] == 'com':
                res_com = 'com'
                res_com_folder = os.path.join(commercial_folder,'commercial_profiles',commercial_profiles)
                res_com_enduses = os.path.join(commercial_folder, 'raw_data',commercial_profiles,'enduses')

            if timeseries_type[load] == 'mesh':
                res_com = 'mesh'
                res_com_folder = os.path.join(mesh_folder,mesh_profiles)
                res_com_enduses = os.path.join(mesh_folder,mesh_profiles)

                mesh_info = pd.read_parquet(os.path.join(mesh_folder,mesh_profiles,'mesh.parquet'))
                mesh_kw = mesh_info['total_site_electricity_kw']
                mesh_max_index = mesh_kw.idxmax()
                total_peak[load] = mesh_info.loc[mesh_max_index,'total_site_electricity_kw']
                total_peak_kvar[load] = mesh_info.loc[mesh_max_index,'total_site_electricity_kvar']
            # Set the loads to be the Absolute PEAK load instead of the co-incident peak. The multiplicative timeseries multiplies by the max peak value.
            for pl in model['load_'+load].phase_loads:
                #pl.p = pl.p/(coincident_peak[load])
                pl.p = 1000*total_peak[load]/len(model['load_'+load].phase_loads)
                pl.q = 1000*total_peak_kvar[load]/len(model['load_'+load].phase_loads)



            if write_cyme_file: #Requires profiles to already be there (i.e. DSS conversion must be run first)
                if not timeseries.data_label in all_timeseries_profiles:
                    timeseries_data = pd.read_csv(os.path.join(res_com_folder,res_com+'_kw'+str(profile)+'_pu.csv'),header=None)
                    all_timeseries_profiles[timeseries.data_label] = timeseries_data



            if timeseries.data_label in written_timeseries:
                continue



            # TODO: check the timeseries values match up
            # Note that we need to scale by the co-incident peak for this to make sense since the peak value in the loads is the co-incident peak
            # simultanaiety factor is 0.4 for LV an 0.8 for MV loads
            written_timeseries.add(timeseries.data_label)

            next_year = int(year)+1
            datetimes = pd.date_range(f'{year}-01-01',f'{next_year}-01-01',freq='15T')[:-1]
            if int(year) == 2016:
                datetimes = pd.date_range(f'{year}-01-01',f'{year}-12-31',freq='15T')[:-1] # Truncate a day early if a leap year so still has 365 days

            if write_opendss_file and copy_files:
                if res_com == 'mesh':
                    profile_output = ''
                if not os.path.exists(os.path.join(output_folder,res_com+'_kw'+str(profile_with_zone)+'_pu.csv')):
                    shutil.copyfile(os.path.join(res_com_folder,res_com+'_kw'+str(profile)+'_pu.csv'),os.path.join(output_folder,res_com+'_kw'+str(profile_with_zone)+'_pu.csv'))
                if not os.path.exists(os.path.join(output_folder,res_com+'_kvar'+str(profile)+'_pu.csv')):
                    shutil.copyfile(os.path.join(res_com_folder,res_com+'_kvar'+str(profile)+'_pu.csv'),os.path.join(output_folder,res_com+'_kvar'+str(profile_with_zone)+'_pu.csv'))


#                if not os.path.exists(os.path.join(output_folder,res_com+'_kw'+str(profile)+'.csv')):
#                    shutil.copyfile(os.path.join(res_com_folder,res_com+'_kw'+str(profile)+'.csv'),os.path.join(output_folder,res_com+'_kw'+str(profile)+'.csv'))
#                if not os.path.exists(os.path.join(output_folder,res_com+'_kvar'+str(profile)+'.csv')):
#                    shutil.copyfile(os.path.join(res_com_folder,res_com+'_kvar'+str(profile)+'.csv'),os.path.join(output_folder,res_com+'_kvar'+str(profile)+'.csv'))
#                if not os.path.exists(os.path.join(output_folder,res_com+'_pf'+str(profile)+'.csv')):
#                    shutil.copyfile(os.path.join(res_com_folder,res_com+'_pf'+str(profile)+'.csv'),os.path.join(output_folder,res_com+'_pf'+str(profile)+'.csv'))


                profile_output2 = profile.strip('_')
                if res_com == 'mesh':
                    profile_output2 = 'mesh'
                if not os.path.exists(os.path.join(enduse_folder,res_com+str(profile_with_zone)+'.parquet')):
                    shutil.copyfile(os.path.join(res_com_enduses,str(profile_output2)+'.parquet'),os.path.join(enduse_folder,res_com+str(profile_with_zone)+'.parquet'))



            curr_day = -1
            cyme_str = ''
            if write_cyme_file:
                all_timeseries = {}
                timeseries_data_string = list(all_timeseries_profiles[timeseries.data_label][0]*100) #We output percentages so use p.u. values and multiply by 100
                timeseries_data_string = [f'{entry:.4f}' for entry in timeseries_data_string]
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
                        cyme_str+='%,'
                        cyme_str+='TOTAL'
                    if i < len(timeseries_data_string):
                        cyme_str+=','+timeseries_data_string[i]
    
                cyme_str+='\n'
                cyme_output.write(cyme_str)

        if write_cyme_file:
            cyme_output.close() 
            all_fps = []
            for i in range(1,366):
                all_fps.append(open(os.path.join(cyme_folder,f'cyme_load_timeseries_day_{i}.txt'),'w'))
                all_fps[-1].write('[PROFILE_VALUES]\n\n')
                all_fps[-1].write('FORMAT=ID,PROFILETYPE,INTERVALFORMAT,TIMEINTERVAL,GLOBALUNIT,NETWORKID,YEAR,MONTH,DAY,UNIT,PHASE,VALUES\n')

            line_cnt = -1
            day_count = 0
            with open(os.path.join(cyme_folder,'cyme_load_timeseries.txt'),'r') as all_cyme:
                for row in all_cyme.readlines():
                    line_cnt+=1
                    if line_cnt < 3:
                        continue
                    if day_count%365 ==0:
                        day_count = 0
                    all_fps[day_count].write(row)
                    day_count+=1

            for i in range(len(all_fps)):
                all_fps[i].close()
            os.remove(os.path.join(cyme_folder,'cyme_load_timeseries.txt')) #Don't want to save the full file.

        print('finished timseries load layer')
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Add_Athena_Load.main()

    
