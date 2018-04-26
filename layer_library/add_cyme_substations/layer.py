from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import os
import shutil
import numpy as np
from uuid import UUID

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
        kwarg_dict['substation_folder'] = Kwarg(default=None, 
            description="Defaults to this layer's resources folder",
            parser=None, choices=None,nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, feeder_file, output_substation_folder, base_dir=None, substation_folder=None):
        logger.debug("Starting add_cyme_substations")
        if base_dir and (not os.path.exists(feeder_file)):
            feeder_file = os.path.join(base_dir,feeder_file)

        if substation_folder == None:
            substation_folder = os.path.join(os.path.dirname(__file__),'resources')
        elif base_dir and (not os.path.exists(output_substation_folder)):
            output_substation_folder = os.path.join(base_dir,output_substation_folder)

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
           Substation nodes have the form ***_1247. 
           The boundary of the substation is ***_69 on the high side.
           The boundary of the substation in a node with no % on the low side
           A feeder defines these boundaries.
           e.g. IHS0_1247->IDT706 is a substation of IHS0_1247 with a boundary of IDT706
           We remove everything between the high and low boundaries when updating a substation
        '''

        model.build_networkx(source) # Used to remove internal edges in substation
        df = pd.read_csv(feeder_file,' ') #The RNM file specifying which feeders belong to which substation
        substation_boundaries_low= {}
        substation_boundaries_high = {}
        substation_transformers = {}
        for index,row in df.iterrows():
            substation = row.iloc[1].lower()
            feeder = row.iloc[2].lower()
            transformer = row.iloc[3].lower()
            transformer = 'tr'+transformer[6:] #The prefix is slightly different with the feeder.txt file
            buses = feeder.split('->')
            bus2 = buses[1]
            if substation in substation_boundaries_low:
                substation_boundaries_low[substation].add(bus2)
            else:
                substation_boundaries_low[substation]=set([bus2])

            if substation not in substation_boundaries_high:
                substation_boundaries_high[substation] = set([substation.replace('_1247','_69')])

            if substation not in substation_transformers:
                substation_transformers[substation] = set([transformer])


        for sub in substation_boundaries_low.keys(): #sub is the name of the substation and substation_boundaries_low[sub] is a set of all the connected feeders
            logger.debug("Building to_delete and modifier")
            to_delete = Store()
            modifier = Modifier()
            logger.info("Processing substation {}. There are {} in total.".format(sub,len(substation_boundaries_low)))

            all_boundaries = substation_boundaries_low[sub].union(substation_boundaries_high[sub])
            
            # TODO: do a search from the high boundary to the low boundary and include everything inside
            #get_internal_nodes(substation_boundaries_high[sub],substation_boundaries_low[sub])
            

            all_nodes = []

            high_boundary = list(substation_boundaries_high[sub])[0] #Should only be one high side boundary point in the set
            all_nodes.append(high_boundary)
            all_nodes.append(sub+'>'+high_boundary+'%%%')
            all_nodes.append(sub+'>'+high_boundary+'%%')
            all_nodes.append(sub+'>'+high_boundary+'%')
            all_nodes.append(sub)
            for low_val in substation_boundaries_low[sub]:
                all_nodes.append(low_val+'>'+sub+'%%')
                all_nodes.append(low_val+'>'+sub+'%')
                all_nodes.append(low_val)
                
            all_nodes_set = set(all_nodes)
            internal_edges = model.get_internal_edges(all_nodes_set)

            feeder_names = list(substation_boundaries_low[sub]) # Feeder point of connection to the substation
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

            # Mark the internals of the substation for deletion
            for n in all_nodes_set:
                obj_name = type(model[n]).__name__
                base_obj = globals()[obj_name](to_delete)
                base_obj.name = n
            for e in internal_edges:
                obj_name = type(model[e]).__name__
                base_obj = globals()[obj_name](to_delete)
                base_obj.name = e

            num_model_feeders = len(feeder_names)
            not_allocated = True
            
            low_voltage = 12470
            high_voltage = 69000

            # Read the CYME models
            for sub_file in os.listdir(substation_folder): # Insert extra logic here to determine which one to use
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
                        try:
                            if i.nominal_voltage == low_voltage:
                                available_feeders+=1
                        except:
                            import pdb;pdb.set_trace()
                            raise ValueError("Nominal Voltages not set correctly in substation")


                logger.info("Processing substation {}. There are {} feeders available and {} feeders in RNM".format(sub,available_feeders,num_model_feeders))
                if available_feeders >= num_model_feeders:
                    feeder_cnt = 0
                    ref_lat = 0
                    ref_long = 0
                    for i in sub_model.models:
                        if isinstance(i,PowerTransformer) and hasattr(i,'positions') and len(i.positions) >0 and hasattr(i.positions[0],'lat') and i.positions[0].lat is not None and hasattr(i.positions[0],'long') and i.positions[0].long is not None:
                            ref_lat = i.positions[0].lat
                            ref_long = i.positions[0].long
                    for i in sub_model.models:

                        # Remove feeder name from substation elements. This is normally set automatically when reading from CYME
                        if hasattr(i,'feeder_name'): 
                            i.feeder_name = None 


                        # Assign feeder names to the endpoints of the substation 
                        if isinstance(i,Node) and hasattr(i,'is_substation_connection') and i.is_substation_connection == 1:
                            if hasattr(i,'nominal_voltage') and i.nominal_voltage is not None and i.nominal_voltage>=high_voltage:
                            
#########  USE no_feeders.txt to inform how many connection points there should be. Skip this substation if the number isn't correct-->>>>
#### Need to discuss with Carlos                            
                                i.name = high_boundary #TODO: issue of multiple high voltage inputs needs to be addressed
                                i.feeder = 'subtransmission' #i.e. connect to the subtransmission network
                            elif hasattr(i,'nominal_voltage') and i.nominal_voltage is not None and i.nominal_voltage<high_voltage:
                                feeder_cnt+=1
                                if feeder_cnt<=num_model_feeders:
                                    i.name = feeder_names[feeder_cnt-1] 
                                    i.feeder_name = i.name #Set the feeder the be this node
                                else:
                                    i.name = sub_file+'_'+sub+'_'+i.name #ie. No feeders assigned to this berth so using the substation identifiers
                            else:
                                raise ValueError("Nominal Voltages not set correctly in substation")

                        elif hasattr(i,'name') and (not isinstance(i,Feeder_metadata)): 
                            i.name = sub_file+'_'+sub+'_'+i.name
                        if isinstance(i,Regulator) and hasattr(i,'connected_transformer') and i.connected_transformer is not None:
                            i.connected_transformer = sub_file+'_'+sub+'_'+i.connected_transformer

                        if hasattr(i,'from_element') and i.from_element is not None:
                            i.from_element = sub_file + '_'+sub + '_'+i.from_element
                        if hasattr(i,'to_element') and i.to_element is not None:
                            i.to_element = sub_file + '_'+sub + '_'+i.to_element


                        if hasattr(i,'positions') and i.positions is not None and len(i.positions)>0:
                            if ref_long ==0 and ref_lat ==0:
                                logger.warning("Warning: Reference co-ords are (0,0)")
                            i.positions[0].lat = i.positions[0].lat-ref_lat + lat
                            i.positions[0].long = i.positions[0].long-ref_long + long
                    not_allocated = False
                    reduced_model = modifier.delete(model, to_delete) 
                    logger.info("Adding model from {} to model".format(substation_folder))
                    model = modifier.add(reduced_model, sub_model) #Is it a problem to be modifying the model directly? 
                    break
            if not_allocated:
                raise ValueError('Substation too small. {num} feeders needed.  Exiting...'.format(num=num_model_feeders))

        model.set_names()
# modifier = system_structure_modifier(model,'st_mat_src')
#        modifier.set_nominal_voltages_recur()
        logger.debug("Returning {!r}".format(model))
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    AddSubstations.main()
    
