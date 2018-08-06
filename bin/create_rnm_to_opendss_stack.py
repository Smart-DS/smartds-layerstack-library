import logging
import os

logger = logging.getLogger(__name__)

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack
#from .helpers import layer_library_dir, stack_library_dir, placement_library_dir
layer_library_dir = '../layer_library'
stack_library_dir = '../stack_library'

def create_rnm_to_opendss_stack(dataset_dir, feeder):
    '''Create the stack to convert RNM models in OpenDSS to CYME.'''

    stack = Stack(name='RNM to OpenDSS Stack')

    #Parse load coordinates csv file
    stack.append(Layer(os.path.join(layer_library_dir,'csv_processing')))

    #Parse Capacitor coordinates csv file
    stack.append(Layer(os.path.join(layer_library_dir,'csv_processing')))

    #Read the OpenDSS input model
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))

 #   #Attach timeseries loads
 #   stack.append(Layer(os.path.join(layer_library_dir,'connect_timeseries_loads')))

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
    stack.append(Layer(os.path.join(layer_library_dir,'add_cyme_substations')))

    #Add ltc control settings
    stack.append(Layer(os.path.join(layer_library_dir,'set_ltc_controls')))


    #Find missing coordinates
    stack.append(Layer(os.path.join(layer_library_dir,'find_missing_coords')))

    #Write to OpenDSS
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))


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
    from_opendss.args[1] = os.path.join(feeder,'OpenDSS','BusCoord.dss')
    from_opendss.kwargs['base_dir'] = dataset_dir

    #Timeseries Loads
  #  add_timeseries = stack[3]
  #  add_timeseries.kwargs['customer_file'] = os.path.join(dataset_dir,feeder,'Inputs','customers_ext.txt')
  #  add_timeseries.kwargs['residential_load_data'] = os.path.join(dataset_dir,'GSO_loads','residential','guilford_real_power.dsg')
  #  add_timeseries.kwargs['residential_load_metadata'] = os.path.join(dataset_dir,'GSO_loads','residential','results.csv')
  #  add_timeseries.kwargs['commercial_load_data'] = os.path.join(dataset_dir,'GSO_loads','commercial','com_guilford_real_power.dsg')
  #  add_timeseries.kwargs['commercial_load_metadata'] = os.path.join(dataset_dir,'GSO_loads','commercial','results.csv')
  #  add_timeseries.kwargs['output_folder'] = os.path.join('.','results',feeder)

    #Modify layer
    post_processing = stack[3]
    post_processing.kwargs['path_to_feeder_file'] = os.path.join(dataset_dir,feeder,'Feeders','feeders.txt')
    post_processing.kwargs['path_to_switching_devices_file'] = os.path.join(dataset_dir,feeder,'OpenDSS','SwitchingDevices.dss')

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

    add_substations = stack[8]
    add_substations.args[0] = os.path.join(dataset_dir,feeder,'Feeders', 'feeders.txt')
    add_substations.kwargs['base_dir'] = dataset_dir

    #LTC Controls

    ltc_controls = stack[9]
    ltc_controls.kwargs['setpoint'] = 105

    # Missing coords
    # No args/kwargs for this layer




    #Write to OpenDSS
    final = stack[11]
    final.args[0] = os.path.join('.','results',feeder)
    final.kwargs['separate_feeders'] = False
    final.kwargs['separate_substations'] = False

    stack.save(os.path.join(stack_library_dir,'rnm_to_opendss_stack.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_cyme_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    create_rnm_to_opendss_stack(os.path.join('..','..','dataset_3_20180716', 'MixedHumid'), 'demo2')
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/rnm_to_opendss_stack.json')
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
