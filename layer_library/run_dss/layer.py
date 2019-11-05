from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import opendssdirect as dss
import pandas as pd
import networkx as nx
import os
import matplotlib
import numpy as np
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models import Line

logger = logging.getLogger('layerstack.layers.Run_Dss')


class Run_Dss(DiTToLayerBase):
    name = "run_dss"
    uuid = UUID("e5ef54d0-3d98-4ee4-94bf-88e7a5f98c4c")
    version = '0.1.0'
    desc = "Run OpenDSSDirect on the ouput data and export plots and voltages "

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['master_file'] = Kwarg(default=None, description='Location of Masterfile to load using opendssdirect',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['plot_profile'] = Kwarg(default=None, description='',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['output_folder'] = Kwarg(default=None, description='Location of output plots and voltage profiles',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['region'] = Kwarg(default=None, description='Region this is being run for',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        plot_profile = False
        output_folder = None
        master_file = None
        region = None
        print('Starting OpenDSS run')
        if 'region' in kwargs:
            region = kwargs['region']
        if 'master_file' in kwargs:
            master_file = kwargs['master_file']
        if 'plot_profile' in kwargs:
            plot_profile = kwargs['plot_profile']
        if 'output_folder' in kwargs:
            output_folder = kwargs['output_folder']

        if master_file is not None:
            if not os.path.isdir(output_folder):
                os.makedirs(output_folder)
            dss_map = {}
            sorted_dss_vals_avg = []
            sorted_dss_vals_max = []
            dss_vals_avg = []
            monitor_line = None
            #nominal_voltage_map = {}
            dss.run_command("Redirect "+master_file)
            all_feeders = {}
            all_monitors = {}
            for i in model.models:
                if hasattr(i,'feeder_name') and i.feeder_name is not None and hasattr(i,'substation_name') and i.substation_name is not None and hasattr(i,'from_element') and i.from_element is not None:
                    if i.substation_name+"_"+i.feeder_name in all_feeders:
                        all_feeders[i.substation_name+"_"+i.feeder_name].append(i.from_element)
                    else:
                        all_feeders[i.substation_name+"_"+i.feeder_name] = [i.from_element]
                    if i.feeder_name is not "" and i.from_element in model.model_names and model[i.from_element].is_substation_connection:
                        all_monitors[i.feeder_name] = i.name
            #    if hasattr(i,'from_element') and i.from_element == 'st_mat':
            #        monitor_line = i.name
            #    if hasattr(i,'nominal_voltage') and  i.nominal_voltage is not None and hasattr(i,'name') and i.name is not None:
            #        nominal_voltage_map[i.name] = i.nominal_voltage

            all_G = {}
            if plot_profile:
                #G = nx.Graph()
                pos = {}
                line_df = dss.utils.lines_to_dataframe()
                trans_df = dss.utils.class_to_dataframe("transformer")
                line_data = line_df[['Name','Bus1', 'Bus2']].to_dict(orient="index")
                trans_data = pd.DataFrame(trans_df[['XfmrCode','buses']]).to_dict(orient="index")
    
                all_labels = {}
    
                for idx in trans_data:
                    tf = trans_data[idx]
                    label = 'Transformer'
                    color = 'gainsboro'
                    size = 2
                    name = tf["XfmrCode"]
                    if idx.split('.')[1] in model.model_names:
                        feeder = model[idx.split('.')[1]].feeder_name
                        if feeder not in all_G:
                            all_G[feeder] = nx.Graph()
                        if label not in all_labels:
                            all_labels[label] = Line2D([0,1],[0,1], color=color,lw=size)
                        all_G[feeder].add_edge(tf["buses"][0].split(".")[0], tf["buses"][1].split(".")[0],color=color,weight=size,label=label)
                    else:
                        print('ignoring transformer '+name)
                    
                for idx in line_data:
                    line = line_data[idx]
                    linename = line["Name"]
                    if linename in model.model_names:
                        feeder = model[linename].feeder_name
                        if feeder not in all_G:
                            all_G[feeder]= nx.Graph()
                        phases = set(line["Bus1"].split(".")[1:])
                        name = line["Bus1"].split(".")[0]
                        #nominal_voltage = nominal_voltage_map[name]
                        label = ''
                        color = [0,0,0]
                        if '1' in phases:
                            color = tuple(np.add(color, (255,0,0)))
                            label+='A'
                            size = 2
                        if '2' in phases:
                            color = tuple(np.add(color, (0,255,0)))
                            label+='B'
                            size = 2
                        if '3' in phases:
                            color = tuple(np.add(color, (0,0,255)))
                            label+='C'
                            size = 2
                        if color == (255,255,255):
                            color = (0,0,0)
                        color='#%02x%02x%02x' % (color[0],color[1],color[2]) 
                        #if nominal_voltage < 600: # For LV lines
                        if len(phases)==2: # basic proxy for LV lines in non-delta systems. TODO: add nominal voltage checking
                            color = 'darkorange'
                            size=1
                            label = 'Triplex'
        
                        if label not in all_labels:
                            all_labels[label] = Line2D([0,1],[0,1], color=color,lw=size)
                        all_G[feeder].add_edge(line["Bus1"].split(".")[0], line["Bus2"].split(".")[0],color=color,weight=size,label=label)
                    else:
                        print('ignoring line '+linename)
    
                
                
            
            #dss.run_command("export voltages "+os.path.join(output_folder,"bus_voltages.csv"))
            names = dss.Circuit.AllBusNames()
            global_max = -1000
            global_min = 100000

            first_run = True
            distance_lookup = {}
            for monitor_feeder,monitor_line in all_monitors.items():
                dss.run_command("Redirect "+master_file) #rerun to get correct distances
                print("Monitor at "+monitor_line)
                dss.run_command("New Energymeter.m1 Line."+monitor_line) #should always be a line from st_mat
                dss.run_command("Solve")
                for name in names:
                    dss.Circuit.SetActiveBus(name)
                    dss_pus = dss.Bus.PuVoltage()
                    pus = []
                    tot = 0
                    cnt = 0
                    D = 0
                    use_D = False
                    for i in range(int(len(dss_pus)/2)):
                        mag = abs(complex(dss_pus[2*i],dss_pus[2*i+1]))
                        if plot_profile:
                            D = dss.Bus.Distance()
                            if name in distance_lookup:
                                if distance_lookup[name] < D:
                                    pos[dss.Bus.Name()] = (D, mag) 
                                    use_D = True
                                    distance_lookup[name] = D
                            else:
                                distance_lookup[name] = D
                                pos[dss.Bus.Name()] = (D, mag) 
                        if mag > 0:
                            tot += mag
                            cnt+=1
                    if cnt == 0:
                        tot = 0
                    else:
                        tot = tot/cnt
                    if use_D:
                        pos[dss.Bus.Name()] = (D, tot) 
                    if tot < global_min and tot !=0 and first_run:
                        global_min = tot
                    if tot > global_max and first_run:
                        global_max = tot
                    if tot>0 and first_run:
                        dss_map[name] = tot
                        dss_vals_avg.append(tot)
                        sorted_dss_vals_avg.append((tot,name))
                first_run=False
            
            sorted_dss_vals_avg = pd.DataFrame(sorted(sorted_dss_vals_avg))
            try:
                sorted_dss_vals_avg.columns = ('OpenDSS Value', 'Node')
                sorted_dss_vals_avg.to_csv(os.path.join(output_folder,region+'_pu_voltages_avg_opendss.csv'), index=False, header=True)
            except:
                print("System didn't solve")
                return model

            if plot_profile:

                if not os.path.exists(os.path.join(output_folder,region+"_profiles")):
                    os.makedirs(os.path.join(output_folder,region+"_profiles"))
                for feeder in all_G:
                    G = all_G[feeder]
                    fig, axs = plt.subplots(1, 1, figsize=(16, 10))

    
                    edges = G.edges()
                    colors = [G[u][v]['color'] for u,v in edges]
                    weights = [G[u][v]['weight'] for u,v in edges]
                    
                    ax = axs
                    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='k', node_size=10)
                    #nx.draw_networkx_labels(G, pos, ax=ax, labels={x: x for x in G.nodes()})
                    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=colors, width=weights)
                    
                    ax.grid()
                    ax.set_ylabel("Voltage in p.u.")
                    ax.set_xlabel("Distance in km")
                    ax.set_title(region+"_"+feeder+" Voltage profile plot");
                    ax.set_ylim(global_min-0.01,global_max+0.01)
                    all_keys_tmp = ['ABC','A','B','C','Triplex','Transformer']
                    all_values = []
                    all_keys = []
                    for key in all_keys_tmp:
                        if key in all_labels:
                            all_values.append(all_labels[key])
                            all_keys.append(key)
                    plt.legend(all_values,all_keys)
                    plt.savefig(os.path.join(output_folder,region+"_profiles",region+'_'+feeder.replace('>','')+'_voltage_profile.png'))
    

                plt.clf()


            comparison_ticks = []
            comparison_cnt = 0.01
            while comparison_cnt < 1.5:
                comparison_cnt+=0.005
                if comparison_cnt >= global_min-0.01 and comparison_cnt <= global_max + 0.01:
                    comparison_ticks.append(round(comparison_cnt,3))
            
            f, axarr = plt.subplots(1, sharex=True)
            bins = np.linspace(0.9,1.07,50)
            axarr.set_title(region+' OpenDSS P.U. Voltages')
            axarr.hist(x=dss_vals_avg, bins=bins, color='#0504aa',
                                        alpha=0.7, rwidth=0.85)
            axarr.set_xlim(global_min-0.01,global_max+0.01)
            axarr.set_xticks(comparison_ticks)
            axarr.set_xticklabels(comparison_ticks,rotation=70)
            axarr.set_ylabel('Frequency')
            axarr.set_xlabel('p.u.')
            
            plt.savefig(os.path.join(output_folder, region+'_pu_voltages_opendss.png'))
            plt.clf()
            percentiles = []
            for i in range(100):
                percentiles.append(np.percentile(dss_vals_avg,i))
            plt.bar(range(len(percentiles)), percentiles, width = 1/1.5)
            max_pct = max(percentiles)
            min_pct = min(percentiles)
            plt.ylim(min_pct - (max_pct-min_pct)/20, max_pct + (max_pct-min_pct)/20)
            plt.grid()
            
            plt.xlabel('Percentile')
            plt.ylabel('Value')
            plt.title(region+' All Percentiles')
            plt.savefig(os.path.join(output_folder,region+ "_pu_percentiles.png"),bbox_inches='tight')
    


        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Run_Dss.main()

    
