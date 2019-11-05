from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import os
import shutil
import numpy as np
from uuid import UUID
import random

from layerstack.args import Arg, Kwarg, ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack
from ditto.dittolayers import DiTToLayerBase

from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.readers.cyme.read import Reader as CymeReader
from ditto.modify.modify import Modifier
from ditto.modify.system_structure import system_structure_modifier
from ditto.models.node import Node
from ditto.models.line import Line
from ditto.models.load import Load
from ditto.models.phase_load import PhaseLoad
from ditto.models.regulator import Regulator
from ditto.models.wire import Wire
from ditto.models.capacitor import Capacitor
from ditto.models.phase_capacitor import PhaseCapacitor
from ditto.models.powertransformer import PowerTransformer
from ditto.models.power_source import PowerSource
from ditto.models.winding import Winding
from ditto.models.phase_winding import PhaseWinding
from ditto.models.timeseries import Timeseries
from ditto.models.position import Position
from ditto.models.feeder_metadata import Feeder_metadata

import pandas as pd

logger = logging.getLogger('layerstack.layers.AddSubstations')


class AddSubstations(DiTToLayerBase):
    name = "Add Substations"
    uuid = UUID("3a5c2446-2836-4744-8a5f-0aa187f6ea75")
    version = 'v0.1.0'
    desc = "Layer to Add CYME substations to the dataset3 model"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('feeder_file', description='', parser=None,
                            choices=None, nargs=None))
        arg_list.append(Arg('output_substation_folder', description='', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['base_dir'] = Kwarg(default=None, description='Base directory for argument paths.')
        kwarg_dict['readme_file'] = Kwarg(default=None,description='Location of readme file')
        kwarg_dict['substation_folder'] = Kwarg(default=None, 
            description="Defaults to this layer's resources folder",
            parser=None, choices=None,nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, feeder_file, output_substation_folder, base_dir=None, readme_file = None, substation_folder=None):
        # Format is max number of feeders, list of substation numbers
        subs_4kv = [(4,[5]),(8,[13]),(12,[14])]
        subs_25kv = [(6,[11]),(12,[15]),(16,[16])]
        subs_1247kv = [(1,[1]),(2,[8]),(3,[2]), (4,[4,10]), (6,[9]), (8,[3,7]), (12,[6]), (16,[12])]
        sub_list = None
        logger.debug("Starting add_cyme_substations")
        if base_dir and (not os.path.exists(feeder_file)):
            feeder_file = os.path.join(base_dir,feeder_file)

        if substation_folder == None:
            substation_folder = os.path.join(os.path.dirname(__file__),'resources')
        elif base_dir and (not os.path.exists(output_substation_folder)):
            output_substation_folder = os.path.join(base_dir,output_substation_folder)

        transformer_config = 'Y' #Default is Delta-Wye. If specified we set it to be wye-wye
        if readme_file is not None and os.path.exists(readme_file):
            f = open(readme_file,'r')
            info = f.readline().split()
            suffix = info[1][:-2]
            config = info[5]
            if config == 'delta-delta':
                transformer_config = 'D'
            kv = int(float(suffix)*1000)
            if suffix == '12.47':
                suffix='1247'
            suffix = '_'+suffix
            if kv == 4000:
                sub_list = subs_4kv
            elif kv == 25000:
                sub_list = subs_25kv
            else:
                sub_list = subs_1247kv
        else:
            kv = 12470
            suffix = '_1247'
            sub_list = subs_1247kv

        from_cyme_layer_dir = None
        # first look in stack
        for layer in stack:
            if layer.name == 'From CYME':
                from_cyme_layer_dir = layer.layer_dir
                break
        # then try this layer's library directory
        if from_cyme_layer_dir is None:
            from_cyme_layer_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),'from_cyme')        
        if not os.path.exists(from_cyme_layer_dir):
            msg = "Cannot find the 'From CYME' layer."
            logger.error(msg)
            raise Exception(msg)



        logger.debug("Building the model network")

        srcs = []
        for obj in model.models:
            if isinstance(obj, PowerSource) and obj.is_sourcebus == 1:
                srcs.append(obj.name)
        srcs = np.unique(srcs)
        if len(srcs)==0:
            raise ValueError('No PowerSource object found in the model.')
        elif len(srcs)>1:
            raise ValueError('Mupltiple sourcebus found: {srcs}'.format(srcs=srcs))
        else:
            source = srcs[0]
        logger.debug("Identifying the Source Bus as {src}".format(src=source))
	


        ''' 
           Substation nodes have the form ***_1247. (or _4 or _25 for 4kv and 25kv systems) 
           The boundary of the substation is ***_69 on the high side.
           The boundary of the substation in a node with no x on the low side
           A feeder defines these boundaries.
           e.g. IHS0_1247->IDT706 is a substation of IHS0_1247 with a boundary of IDT706
           We remove everything between the high and low boundaries when updating a substation
        '''

        model.build_networkx(source) # Used to remove internal edges in substation
        df = pd.read_csv(feeder_file,' ') #The RNM file specifying which feeders belong to which substation
        substation_boundaries_low= {}
        substation_boundaries_high = {}
        substation_transformers = {}
        substation_names = {}
        for index,row in df.iterrows():
            substation = row.iloc[1].lower()
            feeder = row.iloc[2].lower()
            transformer = row.iloc[3].lower()
            transformer = 'tr'+transformer[6:] #The prefix is slightly different with the feeder.txt file
            buses = feeder.split('->')
            bus2 = buses[1]
            bus1 = buses[0]
            if substation in substation_boundaries_low:
                substation_boundaries_low[substation].add(bus2+'-'+bus1+'x') #Set the first node to be the location with one x sign as sometimes there isn't one with xx
                substation_names[bus2+'-'+bus1+'x'] = substation
            else:
                substation_boundaries_low[substation]=set([bus2+'-'+bus1+'x'])
                substation_names[bus2+'-'+bus1+'x'] = substation

            if substation not in substation_boundaries_high:
                substation_boundaries_high[substation] = set([substation.replace(suffix,'_69')]) # All substations are from 69kV

            if substation not in substation_transformers:
                substation_transformers[substation] = set([transformer])


        print(substation_names)
        for sub in substation_boundaries_low.keys(): #sub is the name of the substation and substation_boundaries_low[sub] is a set of all the connected feeders
            logger.debug("Building to_delete and modifier")
            to_delete = Store()
            modifier = Modifier()
            logger.info("Processing substation {}. There are {} in total.".format(sub,len(substation_boundaries_low)))

            all_boundaries = substation_boundaries_low[sub].union(substation_boundaries_high[sub])
            
            # TODO: do a search from the high boundary to the low boundary and include everything inside
            #get_internal_nodes(substation_boundaries_high[sub],substation_boundaries_low[sub])
            

            feeder_names = list(substation_boundaries_low[sub]) # Feeder point of connection to the substation
            internal_nodes = [i for i in model.model_names if sub in i and isinstance(model[i],Node)]
            internal_edges = [i for i in model.model_names if sub in i and (isinstance(model[i],Line) or isinstance(model[i],PowerTransformer))]
            tmp_include_edges = []
            for i in internal_edges:
                if model[i].from_element in feeder_names:
                    internal_nodes.append(model[i].from_element)
                if model[i].to_element in feeder_names:
                    internal_nodes.append(model[i].to_element)
                if 'mv' in model[i].to_element and 'mv' in model[i].from_element:
                    tmp_include_edges.append(i) #Used to address MV loads attached directly to the substation
            for i in tmp_include_edges:
                internal_edges.remove(i)

            high_boundary = list(substation_boundaries_high[sub])[0] #Should only be one high side boundary point in the set
            internal_nodes.append(high_boundary)
            """
            #import pdb;pdb.set_trace()
            all_nodes.append(sub+'-'+high_boundary+'xxx')
            all_nodes.append(sub+'-'+high_boundary+'xx')
            all_nodes.append(sub+'-'+high_boundary+'x')
            all_nodes.append(sub)
            for low_val in substation_boundaries_low[sub]:
                all_nodes.append(low_val)  # End at these nodes. No reclosers after these.
                last_node = low_val+'-'+sub+'x'
                last_node_rev = sub+'-'+low_val+'x'
                if last_node in model.model_names:
                    all_nodes.append(last_node) #The connection point
                if last_node_rev in model.model_names:
                    all_nodes.append(last_node_rev) #The connection point if the name is backwards. Dypically with UMV nodes
                if last_node+'x' in model.model_names:
                    all_nodes.append(last_node+'x') #This extra node often exists 
                if last_node+'_p' in model.model_names:
                    all_nodes.append(last_node+'_p') #This extra node sometimes exists 
                if last_node+'xx' in model.model_names:
                    all_nodes.append(last_node+'xx') #This extra node sometimes exists too
            """                
            all_nodes_set = set(internal_nodes)
            #internal_edges = model.get_internal_edges(all_nodes_set)
            #import pdb;pdb.set_trace()

            # These attribuetes will be used to inform which substation is selected
            rated_power = None
            emergency_power = None
            loadloss = None
            noloadloss = None
            reactance = None
            lat = None
            long = None
            transformer = list(substation_transformers[sub])[0] # Assume only one transformer per substation in RNM

# Currently using CYME reader which has different names for the transformers to the feeders.txt file                
#            reactance = model[transformer].reactances[0] # Assume the same for all windings in a substation
#            loadloss = model[transformer].loadloss
#            noloadloss = model[transformer].noload_loss
#            rated_power = model[transformer].windings[0].rated_power # Assume the same for all windings in a substation
#            emergency_power = model[transformer].windings[0].emergency_power # Assume the same for all windings in a substation
            try:
                lat = model[sub].positions[0].lat
                long = model[sub].positions[0].long
            except:
                raise ValueError('{} missing position elements'.format(model[sub].name))

           # import pdb;pdb.set_trace()
            # Mark the internals of the substation for deletion
            for n in all_nodes_set:
                if not n in model.model_names:
                    continue
#                is_endpoint = False
#                for key in substation_boundaries_low:
#                    if n in substation_boundaries_low[key]: #Don't delete the boundaries of the substation
#                        is_endpoint = True
#                        break
#                if is_endpoint:
#                    continue
                obj_name = type(model[n]).__name__
                base_obj = globals()[obj_name](to_delete)
                base_obj.name = n
            for e in internal_edges:
                if not e in model.model_names:
                    continue
                if  model[e].from_element in feeder_names: #Don't remove edge from bus2-bus1-x to the first distribution transformer
                    continue
                obj_name = type(model[e]).__name__
                base_obj = globals()[obj_name](to_delete)
                base_obj.name = e

            num_model_feeders = len(feeder_names)
            not_allocated = True
            
            low_voltage = kv
            high_voltage = 69000

            #import pdb;pdb.set_trace()
            # Read the CYME models
            random.seed(0)
            for element in sub_list: # Insert extra logic here to determine which one to use
                if num_model_feeders>element[0]:
                    continue

                sub_file = 'sb'+str(element[1][random.randint(0,len(element[1])-1)])
                print(sub_file)
                sub_model = Store()
                reader  = CymeReader(data_folder_path=os.path.join(os.path.dirname(__file__),'resources',sub_file))
                reader.parse(sub_model)
                sub_model.set_names()
                                     
                # Set the nominal voltages within the substation using the cyme model transformer and source voltage
                modifier = system_structure_modifier(sub_model)
                modifier.set_nominal_voltages_recur()

                # Determine which nodes in the CYME model connect feeders/HV
                all_substation_connections = []
                available_feeders = 0
                for i in sub_model.models:
                    if isinstance(i,Node) and hasattr(i,'is_substation_connection') and i.is_substation_connection == 1:
                        all_substation_connections.append(i)
                        i.setpoint = 1.03
                        try:
                            if i.nominal_voltage == low_voltage:
                                available_feeders+=1
                        except:
                            raise ValueError("Nominal Voltages not set correctly in substation")


                logger.info("Processing substation {}. There are {} feeders available and {} feeders in RNM".format(sub,available_feeders,num_model_feeders))
                if available_feeders >= num_model_feeders:
                    boundry_map = {}
                    feeder_cnt = 0
                    ref_lat = 0
                    ref_long = 0
                    for i in sub_model.models:
                        # Remove the source node. This is no longer needed
                        if isinstance(i,PowerSource):
                            sub_model.remove_element(i)



                        # Set a random node as the reference node
                        if isinstance(i,Node) and hasattr(i,'positions') and len(i.positions) >0 and hasattr(i.positions[0],'lat') and i.positions[0].lat is not None and hasattr(i.positions[0],'long') and i.positions[0].long is not None:
                            ref_lat = i.positions[0].lat
                            ref_long = i.positions[0].long


                    substation_name = substation_names[feeder_names[0].lower()]
                    for i in sub_model.models:

                        # Remove feeder name from substation elements. This is normally set automatically when reading from CYME
                        if hasattr(i,'feeder_name'): 
                            i.feeder_name = '' 
                        if hasattr(i,'substation_name'): 
                            i.substation_name = substation_name 
                        if hasattr(i,'is_substation'): 
                            i.is_substation = True 
                        
                        if isinstance(i,PowerTransformer) and transformer_config =='D' and i.windings is not None and len(i.windings) == 2 and i.windings[1] is not None:
                            i.windings[1].connection_type = 'D'



                        # Assign feeder names to the endpoints of the substation 
                        if isinstance(i,Node) and hasattr(i,'is_substation_connection') and i.is_substation_connection == 1:
                            if hasattr(i,'nominal_voltage') and i.nominal_voltage is not None and i.nominal_voltage>=high_voltage:
                            
#########  USE no_feeders.txt to inform how many connection points there should be. Skip this substation if the number isn't correct-->>>>
#### Need to discuss with Carlos                            
                                boundry_map[i.name] = high_boundary
                                i.setpoint = 1.0
                                i.name = high_boundary #TODO: issue of multiple high voltage inputs needs to be addressed
                                #i.feeder_name = 'subtransmission'
                                i.substation_name = substation_name
                                i.is_substation = False
                            elif hasattr(i,'nominal_voltage') and i.nominal_voltage is not None and i.nominal_voltage<high_voltage:
                                feeder_cnt+=1
                                if feeder_cnt<=num_model_feeders:
                                    endpoint = feeder_names[feeder_cnt-1].split('-')[0]
                                    if 'mv' in endpoint: #The node names for these are reversed for some reason
                                        boundry_map[i.name] = substation_name+'-'+endpoint+'x'
                                        i.name = substation_name+'-'+endpoint+'x' 
                                        if i.name in all_nodes_set:
                                            all_nodes_set.remove(i.name)
                                    else:
                                        boundry_map[i.name] = feeder_names[feeder_cnt-1]
                                        i.name = feeder_names[feeder_cnt-1].lower() 
                                    i.substation_name = substation_name
                                    i.is_substation = False
                                    i.feeder_name = i.substation_name+'->'+endpoint
                                    #import pdb;pdb.set_trace()
                                    if i.substation_name+'->'+endpoint in model.model_names: # Set the Feedermetadata headnode to be the correct name.
                                        model[i.substation_name+'->'+endpoint].headnode=i.name 
                                else:
                                    i.name = str(sub_file+'_'+sub+'_'+i.name).lower() #ie. No feeders assigned to this berth so using the substation identifiers
                            else:
                                raise ValueError("Nominal Voltages not set correctly in substation")

                        elif hasattr(i,'name') and (not isinstance(i,Feeder_metadata)): 
                            i.name = str(sub_file+'_'+sub+'_'+i.name).lower()
                        if isinstance(i,Regulator) and hasattr(i,'connected_transformer') and i.connected_transformer is not None:
                            i.connected_transformer = str(sub_file+'_'+sub+'_'+i.connected_transformer).lower()

                        if hasattr(i,'from_element') and i.from_element is not None:
                            if i.from_element in boundry_map:
                                i.from_element = boundry_map[i.from_element]
                            else:
                                i.from_element = str(sub_file + '_'+sub + '_'+i.from_element).lower()
                        if hasattr(i,'to_element') and i.to_element is not None:
                            if i.to_element in boundry_map:
                                i.to_element = boundry_map[i.to_element]
                            else:
                                i.to_element = str(sub_file + '_'+sub + '_'+i.to_element).lower()


                        if hasattr(i,'positions') and i.positions is not None and len(i.positions)>0:
                           # import pdb;pdb.set_trace()
                            if ref_long ==0 and ref_lat ==0:
                                logger.warning("Warning: Reference co-ords are (0,0)")
                            scale_factor = 1
                            if element[0]>=12: # The larger substations were created with a strange scale factor
                                scale_factor = 1/50.0
                            i.positions[0].lat = scale_factor*7*(i.positions[0].lat-ref_lat) + lat
                            i.positions[0].long = scale_factor*10*(i.positions[0].long-ref_long) + long
                            if len(i.positions)>1:
                                for k in range(1,len(i.positions)):
                                    i.positions[k].lat = scale_factor*7*(i.positions[k].lat-ref_lat) + lat
                                    i.positions[k].long = scale_factor*10*(i.positions[k].long-ref_long) + long
#import pdb;pdb.set_trace()
                    not_allocated = False
                    sub_model.set_names()
                    to_delete.set_names()
                    reduced_model = modifier.delete(model, to_delete) 
                    logger.info("Adding model from {} to model".format(substation_folder))
                    #import pdb;pdb.set_trace()
                    model = modifier.add(reduced_model, sub_model) #Is it a problem to be modifying the model directly? 
                    break
            if not_allocated:
                raise ValueError('Substation too small. {num} feeders needed.  Exiting...'.format(num=num_model_feeders))

        model.set_names()
        logger.debug("Returning {!r}".format(model))
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    AddSubstations.main()
    
