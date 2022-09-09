from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import os
import json
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed, wait
import multiprocessing

import math
from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.load import Load
from ditto.models.line import Line
from ditto.models.powertransformer import PowerTransformer
import opendssdirect as dss

logger = logging.getLogger('layerstack.layers.Find_Line_Overloads')

""" A mult-process function"""
def read_data(input_args):
    file_location = input_args 
    parquet_data = pd.read_parquet(file_location).reset_index()
    kw_data = parquet_data['total_site_electricity_kw']
    kvar_data = parquet_data['total_site_electricity_kvar']
    file_name = os.path.basename(file_location).split('.')[0]
    return (file_name,(kw_data,kvar_data))


def check_line_overloads(ub=1.05):
    """Computes the loading for Lines."""
    
    line_overloads_dict = {}
    unloaded_line_dict = {}
    # Set the active class to be the lines
    dss.Circuit.SetActiveClass("Line")

    # Loop over the lines
    flag = dss.ActiveClass.First()
    while flag > 0:
        line_name = dss.CktElement.Name()
        # Get the current limit
        bus1 = dss.Properties.Value("bus1")
        bus2 = dss.Properties.Value("bus2")
        line_limit_per_phase = dss.CktElement.NormalAmps()
        
        # Compute the current through the line
        phase = int(.25*len(dss.CktElement.Currents()))
        line_current = dss.CktElement.CurrentsMagAng()[:2*phase]
        line_current = line_current[::2]
        # The loading is the ratio of the two
        ldg = max(line_current)/float(line_limit_per_phase)
        if ldg>ub:
            line_overloads_dict[line_name] = {'Bus1': bus1, 'Bus2': bus2, 'Loading (p.u.)': ldg}
        elif ldg == 0:
            unloaded_line_dict[line_name] = {'Bus1': bus1, 'Bus2': bus2}
        
        # Move on to the next line
        flag = dss.ActiveClass.Next()
        
    return line_overloads_dict, unloaded_line_dict

def check_xfmr_overloads(ub=1.05):
    
    #####################################
    #    Transformer current violations
    #####################################
    #
    transformer_violation_dict ={}
    unloaded_transformers_dict = {}
    dss.Circuit.SetActiveClass("Transformer")
    flag = dss.ActiveClass.First()
    while flag > 0:
        # Get the name of the Transformer
        transformer_name = dss.CktElement.Name()
        transformer_current = []
        
        #transformer_limit = dss.CktElement.NormalAmps()
        
        
        hs_kv = float(dss.Properties.Value('kVs').split('[')[1].split(',')[0])
        kva = float(dss.Properties.Value('kVA'))
        n_phases = dss.CktElement.NumPhases()
        if n_phases>1:
            transformer_limit_per_phase = kva/(hs_kv*math.sqrt(3))
        else:
            transformer_limit_per_phase = kva/hs_kv
    
        #nwindings = int(dss.Properties.Value("windings"))
        primary_bus = dss.Properties.Value("buses").split('[')[1].split(',')[0]
        
        #phase = int((len(dss.CktElement.Currents())/(nwindings*2.0)))
        Currents = dss.CktElement.CurrentsMagAng()[:2*n_phases]
        Current_magnitude = Currents[::2]    
        
        transformer_current = Current_magnitude

        # Compute the loading
        ldg = max(transformer_current)/transformer_limit_per_phase
        
        # If the loading is more than 100%, store the violation
        if ldg > ub:
            transformer_violation_dict[transformer_name] = {'Bus': primary_bus, 'Loading (p.u.)': ldg, 'kVA' : kva, 'number_of_phases': n_phases}
        elif ldg == 0:
            unloaded_transformers_dict[transformer_name] = {'Bus': primary_bus, 'kVA' : kva, 'number_of_phases': n_phases}
        
        # Move on to the next Transformer...
        flag = dss.ActiveClass.Next()
    
      
    return transformer_violation_dict, unloaded_transformers_dict


class Find_Line_Overloads(DiTToLayerBase):

    

    name = "find_line_overloads"
    uuid = UUID("a8c75907-a067-4d1a-9a73-7c144a3662f9")
    version = '0.1.0'
    desc = "Run powerflow and find lines that are overloaded"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['master_folder'] = Kwarg(default=None, description='Location of master file for model head',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['enduse_folder'] = Kwarg(default=None, description='Location of enduse folder',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['is_reference'] = Kwarg(default=False, description='Whether this is the scenario used as a reference',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['use_substations'] = Kwarg(default=False, description='If True, run powerflow on the substations rather than the root folder',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        master_folder = kwargs.get('master_folder',None)
        enduse_folder = kwargs.get('enduse_folder',None)
        master_file = os.path.join(master_folder,'Master.dss')
        is_reference = kwargs.get('is_reference',False)
        use_substations = kwargs.get('use_substations',False)
        model.set_names()
        node_lines = {} # a map from a node (which is adjacent to a fuse) to a list of all non-fuse lines that it connects to
        min_node_ampacity = {} # a map from a node to the minimum ampacity of all non-fuse lines that it connects to

        # Initialize the nodes which are adjacent to a fuse (as an empty list)
        for i in model.models:
            if isinstance(i,Line) and i.is_fuse:
                node_lines[i.to_element] =[]
                node_lines[i.from_element] =[]

        # Find lines next to the nodes of the fuse
        for i in model.models:
            if isinstance(i,Line) and not i.is_fuse:
                if i.from_element in node_lines:
                    node_lines[i.from_element].append(i.name)
                if i.to_element in node_lines:
                    node_lines[i.to_element].append(i.name)

        
        all_ampacities = set()
        all_xfmr_sizes = set()
        all_fuses = set()
        for i in model.models:
            if hasattr(i,'wires'):
                for wire in i.wires:
                    if wire.ampacity is not None:
                        all_ampacities.add(wire.ampacity)
                    if i.is_fuse and wire.interrupting_rating is not None:
                        all_fuses.add(wire.interrupting_rating)
            if isinstance(i,PowerTransformer) and hasattr(i,'windings'):
                for winding in i.windings:
                    if winding.rated_power is not None:
                        all_xfmr_sizes.add(winding.rated_power)
        all_parquet_locations = {}
        load_name_mapping = {}
        if is_reference:
            for load in model.models:
                if isinstance(load,Load):
                    if load.timeseries is not None:
                        for ts in load.timeseries:
                            sp_location = ts.data_location.split('/')[-1].split('_')
                            parquet_location = os.path.join(enduse_folder,sp_location[0]+'_'+sp_location[2]+'.parquet') #Enduses are not a subfolder of profiles
                            if 'mesh' in parquet_location:
                                parquet_location = parquet_location.replace('.csv','') # a hack to fix inconsistencies in underscore naming
                                parquet_location = parquet_location.replace('_pu','') # a hack to fix inconsistencies in underscore naming
                            #print(parquet_location)
                            if not parquet_location in all_parquet_locations:
                                all_parquet_locations[parquet_location] = 0
                            all_parquet_locations[parquet_location]+=1 
                            load_name_mapping[load.name] = sp_location[0]+'_'+sp_location[2]
            with open(os.path.join(master_folder,'all_parquet_locations.json'),'w') as outfile:
                outfile.write(json.dumps(all_parquet_locations,indent=4))
            with open(os.path.join(master_folder,'load_name_mapping.json'),'w') as outfile:
                outfile.write(json.dumps(load_name_mapping,indent=4))
        else:
            with open(os.path.join(master_folder,'all_parquet_locations.json'),'r') as infile:
                all_parquet_locations = json.load(infile)
            with open(os.path.join(master_folder,'load_name_mapping.json'),'r') as infile:
                load_name_mapping = json.load(infile)
            

        parquet_counts = {}
        for parquet_file,cnt in all_parquet_locations.items():
            parquet_name = parquet_file.split('/')[-1]
            parquet_counts[parquet_name.replace('.parquet','')] = cnt

        print('Reading timeseries loads')
        inputs = [parquet_file for parquet_file,cnt in all_parquet_locations.items()] #not using parquet file counts when reading data
        nprocs = int(multiprocessing.cpu_count()*3/4)
        nprocs = 3
        pool = multiprocessing.Pool(processes=nprocs)
        all_parquet = pool.map(read_data, inputs) #Format is [feeder number, total/res/com, load number, timeseries]
        pool.close()
        pool.join()
        """
        all_parquet = []
        for pool_input in inputs:
            all_parquet.append(read_data(pool_input))
        """
        print('Done reading timeseries')
        enduse_map = {}
        all_kw = []
        all_kvar = []
        for (idx,value) in all_parquet:
            enduse_map[idx] = value
            all_kw.append(value[0]* parquet_counts[idx])
            all_kvar.append(value[1] * parquet_counts[idx])
        
        total_load = sum(all_kw)
        max_time  = total_load.idxmax()
        peak_total_hour = int(max_time/4)
        peak_total_sec = (max_time%4)*15*60

        # Use if loading the master file with timeseries is taking too long
        all_masters = [master_file]
        if use_substations:
            all_masters = []
            for substation_folder in os.listdir(master_folder):
                if os.path.exists(os.path.join(master_folder,substation_folder,'Master.dss')):
                    all_masters.append(os.path.join(master_folder,substation_folder,'Master.dss'))
        for substation_master_file in all_masters:
            result = dss.run_command("Redirect "+substation_master_file)
            print('finished initial load') #Timeseries runs don't include solve in them so shouldn't run
            print(result,flush=True)
            dss.Loads.First()
            while True:
                name = dss.Loads.Name()
                name_base=name
                multiplier = 1
                if name.endswith('_1') or name.endswith('_2'): #center tap loads
                    name_base = name[:-2]
                    multiplier = 0.5
    
                try:
                    load  = model[name_base]
                except:
                    import pdb;pdb.set_trace()
    
    
                parquet_name = load_name_mapping[name_base]
                if 'mesh' in parquet_name:
                    parquet_name = 'mesh'
                kw = enduse_map[parquet_name][0].iloc[max_time]*multiplier
                kvar = enduse_map[parquet_name][1].iloc[max_time]*multiplier
                res1 = dss.Loads.kW(kw)
                res2 = dss.Loads.kvar(kvar)
                #print(name_base,kw,kvar,max_time,parquet_name,res1,res2)
    
                if not dss.Loads.Next() > 0:
                    break
    
            result = dss.run_command(f"Solve")
            print('finished timeseries run')
            print(result,flush=True)
    
    
            all_ampacities = sorted(list(all_ampacities))
            all_xfmr_sizes = sorted(list(all_xfmr_sizes))
            all_fuses = sorted(list(all_fuses))
    
            """
            print('Running powerflow for Hour:',peak_total_hour,'Second: ',peak_total_sec)
            result = dss.run_command("Redirect "+master_file)
            print('finished initial load') #Timeseries runs don't include solve in them so shouldn't run
            print(result,flush=True)
            result = dss.run_command(f"Solve mode=yearly hour={peak_total_hour} sec={peak_total_sec} number=1")
            print('finished timeseries run')
            print(result,flush=True)
            """
            line_overloads_dict, unloaded_lines_dict = check_line_overloads()
            data = pd.DataFrame.from_dict(line_overloads_dict,'index',columns=['Bus1','Bus2','Loading (p.u.)'])
            data = data.sort_values(by=['Loading (p.u.)'])
            data = data.reset_index()
            print(data)
            for idx,row in data.iterrows():
                line_name = row['index'].replace('Line.','')
                line = model[line_name]
                for wire in line.wires:
                    if wire.ampacity is not None:
                        required_value = wire.ampacity*row['Loading (p.u.)']*1.25 # *1.25 to oversize a bit more
                        seen_wire = False
                        for new_ampacity in all_ampacities:
                            if new_ampacity > required_value:
                                wire.ampacity = new_ampacity
                                seen_wire = True
                                break
                        if not seen_wire:
                            wire.ampacity = 1500.0 # Provide as a maximum value if too big.
    
            xfmr_overloads_dict, unloaded_xfmrs_dict = check_xfmr_overloads()
            data = pd.DataFrame.from_dict(xfmr_overloads_dict,'index',columns=['Bus','kVA','Loading (p.u.)','number_of_phases'])
            data = data.sort_values(by=['Loading (p.u.)'])
            data = data.reset_index()
            print(data)
            print(data[['Bus','Loading (p.u.)']])
            for idx,row in data.iterrows():
                transformer_name = row['index'].replace('Transformer.','')
                if not transformer_name in model.model_names:
                    transformer_name = row['index'].replace('Transformer.trans_','') # Actually a regulator, but also has windings
                transformer = model[transformer_name]
                for winding in transformer.windings:
                    if winding.rated_power is not None:
                        required_value = winding.rated_power*row['Loading (p.u.)']*1.1 #*1.1 to oversize a bit more
                        seen_xfmr = False
                        for new_xfmr_size in all_xfmr_sizes:
                            if new_xfmr_size > required_value:
                                winding.rated_power = new_xfmr_size
                                seen_xfmr = True
                                break
                        if not seen_xfmr:
                            winding.rated_power = winding.rated_power*2 #Mostly for regulators 
    
    
            # For each node, find the minimum ampacity of all the non-fuse lines that it connects to
            # Firstly determine  the maximum ampacity of all the wires on a line. Then compute the mimimum ampacity of those lines
            for node in node_lines:
                min_ampacity = 1000000000
                for line in node_lines[node]:
                    max_ampacity = -1
                    for wire in model[line].wires:
                        max_ampacity = max(wire.ampacity,max_ampacity)
                    if max_ampacity == -1:
                        max_ampacity = 1000000000
                    min_ampacity = min(min_ampacity,max_ampacity)
                if min_ampacity != 1000000000:
                    min_node_ampacity[node] = min_ampacity
                else:
                    min_node_ampacity[node] = -1 #i.e. no adjacent lines to the node
    
    
            dss.Fuses.First()
            while True:
                name = dss.Fuses.Name()
                name = name.replace('fuse_','')
                if dss.Fuses.IsBlown():
                    print(wire.interrupting_rating,'blown')
    
                    current_interrupting_rating = -1
                    for wire in model[name].wires:
                        current_interrupting_rating = max(wire.interrupting_rating,current_interrupting_rating)
                    min_adjacent_ampacity = max(min_node_ampacity[model[name].from_element],min_node_ampacity[model[name].to_element])
                    if min_adjacent_ampacity > current_interrupting_rating:
                        for wire in model[name].wires:
                            wire.interrupting_rating = min_adjacent_ampacity
                            print('Fuse',name,'upgraded to have rating of ',min_adjacent_ampacity)
                            dss.Fuses.RatedCurrent(min_adjacent_ampacity)
                    else:
                        print( 'Fuse not upgrade',name, model[name].wires[0].ampacity, min_adjacent_ampacity)
    
                if not dss.Fuses.Next() > 0:
                    break

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Find_Line_Overloads.main()

    
