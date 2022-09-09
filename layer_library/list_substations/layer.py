from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.node import Node
from ditto.models.load import Load

import os
import pandas as pd
import math
import pyproj
import json
logger = logging.getLogger('layerstack.layers.List_Substations')


class List_Substations(DiTToLayerBase):
    name = "list_substations"
    uuid = UUID("d75ab38b-33cb-4ca1-9648-2660bffec624")
    version = '0.1.0'
    desc = "List all of the substations in one file"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['output_folder'] = Kwarg(default='.', description='Location where substation data is written to',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['dataset'] = Kwarg(default=None, description='Which dataset is being used for projection',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['is_timeseries'] = Kwarg(default=False, description='whether or not there is timeseries data too',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        output_folder = kwargs.get('output_folder')
        dataset = kwargs.get('dataset')
        is_timeseries = kwargs.get('is_timeseries')
        projection = {'dataset_4':'epsg:32610', 'dataset_3':'epsg:32617', 'dataset_2':'epsg:32613','t_and_d':'epsg:32614','houston':'epsg:32614','texas_rural':'epsg:32614','Full_Texas':'epsg:32614', 'South_Texas':'epsg:32614','texas_test':'epsg:32614'}
        substation_kv = {}
        substation_load_p = {}
        substation_load_q = {}
        substation_coords_lat = {}
        substation_coords_long = {}
        substation_connections = {}
        substation_timeseries_p = {}
        for i in model.models:
            if isinstance(i,Node) and i.is_substation_connection:
                feeder_name = i.feeder_name
                substation_name = i.substation_name
                feeder_name = feeder_name.replace(">", "-")
                substation_name = substation_name.replace(">", "-")
                if (
                    feeder_name == "" and i.nominal_voltage < 30000
                ):  
                    continue
                if (
                    substation_name != "subtransmission"
                    and feeder_name == ""
                ):  # i.e. it's a substation
                    substation_load_p[substation_name] = 0
                    substation_load_q[substation_name] = 0
                    x = i.positions[0].long
                    y = i.positions[0].lat
                    invproj = pyproj.Proj(init=projection[dataset],preserve_units=True) 
                    lat_long = invproj(x,y,inverse=True)
                    i_lat = lat_long[1]
                    i_long = lat_long[0]
                    substation_coords_lat[substation_name] = i_lat
                    substation_coords_long[substation_name] = i_long
                    substation_connections[substation_name] = i.name
                    substation_kv[substation_name] = i.nominal_voltage/1000.0
        print('starting to read load information')
        for i in model.models:
            if isinstance(i,Load):
                for pl in i.phase_loads:
                    if pl.p is not None and i.substation_name in substation_load_p:
                        substation_load_p[i.substation_name]+=pl.p/1000.0
                        substation_load_q[i.substation_name]+=pl.q/1000.0
                if is_timeseries and len(i.timeseries) > 0:
                    timeseries_file = i.timeseries[0].data_location.replace('_pu','')

                    ts_data = pd.read_csv(timeseries_file,header=None)
                    if i.substation_name not in substation_timeseries_p:
                        substation_timeseries_p[i.substation_name] = ts_data
                    else:
                        substation_timeseries_p[i.substation_name] += ts_data
        csv_output = pd.DataFrame([])
        for substation in substation_load_p:
            print(substation,substation_load_p[substation],substation_load_q[substation],substation_kv[substation], substation_coords_lat[substation], substation_connections[substation])
            csv_output = csv_output.append({'Name':substation, 'Total Real Load': substation_load_p[substation], 'Total Reactive Load': substation_load_q[substation], 'kV': substation_kv[substation], 'Latitude': substation_coords_lat[substation],'Longitude': substation_coords_long[substation], 'Connection Node': substation_connections[substation]},ignore_index=True)

        cols = ['Name','Total Real Load','Total Reactive Load','kV','Latitude','Longitude','Connection Node']
        csv_output = csv_output[cols]
        
        csv_output.to_csv(os.path.join(output_folder,'substations.csv'),header=True,index=False)
        json_data = csv_output.to_dict()


        if is_timeseries:
            print('starting to write timeseries outputs')
            if not os.path.exists(os.path.join(output_folder,'aggregate_timeseries')):
                os.makedirs(os.path.join(output_folder,'aggregate_timeseries'))
            for substation in substation_timeseries_p:
                timeseries_output = substation_timeseries_p[substation]
                timeseries_output.columns = ['Real Power']
                pf = 0.95
                timeseries_output['Reactive Power'] = timeseries_output['Real Power']*(((1/(pf**2))-1)**0.5)
                timeseries_output.to_csv(os.path.join(output_folder,'aggregate_timeseries','substation_'+substation+'.csv'),header=True,index=False)

        print('finished writing substation outputs')
        with open(os.path.join(output_folder,'substations.json'),'w') as json_output:
            json.dump(json_data,json_output, indent=4)



                     


        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    List_Substations.main()

    
