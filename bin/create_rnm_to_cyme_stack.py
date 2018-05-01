import logging
import os

logger = logging.getLogger(__name__)

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack
#from .helpers import layer_library_dir, stack_library_dir, placement_library_dir
layer_library_dir = '../layer_library'
stack_library_dir = '../stack_library'

def create_rnm_to_cyme_stack(dataset_dir, feeder):
    '''Create the stack to convert RNM models in OpenDSS to CYME.'''

    stack = Stack(name='RNM to CYME Stack')

    #Parse load coordinates csv file
    stack.append(Layer(os.path.join(layer_library_dir,'csv_processing')))

    #Parse Capacitor coordinates csv file
    stack.append(Layer(os.path.join(layer_library_dir,'csv_processing')))
	
    #Read the OpenDSS input model
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))
	
    #Modify the model
    stack.append(Layer(os.path.join(layer_library_dir,'post-processing')))

    #Add the load coordinates with a model merge
    stack.append(Layer(os.path.join(layer_library_dir,'merging-layer')))

    #Add the capacitor coordinates with a model merge
    stack.append(Layer(os.path.join(layer_library_dir,'merging-layer')))

    #Split the network into feeders
    stack.append(Layer(os.path.join(layer_library_dir,'network_split')))

    #Add intermediate node coordinates
    stack.append(Layer(os.path.join(layer_library_dir,'intermediate_node')))

    #Add cyme substations
#stack.append(Layer(os.path.join(layer_library_dir,'add_cyme_substations')))


    #Find missing coordinates
    stack.append(Layer(os.path.join(layer_library_dir,'find_missing_coords')))

    #Write to CYME
    stack.append(Layer(os.path.join(layer_library_dir,'to_cyme')))


    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Load coordinate layer
    load_coordinates = stack[0]
    load_coordinates.kwargs['input_filename'] = os.path.join(dataset_dir,feeder,'IntermediateFormat','Loads_IntermediateFormat.csv')
    load_coordinates.kwargs['output_filename'] = os.path.join(dataset_dir,feeder,'IntermediateFormat','Loads_IntermediateFormat2.csv')
    load_coordinates.kwargs['object_name'] = 'Load'

    #Capacitor coordinate layer
    capacitor_coordinates = stack[1]
    capacitor_coordinates.kwargs['input_filename'] = os.path.join(dataset_dir,feeder,'IntermediateFormat','Capacitors_IntermediateFormat.csv')
    capacitor_coordinates.kwargs['output_filename'] = os.path.join(dataset_dir,feeder,'IntermediateFormat','Capacitors_IntermediateFormat2.csv')
    capacitor_coordinates.kwargs['object_name'] = 'Capacitor'

    #Read OpenDSS layer
    from_opendss = stack[2]
    from_opendss.args[0] = os.path.join(feeder,'OpenDSS','Master.dss')
    from_opendss.args[1] = os.path.join(feeder,'OpenDSS','Buscoord.dss')
    from_opendss.kwargs['base_dir'] = dataset_dir

    #Modify layer
    #No input except the model. Nothing to do here...
    post_processing = stack[3]
    post_processing.kwargs['path_to_feeder_file'] = os.path.join(dataset_dir,feeder,'Feeders','feeders.txt')


    #Merging Load layer
    merging_load = stack[4]
    merging_load.kwargs['filename'] = os.path.join(dataset_dir,feeder,'IntermediateFormat','Loads_IntermediateFormat2.csv')
	
    #Merging Capacitor Layer
    merging_caps = stack[5]
    merging_caps.kwargs['filename'] = os.path.join(dataset_dir,feeder,'IntermediateFormat','Capacitors_IntermediateFormat2.csv')

    #Splitting layer
    split = stack[6]
    split.kwargs['path_to_feeder_file'] = os.path.join(dataset_dir,feeder,'Feeders','feeders.txt')

    #Intermediate node layer
    inter = stack[7]
    inter.kwargs['filename'] = os.path.join(dataset_dir,feeder,'OpenDSS','LineCoord.txt')

    #Substations

#    add_substations = stack[8]
#    add_substations.args[0] = os.path.join(dataset_dir,feeder,'Feeders', 'feeders.txt')
#    add_substations.kwargs['base_dir'] = dataset_dir

    # Missing coords
    # No args/kwargs for this layer

    #Write to CYME
    final = stack[9]
    final.args[0] = os.path.join('.','results')

    stack.save(os.path.join(stack_library_dir,'rnm_to_cyme_stack.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
    create_rnm_to_cyme_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/rnm_to_cyme_stack.json')
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
