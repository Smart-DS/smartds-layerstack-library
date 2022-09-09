from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import pandas as pd
import math
import pyproj
import os
import random
import zipfile
import requests
import shutil
import time
import PySAM.Pvwattsv7 as pvwatts
from rex import NSRDBX
import h5py

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.timeseries import Timeseries
from ditto.models.photovoltaic import Photovoltaic

logger = logging.getLogger('layerstack.layers.Connect_Solar_Timeseries')


class Connect_Solar_Timeseries(DiTToLayerBase):
    name = "connect_solar_timeseries"
    uuid = UUID("5cdbde06-9b42-458c-9929-7254eba80d00")
    version = '0.1.0'
    desc = "Attach timeseries data to all the solar locations based on their coordinates"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['solar_scenario'] = Kwarg(default=None, description='none, low, medium, high or extreme. If none than we skip',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['dataset'] = Kwarg(default=None, description='Dataset being used. Important for the projection',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['year'] = Kwarg(default=None, description='Timeseries year',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['base_folder'] = Kwarg(default=None, description='Location of the solar data.',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['customer_file'] = Kwarg(default=None, description='Customer file. Used to find counties being used for Texas',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['output_folder'] = Kwarg(default=None, description='location of the csv files to be attached to timeseries models', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['full_solar_folder'] = Kwarg(default=None, description='location of the csv files for the full solar output', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['cyme_output_folder'] = Kwarg(default=None, description='location of the csv files to be attached to cyme timeseries models', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['write_cyme_file'] = Kwarg(default=True, description='write the cyme timeseries file', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['write_opendss_file'] = Kwarg(default=True, description='write the many opendss timeseries files', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        dataset = None
        base_folder = None
        output_folder = None
        write_opendss_file = False
        write_cyme_file = False
        year = 'peak'
        solar_scenario = 'none'
        if 'solar_scenario' in kwargs:
            solar_scenario = kwargs['solar_scenario']
        if 'dataset' in kwargs:
            dataset = kwargs['dataset']
        if 'year' in kwargs:
            year = kwargs['year']
        if 'base_folder' in kwargs:
            base_folder = kwargs['base_folder']
        if dataset is None or base_folder is None:
            return model
        if 'output_folder' in kwargs:
            output_folder = kwargs['output_folder']
        if 'full_solar_folder' in kwargs:
            full_solar_folder = kwargs['full_solar_folder']
        if 'cyme_output_folder' in kwargs:
            cyme_output_folder = kwargs['cyme_output_folder']
        if 'write_opendss_file' in kwargs:
            write_opendss_file = kwargs['write_opendss_file']
        if 'write_cyme_file' in kwargs:
            write_cyme_file = kwargs['write_cyme_file']
        if 'customer_file' in kwargs:
            customer_file = kwargs['customer_file']
        if output_folder is None:
            output_folder = '.'

        if solar_scenario == 'none':
            return model

        all_counties = set()
        if dataset == 'dataset_4':
            all_counties.add('sanfrancisco')
        if dataset == 'dataset_3':
            all_counties.add('guilford')
        if dataset == 'dataset_2':
            all_counties.add('santafe')
        if dataset == 't_and_d':
            all_counties.add('travis')

        if dataset == 'Full_Texas':
            for row in open(customer_file,'r'):
                split_row = row.split(';') # A csv file delimited by ;
                county = split_row[-1].replace('\n','')
                all_counties.add(county.lower())


        folder = {'dataset_4':'SFO', 'dataset_3':'GSO', 'dataset_2': 'SAF','t_and_d':'AUS','Full_Texas':'Full_Texas'} #NOTE: currently using tilt profiles for Santa Fe in Texas
        projection = {'dataset_4':'epsg:32610', 'dataset_3':'epsg:32617', 'dataset_2':'epsg:32613','t_and_d':'epsg:32614','Full_Texas':'epsg:32614'}
        mapped_locations = set()
        all_coords = []
        azimuth_map = {'N':0, 'NE':45, 'E':90, 'SE':135, 'S':180, 'SW':225, 'W': 270, 'NW':315}
        res_tilt_azimuth = {'small':{}, 'medium':{}, 'large':{}}  #map each tilt_azimuth pair to a counter to build distribution of tilts partitioned by size
        res_tilt_azimuth_total = {'small':0, 'medium':0, 'large':0}
        com_tilt_azimuth = {'small':{}, 'medium':{}, 'large':{}}  #map each tilt_azimuth pair to a counter to build distribution of tilts partitioned by size
        com_tilt_azimuth_total = {'small':0, 'medium':0, 'large':0}
        if dataset =='t_and_d' or dataset == 'Full_Texas':
            solar_tilts = pd.read_csv(os.path.join(base_folder,'texas_counties_rooftop_solar_characteristics.csv'))
        else:
            solar_tilts = pd.read_csv(os.path.join(base_folder,'rooftop_solar_characteristics.csv'))

        all_nsrdb = set()

        all_tilts = set()
        for idx,row in solar_tilts.iterrows():
            if row['county'].lower().replace(' ','') in all_counties:
                size = row['size_class']
                azimuth = azimuth_map[row['azimuth']]
                tilt = row['tilt']
                zone = row['zone']
                all_tilts.add((azimuth,tilt))
                if zone == 'residential':
                    if (azimuth,tilt) in res_tilt_azimuth[size]:
                        res_tilt_azimuth[size][(azimuth,tilt)] = res_tilt_azimuth[size][(azimuth,tilt)]+1
                    else:
                        res_tilt_azimuth[size][(azimuth,tilt)] = 1
                    res_tilt_azimuth_total[size] +=1
                else:
                    if (azimuth,tilt) in com_tilt_azimuth[size]:
                        com_tilt_azimuth[size][(azimuth,tilt)] = com_tilt_azimuth[size][(azimuth,tilt)]+1
                    else:
                        com_tilt_azimuth[size][(azimuth,tilt)] = 1
                    com_tilt_azimuth_total[size] +=1

        all_res_tilts = {'small':[], 'medium':[], 'large':[]}
        all_res_p = {'small':[], 'medium':[], 'large':[]} #The percentage /100 of that tilt/azimuth combination for each size
        all_com_tilts = {'small':[], 'medium':[], 'large':[]}
        all_com_p = {'small':[], 'medium':[], 'large':[]}
        for size in com_tilt_azimuth.keys():
            for orientation in com_tilt_azimuth[size]:
                all_com_p[size].append(com_tilt_azimuth[size][orientation]/float(com_tilt_azimuth_total[size]))
                all_com_tilts[size].append(orientation)
            for orientation in res_tilt_azimuth[size]:
                all_res_p[size].append(res_tilt_azimuth[size][orientation]/float(res_tilt_azimuth_total[size]))
                all_res_tilts[size].append(orientation)


        all_tilts = sorted(list(all_tilts))
        invproj = pyproj.Proj(init=projection[dataset],preserve_units=True) 

        min_long = 100000
        min_lat = 1000000
        max_long = -100000
        max_lat = -100000

        for i in model.models:
            if hasattr(i,'positions') and i.positions is not None and len(i.positions) >0:
                x = i.positions[0].lat
                y = i.positions[0].long
                lat_long = invproj(y,x,inverse=True)
                i_lat = lat_long[1]
                i_long = lat_long[0]
                if i_long < min_long:
                    min_long = i_long
                if i_long > max_long:
                    max_long = i_long
                if i_lat < min_lat:
                    min_lat = i_lat
                if i_lat > max_lat:
                    max_lat = i_lat

        from geopy.distance import great_circle
        total_x = great_circle((min_lat,min_long),(min_lat,max_long)).km # distance along the top of square
        total_y = great_circle((min_lat,min_long),(max_lat,min_long)).km # distance along the left of square

        delta_lat = 4.1 *(max_lat-min_lat)/total_y #4.1 km accross in latitudes
        delta_long = 4.1 *(max_long-min_long)/total_x# 4.1 km
        x=0
        y=0
        while min_long + x*delta_long <= max_long:
            while min_lat + y*delta_lat <= max_lat:
                all_coords.append((min_long+x*delta_long, min_lat+y*delta_lat))
                y+=1
            x+=1



        """    
        for csv_file in os.listdir(os.path.join(base_folder,folder[dataset])): #reads the folders that contain the csv files. Shows the coords for each dataset
            vals = csv_file.split('_')
            clat = vals[0]
            clong = vals[1]
            all_coords.append((clat,clong))
        """

        
        all_seen = set()
        all_profiles = {}
        for location in os.listdir(full_solar_folder):
            if location.startswith(folder[dataset]):
                seen_lat = location.split('_')[1]
                seen_long = location.split('_')[2]
                all_seen.add((seen_lat,seen_long))
                

        """
        url = f"https://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv?api_key={api_key}"
        attributes = 'clearsky_ghi%2Cclearsky_dhi%2Cclearsky_dni%2Cghi%2Cdhi%2Cdni%2Cwind_speed%2Cair_temperature%2Csolar_zenith_angle'
        year = str(year)
        leap_year = 'true' # Remove afterwards
        interval = '30'
        if year == '2018':
            interval = '15'
            url = f"https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-5min-download.json?api_key={api_key}"
        utc = 'false'
        your_name = 'Tarek+Elgindy'
        reason_for_use = 'smartds'
        your_affiliation = 'nrel'
        your_email = 'no-reply@nrel.gov'
        mailing_list = 'false'
        for coord in all_coords:
            time.sleep(2)
            lon = coord[0]
            lat = coord[1]
            lat = f'{lat:.4f}'
            lon = f'{lon:.4f}'

            if (lat,lon) in all_seen: #Reduce number of queries in case it was pulled through another scenario
                for az_tilt in all_tilts:
                    result = pd.read_csv(os.path.join(output_folder,folder[dataset]+'_'+lat+'_'+lon+'_'+str(az_tilt[1])+'_'+str(az_tilt[0])+'_full.csv'),header=0)
                    all_profiles[(az_tilt[0],az_tilt[1],lat,lon)] = result
                continue

            payload = f"&names={year}&leap_day={leap_year}&interval={interval}&utc={utc}&full_name={your_name}&email={your_email}&affiliation={your_affiliation}&mailing_list={mailing_list}&reason={reason_for_use}&attributes={attributes}&wkt=POINT({lon}%20{lat})"
    
            headers = {
                'content-type': "application/x-www-form-urlencoded",
                'cache-control': "no-cache"
            }
            if year == '2018':
                response = requests.request("GET", url+payload, headers=headers)
                j_response = response.json()
                #print(j_response)
                try_count = 0
                ok = True
                while not ('status' in j_response and j_response['status'] == 200): 
                    print(j_response['errors'])
                    if try_count >= 20:
                        ok = False
                        break
            
                    try_count+=1
                    time.sleep(2)
                    response = requests.request("GET", url+payload, headers=headers)
                    j_response = response.json()
                if not ok:
                    print('Timeout on coordinate '+coord)
                    continue
    
                download = j_response['outputs']['downloadUrl']
                all_nsrdb.add((download,lat,lon))
                print(download)
        
            else:
                all_nsrdb.add((url+payload,lat,lon))


        # INSERT TEST3 CODE IN HERE WITH ALL DIFFERENT TILTS/AZIMUTHS

        time.sleep(30) #wait for a bit before downloading
        periods = int(365*24*60/int(interval) )
        for download,lat,lon in all_nsrdb:
            if year == '2018':
                uuid = download.split('/')[-1].split('.')[0]
                r = requests.get(download, stream=True)
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall()
                for f in os.listdir(uuid):
                    info = pd.read_csv(os.path.join(uuid,f),nrows=1)
                    df = pd.read_csv(os.path.join(uuid,f),skiprows=2)
                    print(info)
                    print(df)
                shutil.rmtree(uuid)
            else:
                info = pd.read_csv(download,nrows=1)
                df = pd.read_csv(download,skiprows=2)
        
        
            if year == '2016':
                df = df[:periods]
            df = df.set_index(pd.date_range('1/1/{yr}'.format(yr=2018), freq=interval+'Min', periods=periods)) #Use 2018 to avoid leap year issues
        
            df = df.asfreq('15min').interpolate()
        
            for idx,row in df.iterrows():
                if int(row['Hour'])!=row['Hour']:
                    row['Minute'] = 45.0
                    row['Hour'] = float(int(row['Hour']))
                if int(row['Day'])!=row['Day']:
                    row['Hour'] = 23.0
                    row['Day'] = float(int(row['Day']))
                if int(row['Month'])!=row['Month']:
                    row['Hour'] = 23.0
                    row['Day'] = row['Day']*2-1
                    row['Month'] = float(int(row['Month']))
        
            last_row = str(df.iloc[len(df)-1].name)
            last_row_updated= pd.Timestamp(str(df.iloc[len(df)-1].name).replace(':30:',':45:'))
            df.loc[last_row_updated] = df.loc[last_row]
            df.loc[last_row_updated]['Minute'] = 45.0
            df['Minute'] = df['Minute'].astype(int)
            df['Hour'] = df['Hour'].astype(int)
            df ['Day'] = df['Day'].astype(int)
            df['Month'] = df['Month'].astype(int)
            df['Year'] = df['Year'].astype(int)
        
            timezone, elevation = info['Local Time Zone'], info['Elevation']
        
            solar_resource_data = {
                'tz': timezone, # timezone
                'elev': elevation, # elevation
                'lat': float(lat), # latitude
                'lon': float(lon), # longitude
                'year': tuple(df['Year']), # year is correct in df
                'month': tuple(df.index.month), # month use index since shifting happens for leap year
                'day': tuple(df.index.day), # day use index since shifting happens for leap year
                'hour': tuple(df.index.hour), # hour
                'minute': tuple(df.index.minute), # minute
                'dn': tuple(df['DNI']), # direct normal irradiance
                'df': tuple(df['DHI']), # diffuse irradiance
                'gh': tuple(df['GHI']), # global horizontal irradiance
                'wspd': tuple(df['Wind Speed']), # windspeed
                'tdry': tuple(df['Temperature']) # dry bulb temperature
            }

            for az_tilt in all_tilts:
        
                model_params = {
                    "SystemDesign": {
                        "array_type": 1.0,
                        "azimuth": az_tilt[0],
                        "tilt": az_tilt[1],
                        "dc_ac_ratio": 1.08,
                        "gcr": 0.592,
                        "inv_eff": 97.5,
                        "losses": 15.53,
                        "module_type": 0,
                        "system_capacity": 1000 # Use 1000 kW array
                    },
                    "SolarResource": {
                    }
                }
        
                    
                system_model = pvwatts.new()
                system_model.assign(model_params)
            
                system_model.SolarResource.assign({'solar_resource_data': solar_resource_data})
                system_model.AdjustmentFactors.assign({'constant': 0})
                
                system_model.execute()
                out = system_model.Outputs.export()
                poa = pd.DataFrame(out['poa'])
                gen = pd.DataFrame(out['gen'])
                result = df.copy(deep=True)
    
                result['PoA Irradiance (W/m^2)'] = poa[0].to_list()
                result['kW Generated (1000 kW Array)'] = gen[0].to_list()
                result = result.round(2)
                all_profiles[(az_tilt[0],az_tilt[1],lat,lon)] = result

        """

        year = str(year)
        interval = '30'
        periods = int(365*24*60/int(interval) )
        nsrdb_file = f'/datasets/NSRDB/v3/nsrdb_{year}.h5'

        with NSRDBX(nsrdb_file, hsds=False) as input_nsrdb:
            for coord in all_coords:
                lon = coord[0]
                lat = coord[1]
                lat = f'{lat:.4f}'
                lon = f'{lon:.4f}'
                print(lat,lon)
                if (lat,lon) in all_seen: #Reduce number of queries in case it was pulled through another scenario
                    for az_tilt in all_tilts:
                        result = pd.read_csv(os.path.join(full_solar_folder,folder[dataset]+'_'+lat+'_'+lon+'_'+str(az_tilt[1])+'_'+str(az_tilt[0])+'_full.csv'),header=0)
                        all_profiles[(az_tilt[0],az_tilt[1],lat,lon)] = result
                    continue
    
                coord_round = (float(lat),float(lon))
                df = input_nsrdb.get_SAM_lat_lon(coord_round) #Warning - I've modified the renewable_resource.py file in the rex installation in miniconda to include GHI as well.
                gid = input_nsrdb.lat_lon_gid(coord_round)
                timezone = None
                elevation = None
                with h5py.File(nsrdb_file,'r') as h5data:
                    metadata = h5data['meta'][gid]
                    elevation = metadata[2]
                    timezone = metadata[3]
                if year == '2016':
                    df = df[:periods]
                df = df.set_index(pd.date_range('1/1/{yr}'.format(yr=2018), freq=interval+'Min', periods=periods)) #Use 2018 to avoid leap year issues
            
                df = df.asfreq('15min').interpolate()
            
                for idx,row in df.iterrows():
                    if int(row['Hour'])!=row['Hour']:
                        df.loc[idx,'Minute'] = 45.0
                        df.loc[idx,'Hour'] = float(int(row['Hour']))
                    if int(row['Day'])!=row['Day']:
                        df.loc[idx,'Hour'] = 23.0
                        df.loc[idx,'Day'] = float(int(row['Day']))
                    if int(row['Month'])!=row['Month']:
                        df.loc[idx,'Hour'] = 23.0
                        df.loc[idx,'Day'] = row['Day']*2-1
                        df.loc[idx,'Month'] = float(int(row['Month']))
            
                last_row = str(df.iloc[len(df)-1].name)
                last_row_updated= pd.Timestamp(str(df.iloc[len(df)-1].name).replace(':30:',':45:'))
                df.loc[last_row_updated] = df.loc[last_row]
                df.loc[last_row_updated]['Minute'] = 45.0
                df['Minute'] = df['Minute'].astype(int)
                df['Hour'] = df['Hour'].astype(int)
                df ['Day'] = df['Day'].astype(int)
                df['Month'] = df['Month'].astype(int)
                df['Year'] = df['Year'].astype(int)
            
            
                solar_resource_data = {
                    'tz': timezone, # timezone
                    'elev': elevation, # elevation
                    'lat': float(lat), # latitude
                    'lon': float(lon), # longitude
                    'year': tuple(df['Year']), # year is correct in df
                    'month': tuple(df.index.month), # month use index since shifting happens for leap year
                    'day': tuple(df.index.day), # day use index since shifting happens for leap year
                    'hour': tuple(df.index.hour), # hour
                    'minute': tuple(df.index.minute), # minute
                    'dn': tuple(df['DNI']), # direct normal irradiance
                    'df': tuple(df['DHI']), # diffuse irradiance
                    'gh': tuple(df['GHI']), # global horizontal irradiance
                    'wspd': tuple(df['Wind Speed']), # windspeed
                    'tdry': tuple(df['Temperature']) # dry bulb temperature
                }
    
                for az_tilt in all_tilts:
            
                    model_params = {
                        "SystemDesign": {
                            "array_type": 1.0,
                            "azimuth": az_tilt[0],
                            "tilt": az_tilt[1],
                            "dc_ac_ratio": 1.08,
                            "gcr": 0.592,
                            "inv_eff": 97.5,
                            "losses": 15.53,
                            "module_type": 0,
                            "system_capacity": 1000 # Use 1000 kW array
                        },
                        "SolarResource": {
                        }
                    }
            
                        
                    system_model = pvwatts.new()
                    system_model.assign(model_params)
                
                    system_model.SolarResource.assign({'solar_resource_data': solar_resource_data})
                    system_model.AdjustmentFactors.assign({'constant': 0})
                    
                    system_model.execute()
                    out = system_model.Outputs.export()
                    poa = pd.DataFrame(out['poa'])
                    gen = pd.DataFrame(out['gen'])
                    result = df.copy(deep=True)
        
                    result['PoA Irradiance (W/m^2)'] = poa[0].to_list()
                    result['kW Generated (1000 kW Array)'] = gen[0].to_list()
                    result = result.round(2)
                    all_profiles[(az_tilt[0],az_tilt[1],lat,lon)] = result




        random.seed(0)


        for key in all_profiles:
            solar_profile = all_profiles[key]
            az = key[0]
            tilt = key[1]
            lat = key[2]
            lon = key[3]
            data_location = os.path.join(full_solar_folder,folder[dataset]+'_'+lat+'_'+lon+'_'+str(tilt)+'_'+str(az)+'_full.csv')
            if not os.path.exists(data_location):
                solar_profile.to_csv(data_location,index=False,header=True)

        #import pdb;pdb.set_trace()
        if write_cyme_file:

#            cyme_output = open(os.path.join(cyme_output_folder,'cyme_solar_timeseries.txt'),'w')
#            cyme_output.write('[PROFILE_VALUES]\n\n')
#            cyme_output.write('FORMAT=ID,PROFILETYPE,INTERVALFORMAT,TIMEINTERVAL,GLOBALUNIT,NETWORKID,YEAR,MONTH,DAY,UNIT,PHASE,VALUES\n')

            next_year = int(year)+1
            datetimes = pd.date_range(f'{year}-01-01',f'{next_year}-01-01',freq='15T')[:-1]
            if int(year) == 2016:
                datetimes = pd.date_range(f'{year}-01-01',f'{year}-12-31',freq='15T')[:-1] # Truncate a day early if a leap year so still has 365 days

            all_fps = []
            for i in range(1,366):
                all_fps.append(open(os.path.join(cyme_output_folder,f'cyme_solar_timeseries_day_{i}.txt'),'w'))
                all_fps[-1].write('[PROFILE_VALUES]\n\n')
                all_fps[-1].write('FORMAT=ID,PROFILETYPE,INTERVALFORMAT,TIMEINTERVAL,GLOBALUNIT,NETWORKID,YEAR,MONTH,DAY,UNIT,PHASE,VALUES\n')

        for i in model.models:
            if isinstance(i,Photovoltaic):
                x=None
                y=None
                if hasattr(i,'positions') and i.positions is not None and len(i.positions) > 0:
                    x = i.positions[0].lat
                    y = i.positions[0].long
                elif hasattr(i,'connecting_element') and i.connecting_element is not None and i.connecting_element in model.model_names:
                    connecting_element = model[i.connecting_element]
                    if hasattr(connecting_element,'positions') and connecting_element.positions is not None and len(connecting_element.positions) > 0:
                        x = connecting_element.positions[0].lat
                        y = connecting_element.positions[0].long
                if x == None or y == None:
                    print('Warning: No solar attached for object '+i.name)
                    continue

                lat_long = invproj(y,x,inverse=True)
                i_lat = lat_long[1]
                i_long = lat_long[0]

                best_dist = float('inf')
                closest_lat = ''
                closest_long = ''
                for coords in all_coords:
                    dist = math.sqrt((i_long-float(coords[0]))**2 + (i_lat-float(coords[1]))**2)
                    if dist < best_dist:
                        best_dist = dist
                        closest_long = coords[0]
                        closest_lat = coords[1]
                        closest_long = f'{closest_long:.4f}'
                        closest_lat = f'{closest_lat:.4f}'


                kw = i.rated_power
                customer_class = i.customer_class
                az_tilt = None
                if customer_class == 'residential':
                    if kw < 5000:
                        size='small'
                    elif kw<8000:
                        size='medium'
                    else:
                        size='large'
                    az_tilt = random.choices(all_res_tilts[size],weights=all_res_p[size])[0]
                else:
                    if kw<8000:
                        size='small'
                    elif kw < 100000:
                        size='medium'
                    else:
                        size='large'
                    az_tilt = random.choices(all_com_tilts[size],weights=all_com_p[size])[0]
                timeseries = Timeseries(model)
                #print(az_tilt)
                timeseries.data_label = folder[dataset]+'_'+closest_lat+'_'+closest_long+'_'+str(az_tilt[1])+'_'+str(az_tilt[0]) #TODO - fix this for Texas
                timeseries.data_type = 'float'
                timeseries.feeder_name = i.feeder_name 
                timeseries.substation_name = i.substation_name
                timeseries.scale_factor = 1
                timeseries.interval = float(15/60.0) # 15 minute solar data
                if write_opendss_file:
                    timeseries.data_location = os.path.join(output_folder,timeseries.data_label+'.csv')
#                if write_cyme_file:
#                    timeseries.data_location = timeseries.data_label+'.txt'
                unscaled_location = os.path.join(output_folder,timeseries.data_label+'_1000kW_plant.csv')

                i.timeseries = [timeseries]

                if write_cyme_file:
                    key = (az_tilt[0],az_tilt[1],closest_lat,closest_long)
                    timeseries_data_string = list(all_profiles[key]['kW Generated (1000 kW Array)']/1000*100) #We output percentages so use p.u. values in 1000kW array and multiply by 100
                    timeseries_data_string = [f'{entry:.4f}' for entry in timeseries_data_string]
                    cyme_profile = folder[dataset]+'_'+str(key[2])+'_'+str(key[3])+'_'+str(key[1])+'_'+str(key[0]) # e.g. SFO_37.8067_-122.4322_15_180
    
                    total_counter = -1
                    curr_day = -1
                    cyme_str = ''
    
                    for day in range(len(datetimes)):
                        if curr_day!=datetimes[day].day:
                            if curr_day != -1:
                                cyme_str+='\n'
#                                cyme_output.write(cyme_str)
                                all_fps[total_counter].write(cyme_str)
                            total_counter +=1
                            curr_day = datetimes[day].day
                            cyme_str = ''
                            cyme_str +=i.name+'_'+cyme_profile
                            cyme_str+=',GENERATOR,365DAYS,15MINUTES,%,ALL,'
                            cyme_str+=str(datetimes[day].year)+','
                            cyme_str+=str(datetimes[day].strftime("%B").upper())+','
                            cyme_str+=str(datetimes[day].day)+','
                            cyme_str+='%,'
                            cyme_str+='TOTAL'
                        if day < len(timeseries_data_string):
                            cyme_str+=','+timeseries_data_string[day]

                if (az_tilt[0],az_tilt[1],closest_lat,closest_long) in mapped_locations:
                    continue
                mapped_locations.add((az_tilt[0],az_tilt[1],closest_lat,closest_long))

                try:
                    solar_profile = all_profiles[(az_tilt[0],az_tilt[1],closest_lat,closest_long)]
                except:
                    import pdb;pdb.set_trace()

                scaled = solar_profile['PoA Irradiance (W/m^2)'].apply(lambda row: row/1000.0) #1000 because OpenDSS treatas the base unit as 1 kW/m^2
                #rounded = list(df['PoA'].apply(lambda row: round(row,3))) # Cyme doesn't like big values. NOTE - already done.
                rounded = list(solar_profile['PoA Irradiance (W/m^2)'])
                if write_opendss_file:
                    if not os.path.exists(timeseries.data_location):
                        scaled.to_csv(timeseries.data_location,index=False,header=False)





        if write_cyme_file:
            for i in range(len(all_fps)):
                all_fps[i].close()
                
#            cyme_output.close()



        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Connect_Solar_Timeseries.main()

    
