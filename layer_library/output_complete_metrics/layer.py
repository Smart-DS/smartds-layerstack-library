from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import numpy as np
import pandas as pd
import os
import networkx as nx


from layerstack.args import Arg, Kwarg
from ditto.models.line import Line
from ditto.metrics.network_analysis import NetworkAnalyzer
from ditto.modify.system_structure import system_structure_modifier
from ditto.models.power_source import PowerSource
from ditto.network.network import Network
from ditto.dittolayers import DiTToLayerBase
from ditto.models.powertransformer import PowerTransformer
from ditto.models.load import Load
from ditto.models.phase_load import PhaseLoad

logger = logging.getLogger('layerstack.layers.Output_Complete_Metrics')


class Output_Complete_Metrics(DiTToLayerBase):
    name = "output_complete_metrics"
    uuid = UUID("f0cbb056-49ba-4f16-8464-fe2b53d1e107")
    version = '0.1.0'
    desc = "Output metrics after all modifications have been made"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['path_to_feeder_file'] = Kwarg(default=None, description='Path to feeder.txt',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['path_to_no_feeder_file'] = Kwarg(default=None, description='Path to nofeeder.txt',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['excel_output'] = Kwarg(default=None, description='path to the output file for xlsx export',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['tag_location'] = Kwarg(default=None, description='path to the Feeder Tag information (feeder stats)',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['customer_file'] = Kwarg(default=None, description='path to the customers_ext.txt file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['extra_output_location'] = Kwarg(default=None, description='path to the output where metrics.csv will be copied',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['dataset'] = Kwarg(default=None, description='The dataset name',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        
        # WARNING - this layer modifies the ditto network rather than create a copy (to improve performance)
        path_to_no_feeder_file = kwargs.get('path_to_no_feeder_file',None)
        path_to_feeder_file = kwargs.get('path_to_feeder_file',None)
        excel_output = kwargs.get('excel_output',None)
        tag_location = kwargs.get('tag_location',None)
        customer_file = kwargs.get('customer_file',None)
        dataset = kwargs.get('dataset',None)
        extra_output_location = kwargs.get('extra_output_location',None)
        feeders = {}
        substations = {}
        substation_transformers = {}
        
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



        feeder_values = {}
        feeder_values_cnt = {}
        if dataset != 'dataset_2':
            customers_data = pd.read_csv(customer_file,header=None,delimiter=';')
            for idx,row in customers_data.iterrows():
                if row[8] == 0:
                    land_value = 0
                else:
                    land_value = row[15]/row[8]/10.7639 #sqare meters to square feet
                land_value_name = row[3].lower()
                if not 'load_'+land_value_name in model.model_names:
                    continue
                feeder_name = model['load_'+land_value_name].feeder_name
                if not feeder_name in feeder_values:
                    feeder_values[feeder_name] =0
                    feeder_values_cnt[feeder_name] =0
                feeder_values[feeder_name]+=land_value
                feeder_values_cnt[feeder_name]+=1


        with open(path_to_feeder_file, 'r') as f:
            lines = f.readlines()

        for line in lines[1:]:
    
            #Parse the line
            node,sub,feed,sub_trans = map(lambda x:x.strip().lower(), line.split(' '))
    
            #If feeder is new, then add it to the feeders dict
            if feed not in feeders:
        
                #Initialize with a list holding the node
                feeders[feed] = [node.lower().replace('.','')]

            #Othewise, just append the node
            else:
                feeders[feed].append(node.lower().replace('.',''))
        
            #Same thing for the substation
            if feed not in substations:
                substations[feed] = sub.lower().replace('.','')
        
            #Same thing for substation_transformers
            if feed not in substation_transformers:
                substation_transformers[feed] = sub.lower().replace('.','')

        if path_to_no_feeder_file is not None:
            with open(path_to_no_feeder_file, 'r') as f:
                lines = f.readlines()
            for line in lines[1:]:
                node,feed = map(lambda x:x.strip().lower(), line.split(' '))
                if feed != 'mv-mesh':
                    if 'subtransmission' not in feeders:
                        feeders['subtransmission'] = [node.lower().replace('.','')]
                    else:
                        feeders['subtransmission'].append(node.lower().replace('.',''))
                    if 'subtransmission' not in substations:
                        substations['subtransmission'] = ''

        substations = {}
        for i in model.models:
            if hasattr(i,'is_substation_connection') and i.is_substation_connection and i.feeder_name !='':
                substations[i.feeder_name] = i.name

            # WARNING - this layer modifies the ditto network rather than create a copy (to improve performance). To avoid this, create a copy and do this update in the copied version
            if hasattr(i,'feeder_name') and hasattr(i,'substation_name') and i.feeder_name =='' and i.substation_name is not None and i.substation_name!='':
                i.feeder_name = 'subtransmission'
                i.substation_name = ''
                if hasattr(i,'name') and i.name is not None:
                    feeders['subtransmission'].append(i.name)
        substations['subtransmission'] = 'st_mat'
        #Create a network analyzer object
        model.set_names()
        network_analyst = NetworkAnalyzer(model)

        #Add the feeder information to the network analyzer
        network_analyst.add_feeder_information(list(feeders.keys()), list(feeders.values()), substations, '') #TODO find a way to get the feeder type

        #Split the network into feeders
        network_analyst.split_network_into_feeders()

        #Tag the objects
        network_analyst.tag_objects()

        #Set the names
        network_analyst.model.set_names()

        network_analyst.compute_all_metrics_per_feeder(compute_kva_density_with_transformers=True) #RNM has actual transformers (rather than loads with KVA like in cyme models)

        #Export metrics to Excel
        network_analyst.export(excel_output)

        metrics = pd.read_csv(excel_output,header=0)
        subtrans_index = None
        for idx,row in metrics.iterrows():
            if row['feeder_name'] == 'subtransmission':
                subtrans_index = idx
        if subtrans_index is not None:
            metrics.loc[subtrans_index,'max_len_secondaries_mi'] = 0
        metrics['nominal_medium_voltage_class'] = metrics['nominal_medium_voltage_class']/1000 #convert to kV not V

        combined = metrics
        if not dataset == 'dataset_2':

            useful_tags = ['Feeder','Avg_Year','Rural_(%)','Urban_(%)','Residential_(%)','Commercial_(%)','Industrial_(%)','County','Config_subest']
    
            tags = pd.read_csv(tag_location,header=0,delimiter=' ')
            tags = tags[useful_tags]
            tags['Feeder'] = tags['Feeder'].str.lower()
            tags = tags.rename({'Feeder':'feeder_name'},axis=1)
            #tags['Avg_Land_value_(USD/km2)'] = tags['Avg_Land_value_(USD/km2)']/0.386102 #Convert to per square Foot
            
            tags = tags.set_index('feeder_name')
            metrics = metrics.set_index('feeder_name')
    
            combined = metrics.join(tags, on='feeder_name')
            combined = combined.reset_index()
    
            combined["Avg_land_value"] = np.nan
    
    
            for idx,row in combined.iterrows():
                feeder_name = row['feeder_name']
                if feeder_name in feeder_values:
                    combined.loc[idx,'Avg_land_value'] = float(feeder_values[feeder_name]/feeder_values_cnt[feeder_name])
    
            combined = combined.fillna('')

        updated_names_list = [
            ('feeder_name','Feeder Name'),
            ('substation_connection_point', 'Feeder Head Node'),
            ('substation_name', 'Substation Name'),
            ('mv_len_mi','Medium Voltage Length (miles)'),
            ('mv_3ph_len_mi', 'Three Phase Medium Voltage Length (miles)'),
            ('mv_oh_3ph_len_mi', 'Three Phase Overhead Medium Voltage Length (miles)'),
            ('mv_2ph_len_mi', 'Two Phase Medium Voltage Length (miles)'),
            ('mv_oh_2ph_len_mi','Two Phase Overhead Medium Voltage Length (miles)'),
            ('mv_1ph_len_mi','Single Phase Medium Voltage Length (miles)'),
            ('mv_oh_1ph_len_mi','Single Phase Overhead Medium Voltage Length (miles)'),
            ('perct_mv_oh_len', 'Overhead Percentage of Medium Voltage Line Miles'),
            ('ratio_mv_len_to_num_cust', 'Ratio of Medium Voltage Lines to Number of Customers'),
            ('max_sub_node_distance_mi', 'Maximum Node Distance From Substation (miles)'),
            ('nominal_medium_voltage_class', 'Nominal Voltage of Source (kV)'),
            ('lv_len_mi', 'Low Voltage Length (miles)'),
            ('lv_3ph_len_mi', 'Three Phase Low Voltage Length (miles)'),
            ('lv_oh_3ph_len_mi', 'Three Phase Overhead Low Voltage Length (miles)'),
            ('lv_2ph_len_mi', 'Two Phase Low Voltage Length (miles)'),
            ('lv_oh_2ph_len_mi', 'Two Phase Overhead Low Voltage Length (miles)'),
            ('lv_1ph_len_mi', 'Single Phase Low Voltage Length (miles)'),
            ('lv_oh_1ph_len_mi', 'Single Phase Overhead Low Voltage Length (miles)'),
            ('max_len_secondaries_mi', 'Maximum Line Length From Transformer to Load (miles)'),
            ('perct_lv_oh_len', 'Overhead Percentage of Low Voltage Line Miles'),
            ('ratio_lv_len_to_num_cust', 'Ratio of Low Voltage Lines to Number of Customers'),
            ('num_regulators', 'Number of Voltage Regulators'),
            ('num_capacitors', 'Number of Capacitors'),
            ('avg_regulator_sub_distance_mi', 'Average Regulator Distance From Substation (miles)'),
            ('avg_capacitor_sub_distance_mi', 'Average Capacitor Distance From Substation (miles)'),
            ('num_fuses', 'Number of Fuses'),
            ('num_reclosers', 'Number of Reclosers'),
            ('avg_recloser_sub_distance_mi', 'Average Recloser Distance From Substation (miles)'),
            ('num_breakers', 'Number of Breakers'),
            ('num_switches', 'Number of Switches'),
            ('num_links_adjacent_feeders', 'Number of Lines Connected to Adjacent Feeder'),
            ('num_loops', 'Number of Closed Loops'),
            ('num_distribution_transformers', 'Number of Transformers'),
            ('sum_distribution_transformer_mva', 'Total Transformer Capacity (MVA)'),
            ('num_1ph_transformers', 'Number of Single Phase Transformers'),
            ('num_3ph_transformers', 'Number of Three Phase Transformers'),
            ('ratio_1ph_to_3ph_transformers', 'Ratio of Single Phase Transformers to Three Phase Transformers'),
            ('sum_load_mw', 'Total Peak Planning Load (MW)'),
            ('sum_load_pha_mw', 'Total Phase A Peak Planning Load (MW)'),
            ('sum_load_phb_mw', 'Total Phase B Peak Planning Load (MW)'),
            ('sum_load_phc_mw', 'Total Phase C Peak Planning Load (MW)'),
            ('sum_load_mvar', 'Total Reactive Peak Planning Load (MVar)'),
            ('perct_lv_pha_load_mw', 'Percentage of Low Voltage Peak Planning Load on Phase A'),
            ('perct_lv_phb_load_mw','Percentage of Low Voltage Peak Planning Load on Phase B'),
            ('perct_lv_phc_load_mw','Percentage of Low Voltage Peak Planning Load on Phase C'),
            ('num_lv_1ph_loads', 'Number of Single Phase Low Voltage Loads'),
            ('num_lv_3ph_loads','Number of Three Phase Low Voltage Loads'),
            ('num_mv_loads', 'Number of Medium Voltage Loads'),
            ('sum_mv_loads_mw', 'Total Medium Voltage Peak Planning Load (MW)'),
            ('avg_num_load_per_transformer', 'Average Number of Loads per Transformer'),
            ('avg_load_pf', 'Average Peak Planning Load Power Factor'),
            ('avg_load_imbalance_by_phase', 'Average Peak Planning Load Imbalance by Phase'),
            ('num_customers', 'Total Number of Customers'),
            ('cust_density', 'Number of Customers per Square Mile of Feeder Convex Hull'),
            ('load_density_mw', 'Total Peak Planning Load (MW) per Square Mile of Feeder Convex Hull'),
            ('load_density_mvar', 'Total Reactive Peak Planning Load (MVar) per Square Mile of Feeder Convex Hull'),
            ('kva_density', 'Total Transformer Capacity (MVA) per Square Mile of Feeder Convex Hull'),
            ('avg_degree', 'Average Node Degree'),
            ('avg_path_len', 'Average Shortest Path Length'),
            ('diameter', 'Diameter (Maximum Eccentricity)'),
            ('num_pv', 'Number of PVs'),
            ('sum_pv_mw', 'Total PV Capacity (MW)'),
            ('num_pv_vv', 'Number of PVs with Volt-Var Control'),
            ('sum_pv_vv_mw', 'Total Capacity of PVs with Volt-Var Control (MW)'),
            ('num_pv_vv_vw', 'Number of PVs with Volt-Watt and Volt-Var Control'),
            ('sum_pv_vv_vw_mw','Total Capacity of PVs with Volt-Watt Volt-Var Control (MW)'),
            ('num_batteries', 'Number of Batteries'),
            ('sum_batteries_mw', 'Total Capacity of Batteries (MW)'),

        ]
        if not dataset == 'dataset_2':
            updated_names_list.extend([
            ('Avg_Year', 'Average Year of Building Construction'),
            ('Avg_land_value', 'Average Land Value (USD per Square Foot)'),
            ('Rural_(%)', 'Percentage of Rural Customers'),
            ('Urban_(%)', 'Percentage of Urban Customers'),
            ('Residential_(%)', 'Percentage of Residential Customers'),
            ('Commercial_(%)', 'Percentage of Commercial Customers'),
            ('Industrial_(%)', 'Percentage of Industrial Customers'),
            ('County', 'County'),
            ('Config_subest', 'Line Configuration')
            ])
        updated_names_dict = {i:j for i,j in updated_names_list}

        combined = combined.rename(updated_names_dict,axis=1)
        output_df = combined[[j for i,j in updated_names_list]] #Fix order of outputs
        output_df.to_csv(excel_output,header=True,index=False, float_format='%.4f')
        if not os.path.exists(os.path.dirname(extra_output_location)):
            os.makedirs(os.path.dirname(extra_output_location))
        output_df.to_csv(extra_output_location,header=True,index=False, float_format='%.4f')



        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Output_Complete_Metrics.main()

    
