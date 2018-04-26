from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

from ditto.metrics.network_analysis import network_analyzer

logger = logging.getLogger('layerstack.layers.Network_Split')


class Network_Split(DiTToLayerBase):
    name = "network_split"
    uuid = "UUID(5e2849d9-7f25-499b-a5f7-b1f85e97dde9)"
    version = '0.1.0'
    desc = "Use information from feeder.txt to split the network into different feeders"

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
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        if 'path_to_feeder_file' in kwargs:
            path_to_feeder_file = kwargs['path_to_feeder_file']       

        #Open and read feeder.txt
        with open(path_to_feeder_file, 'r') as f:
            lines = f.readlines()
    
        #Parse feeder.txt to have the feeder structure of the network
        feeders = {}
        substations = {}
        substation_transformers = {}

        for line in lines[1:]:
    
            #Parse the line
            node,sub,feed,sub_trans = map(lambda x:x.strip(), line.split(' '))
    
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

        #Create a network analyzer object
        network_analyst = network_analyzer(model)

        #Add the feeder information to the network analyzer
        network_analyst.add_feeder_information(list(feeders.keys()),
        	                                   list(feeders.values()),
                    	                       substations,
                            	               '') #TODO find a way to get the feeder type

        #Split the network into feeders
        network_analyst.split_network_into_feeders()

        #Tag the objects
        network_analyst.tag_objects()

        #Set the names
        network_analyst.model.set_names()

        #Return the model
        return network_analyst.model

if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Network_Split.main()

    
