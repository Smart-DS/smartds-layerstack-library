from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.metrics.network_analysis import NetworkAnalyzer
import os
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

logger = logging.getLogger('layerstack.layers.Partitioned_Customers_Per_Transformer_Plots')


class Partitioned_Customers_Per_Transformer_Plots(DiTToLayerBase):
    name = "partitioned_customers_per_transformer_plots"
    uuid = UUID("155b7d1c-9289-49db-b5c8-6a0e80642ff4")
    version = '0.1.0'
    desc = "Compute Number of customers per trasnformer partitioned by unique loads"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['output_folder'] = Kwarg(default=None, description='output folder location for figures on number of customers per transformer',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['customer_file'] = Kwarg(default=None, description='location of the customer infomration file. Header format of "X, Y, Z, Identifier, voltage level, peak active power, peak reactive power, phases, area, height, energy, coincident active power, coincident reactive power, equivalent users, building type, PV capacity, (empty), (empty), (empty)"', 
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        if 'customer_file' in kwargs:
            customer_file = kwargs['customer_file']
        else:
            raise ValueError('Missing customer file to assign types')
        if 'output_folder' in kwargs:
            output_folder = kwargs['output_folder']
        else:
            output_folder = '.'

        customer_file_headers = ['X', 'Y', 'Z','Identifier', 'voltage level', 'peak active power', 'peak reactive power', 'phases', 'area', 'height', 'energy', 'coincident active power', 'coincident reactive power', 'equivalent users', 'building type', 'Value', 'Year', 'PV capacity', 'Class', 'Rural/Urban','Zone']

        customer_file_headers_index = {}
        for i in range(len(customer_file_headers)):
            customer_file_headers_index[customer_file_headers[i]] = i
        building_types = {
                           0:'industrial', #Normally a HV load
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

        load_map = {}
        for row in open(customer_file,'r'):
            split_row = row.split(';') # A csv file delimited by ;
            load_name = split_row[customer_file_headers_index['Identifier']].lower()
            try:
                customer_type = building_types[int(split_row[customer_file_headers_index['building type']])]
            except:
                customer_type = building_types[int(split_row[-1])] #dataset 2 has different structure
            load_map['load_'+load_name] = customer_type

        network_analyst = NetworkAnalyzer(model)
        transformer_mapping = network_analyst.get_transformer_load_mapping()
        all_transformers = {}
        residential_transformers = {}
        commercial_transformers = {}
        mixed_transformers = {}
        scaled_all_transformers = {}
        scaled_residential_transformers = {}
        scaled_commercial_transformers = {}
        scaled_mixed_transformers = {}
        for i in transformer_mapping:
            val = len(transformer_mapping[i])
            load_types = set()
            for load in transformer_mapping[i]:
                load_type = load_map[load]
                load_types.add(load_type)

            if val in all_transformers:
                all_transformers[val] = all_transformers[val]+1
                scaled_all_transformers[val] = scaled_all_transformers[val]+val
            else:
                all_transformers[val] = 1
                scaled_all_transformers[val] = val

            if 'single-family' in load_types and len(load_types) ==1:
                if val in residential_transformers:
                    residential_transformers[val]=residential_transformers[val]+1
                    scaled_residential_transformers[val] = scaled_residential_transformers[val]+val
                else:
                    residential_transformers[val] = 1
                    scaled_residential_transformers[val] = val
            if 'single-family' in load_types and len(load_types) >1:
                if val in mixed_transformers:
                    mixed_transformers[val]=mixed_transformers[val]+1
                    scaled_mixed_transformers[val] = scaled_mixed_transformers[val]+val
                else:
                    mixed_transformers[val] = 1
                    scaled_mixed_transformers[val] = val
            if 'single-family' not in load_types:
                if val in commercial_transformers:
                    commercial_transformers[val]=commercial_transformers[val]+1
                    scaled_commercial_transformers[val]=scaled_commercial_transformers[val]+val
                else:
                    commercial_transformers[val] = 1
                    scaled_commercial_transformers[val]=val
        different_categories = [all_transformers,residential_transformers,commercial_transformers,mixed_transformers]
        scaled_different_categories = [scaled_all_transformers,scaled_residential_transformers,scaled_commercial_transformers,scaled_mixed_transformers]
        title_names = ["Number of Customers per Tranformer","Number of Customers per Residential Tranformer","Number of Customers per Commercial Tranformer","Number of Customers per Mixed Tranformer"] 
        weighted_title_names = ["Weighted Number of Customers per Tranformer","Weighted Number of Customers per Residential Tranformer","Weighted Number of Customers per Commercial Tranformer","Weighted Number of Customers per Mixed Tranformer"] 
        for num in range(len(different_categories)):
            category = different_categories[num]
            res_list = []
            if len(category.keys()) == 0:
                continue
            for i in range(max(category.keys())+1):
                if i in category:
                    res_list.append(category[i])
                else:
                    res_list.append(0)
            plt.clf()
            plt.bar(range(len(res_list)),res_list,align='center')
            plt.title(title_names[num])
            plt.xticks(range(len(res_list)),range(len(res_list)))
            plt.savefig(os.path.join(output_folder,title_names[num]+'.png'))

        for num in range(len(scaled_different_categories)):
            category = scaled_different_categories[num]
            res_list = []
            if len(category.keys()) == 0:
                continue
            for i in range(max(category.keys())+1):
                if i in category:
                    res_list.append(category[i])
                else:
                    res_list.append(0)
            plt.clf()
            plt.bar(range(len(res_list)),res_list,align='center')
            plt.title(weighted_title_names[num])
            plt.xticks(range(len(res_list)),range(len(res_list)))
            plt.savefig(os.path.join(output_folder,weighted_title_names[num]+'.png'))


            

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Partitioned_Customers_Per_Transformer_Plots.main()

    
