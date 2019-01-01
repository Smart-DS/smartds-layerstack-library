from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import pandas as pd
import math
import pyproj
import os

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
        kwarg_dict['dataset'] = Kwarg(default=None, description='Dataset being used. Important for the projection',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['base_folder'] = Kwarg(default=None, description='Location of the solar data.',
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

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        dataset = None
        base_folder = None
        output_folder = None
        write_opendss_file = False
        write_cyme_file = False
        if 'dataset' in kwargs:
            dataset = kwargs['dataset']
        if 'base_folder' in kwargs:
            base_folder = kwargs['base_folder']
        if dataset is None or base_folder is None:
            return model
        if 'output_folder' in kwargs:
            output_folder = kwargs['output_folder']
        if 'write_opendss_file' in kwargs:
            write_opendss_file = kwargs['write_opendss_file']
        if 'write_cyme_file' in kwargs:
            write_cyme_file = kwargs['write_cyme_file']
        if output_folder is None:
            output_folder = '.'

        folder = {'dataset_4':'SFO', 'dataset_3':'GSO', 'dataset_2': 'SAF'}
        projection = {'dataset_4':'epsg:32610', 'dataset_3':'epsg:32617', 'dataset_2':'epsg:32613'}
        mapped_locations = set()
        all_coords = []
        for csv_file in os.listdir(os.path.join(base_folder,folder[dataset])):
            vals = csv_file.split('_')
            clat = vals[0]
            clong = vals[1]
            all_coords.append((clat,clong))

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
                    return model

                invproj = pyproj.Proj(init=projection[dataset],preserve_units=True) 
                lat_long = invproj(y,x,inverse=True)
                i_lat = lat_long[1]
                i_long = lat_long[0]

                best_dist = float('inf')
                closest_lat = ''
                closest_long = ''
                for coords in all_coords:
                    dist = math.sqrt((i_lat-float(coords[0]))**2 + (i_long-float(coords[1]))**2)
                    if dist < best_dist:
                        best_dist = dist
                        closest_lat = coords[0]
                        closest_long = coords[1]


                timeseries = Timeseries(model)
                timeseries.data_label = folder[dataset]+'_'+closest_lat+'_'+closest_long
                timeseries.data_type = 'float'
                timeseries.interval = 15 # 15 minute load data so take every 15th minute
                if write_opendss_file:
                    timeseries.data_location = os.path.join(output_folder,timeseries.data_label+'.csv')
                if write_cyme_file:
                    timeseries.data_location = timeseries.data_label+'.txt'
                unscaled_location = os.path.join(output_folder,timeseries.data_label+'_1000kW_plant.csv')

                i.timeseries = [timeseries]

                if (closest_lat,closest_long) in mapped_locations:
                    continue
                mapped_locations.add((closest_lat,closest_long))

                df = pd.read_csv(os.path.join(base_folder,folder[dataset],closest_lat+'_'+closest_long+'_2012.csv'))
                feb28_start =  list(df.index[df['Timestamp'] =='2012_02_28_0000'])[0]
                feb28_end =  list(df.index[df['Timestamp'] =='2012_03_01_0000'])[0]
                extra_day = df.iloc[feb28_start:feb28_end]

                df1 = df[:feb28_end]
                df2 = df[feb28_end:]
                shifted_timestamps = extra_day['Timestamp'].apply(lambda row: row.replace('2012_02_28','2012_02_29'))
                extra_day['Timestamp'] = shifted_timestamps
                tmp1 = df1.append(extra_day,ignore_index=True)
                full_year = tmp1.append(df2,ignore_index=True)
                scaled = full_year['GHI'].apply(lambda row: row/1000.0) #1000 because OpenDSS treatas the base unit as 1 kW/m^2
                rounded = list(full_year['GHI'].apply(lambda row: round(row,3))) # Cyme doesn't like big values
                if write_opendss_file:
                    scaled.write_csv(timeseries.data_location,index=False,header=False)
                if write_cyme_file:
                    if not os.path.isdir(os.path.join(output_folder,timeseries.data_label)):
                        os.makedirs(os.path.join(output_folder,timeseries.data_label))
                    output_file = open(os.path.join(output_folder,timeseries.data_label,timeseries.data_location),'w')
                    output_file.write('[INSOLATION_CURVE_VALUES]\nFORMAT=TIME,INSOLATION\n')
                    time_cnt = 0
                    day = 0
                    curr_day = None
                    for cnt in range(len(rounded)):
                        output_file.write("{time},{irrad}\n".format(time=time_cnt*60,irrad= rounded[cnt]))
                        if time_cnt%(60*24) == 0:
                            day+=1
                            if curr_day != None:
                                curr_day.close()
                            curr_day = open(os.path.join(output_folder,timeseries.data_label,timeseries.data_location[:-4]+"_"+str(day)+timeseries.data_location[-4:]),'w')
                            curr_day.write('[INSOLATION_CURVE_VALUES]\nFORMAT=TIME,INSOLATION\n')
                        curr_day.write("{time},{irrad}\n".format(time=time_cnt*60%(60*60*24),irrad= rounded[cnt]))
                        time_cnt+=1

                    output_file.close()


                full_year.to_csv(timeseries.data_location[:-4]+"_full.csv",index=False,header=True)






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

    
