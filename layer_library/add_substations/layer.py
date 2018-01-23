from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import os
import shutil

from ditto.layers.args import Arg, Kwarg
from ditto.layers.layer import ModelType, ModelLayerBase
from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.readers.opendss.read import reader as OpenDSSReader
from ditto.modify.modify import Modifier
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

from src.layers.from_opendss.layer import From_Opendss
from ditto.layers.stack import Stack

import pandas as pd

logger = logging.getLogger('ditto.layers.Add_Substations')


class Add_Substations(ModelLayerBase):
    name = "Add_Substations"
    desc = "Layer to Add substations to the dataset3 model"
    model_type = 1

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('arg_name', description='', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['kwarg_name'] = Kwarg(default=None, description='',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, feeder_file,substation_folder,output_substation_folder):
        model.build_networkx() # Used to remove internal edges in substation
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

        to_delete = Store()
        modifier = Modifier()
        for sub in substations: #sub is the name of the substation and substations[sub] is a set of all the connected feeders
            all_nodes = []
            subname = sub.replace('.','')
            subname = subname.lower()
            all_nodes.append(subname)
            hv_subname = subname+'->'+subname.replace('1247','69')+'_s'
            all_nodes.append(hv_subname)
            sourcenode = hv_subname+'_s' #Source point of connection to the substation
            all_nodes.append(sourcenode)
            feeder_names = [] # Feeder point of connection to the substation
            rated_power = None
            emergency_power = None
            loadloss = None
            noloadloss = None
            reactance = None
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

                base_obj = globals()[obj_name](to_delete)
                base_obj.name = e

            num_model_feeders = len(substations[sub])
            not_allocated = True
            # Write the substation files to disk. These are then read and added            
            for sub_file in os.listdir(substation_folder): # Important these must be listed in increasing order
                if len(pd.read_csv(substation_folder+'/%s/feeders.csv'%sub_file))>= num_model_feeders:
                    generic_source = list(pd.read_csv(substation_folder+'/%s/source.csv'%sub_file)['source'])
                    generic_feeders = list(pd.read_csv(substation_folder+'/%s/feeders.csv'%sub_file)['feeders'])[:num_model_feeders] #Select the first n feeder bays of the substation as required
                    generic_nodes = list(pd.read_csv(substation_folder+'/%s/all_nodes.csv'%sub_file)['node'])
                    generic_substation_fp = open(substation_folder+'/%s/%s.dss'%(sub_file,sub_file),'r')
                    generic_substation_dss = generic_substation_fp.read()
                    generic_substation_fp.close()
                    substation_dss = generic_substation_dss.replace(generic_source[0],'%s'%sourcenode) # Replace source node
                    for i in range(len(feeder_names)):
                        substation_dss = substation_dss.replace(generic_feeders[i],'%s'%feeder_names[i]) # Replace feeder nodes

                    # TODO: do this in a better way.
                    for i in range(len(generic_nodes)): #Replace any remaining nodes that haven't been changed yet. Unallocated feeder heads are managed here
                        substation_dss = substation_dss.replace(generic_nodes[i]+ ' ','%s_%s_%s '%(sub_file,subname,generic_nodes[i]))
                        substation_dss = substation_dss.replace(generic_nodes[i]+ '.','%s_%s_%s.'%(sub_file,subname,generic_nodes[i]))
                    substation_dss = substation_dss.replace('Line.','Line.%s_%s_'%(sub_file,subname))
                    substation_dss = substation_dss.replace('LineCode.','LineCode.%s_%s_'%(sub_file,subname))
                    substation_dss = substation_dss.replace('Capacitor.','Capacitor.%s_%s_'%(sub_file,subname))
                    substation_dss = substation_dss.replace('CapControl.','CapControl.%s_%s_'%(sub_file,subname))
                    substation_dss = substation_dss.replace('Monitor.','Monitor.%s_%s_'%(sub_file,subname))
                    substation_dss = substation_dss.replace('Relay.','Relay.%s_%s_'%(sub_file,subname))
                    substation_dss = substation_dss.replace('Transformer.','Transformer.%s_%s_'%(sub_file,subname))
                    substation_dss = substation_dss.replace('transformer=','transformer=%s_%s_'%(sub_file,subname))
                    substation_dss = substation_dss.replace('Regcontrol.','Regcontrol.%s_%s_'%(sub_file,subname))

                    # TODO: WARNING: This is a total hack to replace the substation attributes and should not be used long-term.
                    # This is very specific to the substations used in dataset3 and is very case sensative.
                    substation_dss = substation_dss.replace('kvas=(30000, 30000)','kvas=(%f, %f)'%(rated_power,rated_power))
                    substation_dss = substation_dss.replace('kvas=(25000, 25000)','kvas=(%f, %f)'%(rated_power/3.0,rated_power/3.0))
                    substation_dss = substation_dss.replace('%noloadloss=0.12','%noloadloss={noll}'.format(noll=noloadloss))
                    substation_dss = substation_dss.replace('%loadloss=0.1','%loadloss={ll}'.format(ll=loadloss))
                    substation_dss = substation_dss.replace('XHL=0.1','XHL=%f'%(reactance))

                    if not os.path.isdir(output_substation_folder+'/%s'%subname):
                        os.makedirs(output_substation_folder+'/%s'%subname)
                    substation_output = open(output_substation_folder+'/%s/substation.dss'%(subname),'w')
                    substation_output.write(substation_dss)
                    substation_output.close()
                    buscoords = open(output_substation_folder+'/%s/Buscoords.dss'%subname,'w')
                    buscoords.close()
                    masterfile_fp = open(substation_folder+'/%s/master.dss'%sub_file,'r')
                    masterfile_dss = masterfile_fp.read()
                    masterfile_fp.close()
                    masterfile_dss = masterfile_dss.replace('SourceBus',sourcenode)
                    master_output = open(output_substation_folder+'/%s/master.dss'%subname,'w')
                    master_output.write(masterfile_dss)
                    master_output.close()
                    #shutil.copyfile(substation_folder+'/%s/master.dss'%sub_file,output_substation_folder+'/%s/master.dss'%subname)
                    not_allocated = False
                    break
            if not_allocated:
                raise('Substation too small. %d feeders needed.  Exiting...'%(num_model_feeders))

        reduced_model = modifier.delete(model, to_delete) 
        final_model = reduced_model
        for sub_folder in os.listdir(output_substation_folder):
            sub_master = os.path.join(output_substation_folder,sub_folder,'master.dss')
            sub_bus_coords = os.path.join(output_substation_folder, sub_folder, 'Buscoords.dss')
            from_opendss_sub = From_Opendss()
            stack_sub = Stack([from_opendss_sub])
            substation_model = Store()
            substation_model = from_opendss_sub.apply(stack_sub, substation_model, sub_master, sub_bus_coords,read_power_source=False)

            final_model = modifier.add(final_model, substation_model)
        return final_model





if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    Add_Substations.main()
