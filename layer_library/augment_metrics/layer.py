from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import pandas as pd
import os
import numpy as np

from ditto.models.storage import Storage
from ditto.models.photovoltaic import Photovoltaic
from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.Augment_Metrics')


class Augment_Metrics(DiTToLayerBase):
    name = "augment_metrics"
    uuid = UUID("668d8340-46b6-4a41-8f4f-4fecc3dae33e")
    version = '0.1.0'
    desc = "Output metrics with extra solar and batteries"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['input_location'] = Kwarg(default=None, description='metrics.csv file being read',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['output_location'] = Kwarg(default=None, description='metrics.csv file being written',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        input_location = kwargs.get('input_location',None)
        output_location = kwargs.get('output_location',None)

        if not os.path.exists(input_location):
            print('metrics file not found. Skipping...')
            return model

        original_metrics = pd.read_csv(input_location,header=0)
        all_feeders = set()
        for input_feeder in original_metrics['Feeder Name']:
            all_feeders.add(input_feeder)

              
        # dictionaries to augment
        num_pv = {}
        sum_pv_mw = {}
        num_pv_vv = {}
        sum_pv_vv_mw = {}
        num_pv_vv_vw = {}
        sum_pv_vv_vw_mw = {}
        num_batteries = {}
        sum_batteries_mw = {}
        for i in model.models:
            if hasattr(i,'feeder_name'):
                feeder = i.feeder_name
                if feeder in all_feeders:
                    num_pv[feeder] = 0
                    num_pv_vv[feeder] = 0
                    num_pv_vv_vw[feeder] = 0
                    num_batteries[feeder] = 0
    
                    sum_pv_mw[feeder] = 0
                    sum_pv_vv_mw[feeder] = 0
                    sum_pv_vv_vw_mw[feeder] = 0
                    sum_batteries_mw[feeder] = 0


        for i in model.models:
            if isinstance(i,Photovoltaic):
                feeder = i.feeder_name
                if feeder in all_feeders:
                    num_pv[feeder] +=1
                    sum_pv_mw[feeder] += i.rated_power/1000/1000

                    if i.control == 'voltvar':
                        num_pv_vv[feeder] +=1
                        sum_pv_vv_mw[feeder] += i.rated_power/1000/1000

                    if i.control == 'voltwatt_voltvar':
                        num_pv_vv_vw[feeder] +=1
                        sum_pv_vv_vw_mw[feeder] += i.rated_power/1000/1000

            if isinstance(i,Storage):
                feeder = i.feeder_name
                if feeder == '':
                    feeder = 'subtransmission'
                if feeder in all_feeders:
                    num_batteries[feeder] +=1
                    sum_batteries_mw[feeder] += i.rated_power/1000/1000


        for idx,row in original_metrics.iterrows():
            feeder = row['Feeder Name']
            original_metrics.loc[idx,'Total PV Capacity (MW)'] = sum_pv_mw[feeder]
            original_metrics.loc[idx,'Number of PVs'] = num_pv[feeder]

            original_metrics.loc[idx,'Total Capacity of PVs with Volt-Var Control (MW)'] = sum_pv_vv_mw[feeder]
            original_metrics.loc[idx,'Number of PVs with Volt-Var Control'] = num_pv_vv[feeder]

            original_metrics.loc[idx,'Total Capacity of PVs with Volt-Watt Volt-Var Control (MW)'] = sum_pv_vv_vw_mw[feeder]
            original_metrics.loc[idx,'Number of PVs with Volt-Watt and Volt-Var Control'] = num_pv_vv_vw[feeder]

            original_metrics.loc[idx,'Total Capacity of Batteries (MW)'] = sum_batteries_mw[feeder]
            original_metrics.loc[idx,'Number of Batteries'] = num_batteries[feeder]


        for idx,row in original_metrics.iterrows():
            orig_feeder = row['Feeder Name']
            original_metrics.loc[idx,'Feeder Name'] = orig_feeder.replace('->','--')

            if 'County' in original_metrics.columns:
                orig_county = row['County']
                if orig_county == 'Greensboro':
                    original_metrics.loc[idx,'County'] = 'Guilford'

        original_metrics = original_metrics.fillna('')
        original_metrics.to_csv(output_location,header=True,index=False,float_format='%.4f')
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Augment_Metrics.main()

    
