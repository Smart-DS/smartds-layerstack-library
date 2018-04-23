from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import os
import shutil
from uuid import UUID

from layerstack.args import Arg, Kwarg, ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack
from ditto.dittolayers import DiTToLayerBase

from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.readers.cyme.read import reader as CymeReader
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
from ditto.models.winding import Winding
from ditto.models.phase_winding import PhaseWinding
from ditto.models.timeseries import Timeseries
from ditto.models.position import Position

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
        if base_dir and (not os.path.exists(output_substation_folder)):
            output_substation_folder = os.path.join(base_dir,output_substation_folder)

        if substation_folder == None:
            substation_folder = os.path.join(os.path.dirname(__file__),'resources')

        # Need to load OpenDSS files later. Make sure we can find the required layer.
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

        model.build_networkx(source=None) # Used to remove internal edges in substation
        df = pd.read_csv(feeder_file,' ') #The RNM file specifying which feeders belong to which substation
        substations = {}
        for index,row in df.iterrows():
            substation = row.iloc[1]
            feeder = row.iloc[2]
            buses = feeder.split('->')
            bus1 = buses[1]
            bus2 = buses[0]
            if bus1[0:4].lower() == 'ucmv': # Not swapped if MV load connected to it
                bus1 = buses[0]
                bus2 = buses[1]
            adjusted_feeder = bus1+'->'+bus2 #In the feeder file bus1 and bus2 are swapped
            if substation in substations:
                substations[substation].add(adjusted_feeder)
            else:
                substations[substation]=set([adjusted_feeder])

        logger.debug("Building to_delete and modifier")

        to_delete = Store()
        modifier = Modifier()
        for sub in substations: #sub is the name of the substation and substations[sub] is a set of all the connected feeders
            logger.debug("Processing substation {}. There are {} in total.".format(sub,len(substations)))

            all_nodes = []
            subname = sub.replace('.','')
            subname = subname.lower()
            all_nodes.append(subname)
            hv_subname = subname+'->'+subname.replace('1247','69')+'_s'
            all_nodes.append(hv_subname)
            sourcenode = hv_subname+'_s' #Source point of connection to the substation
            all_nodes.append(sourcenode)
            feeder_names = [] # Feeder point of connection to the substation
            # These attribuetes will be used to inform which substation is selected
            rated_power = None
            emergency_power = None
            loadloss = None
            noloadloss = None
            reactance = None
            lat = None
            long = None
            for feeder in substations[sub]:
                feeder_name = feeder.replace('.','')+'_s'
                feeder_name = feeder_name.lower()
                feeder_names.append(feeder_name)
                all_nodes.append(feeder_name)

            all_nodes_set = set(all_nodes)
            internal_edges = model.get_internal_edges(all_nodes_set)
            for n in all_nodes_set:
                obj_name = type(model[n]).__name__
                base_obj = globals()[obj_name](to_delete)
                base_obj.name = n
            for e in internal_edges:
                obj_name = type(model[e]).__name__
                if obj_name == 'PowerTransformer':
                    reactance = model[e].reactances[0] # Assume the same for all windings in a substation
                    loadloss = model[e].loadloss
                    noloadloss = model[e].noload_loss
                    rated_power = model[e].windings[0].rated_power # Assume the same for all windings in a substation
                    emergency_power = model[e].windings[0].emergency_power # Assume the same for all windings in a substationr
                    lat = model[e].positions[0].lat
                    long = model[e].positions[0].long

                base_obj = globals()[obj_name](to_delete)
                base_obj.name = e

            num_model_feeders = len(substations[sub])
            not_allocated = True
            # Read the CYME models
            for sub_file in os.listdir(substation_folder): # Important these must be listed in increasing order
                sub_model = Store()
                reader  = CymeReader(data_folder_path=os.path.join(current_directory, 'resources',sub_model))
                reader.parse(sub_model)
                sub_model.set_names()
                modifier = system_structure_modifier(sub_model)
                modifier.set_nominal_voltages_recur()
                all_substation_connections = []
                for i in sub_model.models:
                    if isinstance(i,Node) and hasattr(i,'is_substation_connection') and i.is_substation_connection == 1:
                        all_substation_connections.append(i)
                if len(all_substation_connections) > num_model_feeders:
                    feeder_cnt = 0
                    for i in sub_model.models:
                        if isinstance(i,PowerTransformer) and hasattr(i,'positions') and len(i.positions) >0 and hasattr(i.positions[0],'lat') and i.positions[0].lat is not None and hasattr(i.positions[0],'long') and i.positions[0].long is not None:
                            ref_lat = i.positions[0].lat
                            ref_long = i.positions[0].long
                    for i in sub_model.models:
                        if isinstance(i,Node) and hasattr(i,'is_substation_connection') and i.is_substation_connection == 1:
                            if hasattr(i,'nominal_voltage') and i.nominal_voltage is not None and i.nominal_voltage>=69:
                                i.name = sourcenode #TODO: issue of multiple high voltage inputs needs to be addressed
                            elif hasattr(i,'nominal_voltage') and i.nominal_voltage is not None and i.nominal_voltage<69:
                                if feeder_cnt<len(feeder_name):
                                    i.name = feeder_name[feeder_cnt] 
                                    feeder_cnt+=1
                                else:
                                    i.name = sub_file+'_'+subname+'_'+i.name #ie. No feeders assigned to this berth
                            else:
                                raise('Nominal voltage unknown - upable to assign feeders')

                        else: 
                            i.name = sub_file+'_'+subname+'_'+i.name

                        i.positions[0].lat = i.positions[0].lat-ref_lat + lat
                        i.positions[0].long = i.positions[0].long-ref_long + long
                    reduced_model = modifier.delete(model, to_delete) 
                    logger.debug("Adding model from {} to final_model".format(sub_folder))
                    model = modifier.add(reduced_model, sub_model) #Is it a problem to be modifying the model directly? 
                    not_allocated = False
                    break
            if not_allocated:
                raise('Substation too small. %d feeders needed.  Exiting...'%(num_model_feeders))

        logger.debug("Returning {!r}".format(final_model))
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    AddSubstations.main()
    
