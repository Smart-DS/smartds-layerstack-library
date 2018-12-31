import sys
import logging
import os

logger = logging.getLogger(__name__)

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack
#from .helpers import layer_library_dir, stack_library_dir, placement_library_dir
layer_library_dir = '../layer_library'
stack_library_dir = '../stack_library'

def create_rnm_to_cyme_stack(dataset_dir, region):
    '''Create the stack to convert RNM models in OpenDSS to CYME.'''

    stack = Stack(name='RNM to CYME Stack')

    #Parse load coordinates csv file
    stack.append(Layer(os.path.join(layer_library_dir,'csv_processing')))

    #Parse Capacitor coordinates csv file
    stack.append(Layer(os.path.join(layer_library_dir,'csv_processing')))

    #Read the OpenDSS input model
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))

    #Add regulators with setpoints
    stack.append(Layer(os.path.join(layer_library_dir,'add_rnm_regulators')))

    #Ensure all LV lines are triplex
    stack.append(Layer(os.path.join(layer_library_dir,'set_lv_as_triplex')))

    #Modify the model
    stack.append(Layer(os.path.join(layer_library_dir,'post-processing')))

    #Add the load coordinates with a model merge
    stack.append(Layer(os.path.join(layer_library_dir,'merging-layer')))

    #Add the capacitor coordinates with a model merge
    stack.append(Layer(os.path.join(layer_library_dir,'merging-layer')))

    #Set number of customers
    stack.append(Layer(os.path.join(layer_library_dir,'set_num_customers')))

    #Split the network into feeders
    stack.append(Layer(os.path.join(layer_library_dir,'network_split')))

    #Calculate metrics on customer per transfomer
    stack.append(Layer(os.path.join(layer_library_dir,'partitioned_customers_per_transformer_plots')))

    #Add intermediate node coordinates
    stack.append(Layer(os.path.join(layer_library_dir,'intermediate_node')))

    #Find missing coordinates
    stack.append(Layer(os.path.join(layer_library_dir,'find_missing_coords')))

    #Adjust overlaid nodes
    stack.append(Layer(os.path.join(layer_library_dir,'move_overlayed_nodes')))

    #Add cyme substations
    stack.append(Layer(os.path.join(layer_library_dir,'add_cyme_substations')))

    #Add ltc control settings
    stack.append(Layer(os.path.join(layer_library_dir,'set_ltc_controls')))

    #Add fuse control settings
    stack.append(Layer(os.path.join(layer_library_dir,'set_fuse_controls')))

    #Add extra switches to long lines 
    stack.append(Layer(os.path.join(layer_library_dir,'add_switches_to_long_lines')))

    #Add Additional regulators
    stack.append(Layer(os.path.join(layer_library_dir,'add_additional_regulators')))

    #Add Capacitor control settings
    stack.append(Layer(os.path.join(layer_library_dir,'set_capacitor_controlers')))

    #Reduce overloaded nodes
    stack.append(Layer(os.path.join(layer_library_dir,'reduce_overload_nodes')))

    #Set any delta connections
    stack.append(Layer(os.path.join(layer_library_dir,'set_delta_systems')))

    #Set source kv
    stack.append(Layer(os.path.join(layer_library_dir,'set_source_voltage')))

    #Write to CYME
    stack.append(Layer(os.path.join(layer_library_dir,'to_cyme')))

    #Write to OpenDSS
    stack.append(Layer(os.path.join(layer_library_dir,'to_json')))

    #Copy Tag file over
    stack.append(Layer(os.path.join(layer_library_dir,'add_tags')))

    #Run validation metrics
    stack.append(Layer(os.path.join(layer_library_dir,'statistical_validation')))

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Load coordinate layer
    load_coordinates = stack[0]
    load_coordinates.kwargs['input_filename'] = os.path.join(dataset_dir,region,'IntermediateFormat','Loads_IntermediateFormat.csv')
    load_coordinates.kwargs['output_filename'] = os.path.join(dataset_dir,region,'IntermediateFormat','Loads_IntermediateFormat2.csv')
    load_coordinates.kwargs['object_name'] = 'Load'

    #Capacitor coordinate layer
    capacitor_coordinates = stack[1]
    capacitor_coordinates.kwargs['input_filename'] = os.path.join(dataset_dir,region,'IntermediateFormat','Capacitors_IntermediateFormat.csv')
    capacitor_coordinates.kwargs['output_filename'] = os.path.join(dataset_dir,region,'IntermediateFormat','Capacitors_IntermediateFormat2.csv')
    capacitor_coordinates.kwargs['object_name'] = 'Capacitor'

    #Read OpenDSS layer
    from_opendss = stack[2]
    from_opendss.args[0] = os.path.join(region,'OpenDSS','Master.dss')
    from_opendss.args[1] = os.path.join(region,'OpenDSS','BusCoord.dss')
    from_opendss.kwargs['base_dir'] = dataset_dir

    #Set regulators with setpoints
    rnm_regulators = stack[3]
    rnm_regulators.kwargs['rnm_name'] = 'CRegulador'
    rnm_regulators.kwargs['setpoint'] = 103

    #Ensure all LV lines are triplex
    set_lv_triplex = stack[4]
    set_lv_triplex.kwargs['to_replace'] = ['Ionic', 'Corinthian', 'Doric']

    #Modify layer
    #No input except the model. Nothing to do here...
    post_processing = stack[5]
    post_processing.kwargs['path_to_feeder_file'] = os.path.join(dataset_dir,region,'Auxiliary','Feeder.txt')
    post_processing.kwargs['path_to_switching_devices_file'] = os.path.join(dataset_dir,region,'OpenDSS','SwitchingDevices.dss')
    post_processing.kwargs['center_tap_postprocess'] = True
    post_processing.kwargs['switch_to_recloser'] = True

    #Merging Load layer
    merging_load = stack[6]
    merging_load.kwargs['filename'] = os.path.join(dataset_dir,region,'IntermediateFormat','Loads_IntermediateFormat2.csv')

    #Merging Capacitor Layer
    merging_caps = stack[7]
    merging_caps.kwargs['filename'] = os.path.join(dataset_dir,region,'IntermediateFormat','Capacitors_IntermediateFormat2.csv')

    #Resetting customer number layer
    customer = stack[8]
    customer.kwargs['num_customers'] = 1

    #Splitting layer
    split = stack[9]
    split.kwargs['path_to_feeder_file'] = os.path.join(dataset_dir,region,'Auxiliary','Feeder.txt')
    split.kwargs['path_to_no_feeder_file'] = os.path.join(dataset_dir,region,'Auxiliary','NoFeeder.txt')
    split.kwargs['compute_metrics'] = True
    split.kwargs['compute_kva_density_with_transformers'] = True #RNM networks have LV information
    split.kwargs['excel_output'] = os.path.join('.', 'results_v2', region, 'base','cyme', 'metrics.csv')
    split.kwargs['json_output'] = os.path.join('.', 'results_v2', region, 'base', 'cyme','metrics.json')

    #Customer per Transformer plotting layer
    transformer_metrics = stack[10]
    transformer_metrics.kwargs['customer_file'] = os.path.join(dataset_dir,region,'Inputs','customers_ext.txt') 
    transformer_metrics.kwargs['output_folder'] = os.path.join('.','results_v2',region,'base','cyme')

    #Intermediate node layer
    inter = stack[11]
    inter.kwargs['filename'] = os.path.join(dataset_dir,region,'OpenDSS','LineCoord.txt')

    # Missing coords
    # No args/kwargs for this layer

    # Move overlayed node layer
    adjust = stack[13]
    adjust.kwargs['delta_x'] = 10
    adjust.kwargs['delta_y'] = 10

    #Substations

    add_substations = stack[14]
    readme_list = [os.path.join(dataset_dir,region,'Inputs',f) for f in os.listdir(os.path.join(dataset_dir,region,'Inputs')) if f.startswith('README')]
    readme = None
    if len(readme_list)==1:
        readme = readme_list[0]
    add_substations.args[0] = os.path.join(dataset_dir,region,'Auxiliary', 'Feeder.txt')
    add_substations.kwargs['base_dir'] = dataset_dir
    add_substations.kwargs['readme_file'] = readme

    #LTC Controls

    ltc_controls = stack[15]
    ltc_controls.kwargs['setpoint'] = 103

    #Fuse Controls

    fuse_controls = stack[16]
    fuse_controls.kwargs['current_rating'] = 100
    fuse_controls.kwargs['high_current_rating'] = 600

    #Add switch in long lines

    switch_cut = stack[17]
    switch_cut.kwargs['cutoff_length'] = 800

   #Add additional regulators

    additional_regs = stack[18]
    additional_regs.kwargs['file_location'] = os.path.join(dataset_dir,region,'Auxiliary','additional_regs.csv')
    additional_regs.kwargs['setpoint'] = 103

    # Capacitor controls
    cap_controls = stack[19]
    cap_controls.kwargs['delay'] = 100
    cap_controls.kwargs['lowpoint'] = 120.5
    cap_controls.kwargs['highpoint'] = 125

    # Reduce overloaded nodes
    overload_nodes = stack[20]
    overload_nodes.kwargs['powerflow_file'] = os.path.join(dataset_dir,region,'Auxiliary','powerflow.csv')
    overload_nodes.kwargs['threshold'] = 0.94
    overload_nodes.kwargs['scale_factor'] = 2.0

    # Set delta loads and transformers   
    delta = stack[21]
    readme_list = [os.path.join(dataset_dir,region,'Inputs',f) for f in os.listdir(os.path.join(dataset_dir,region,'Inputs')) if f.startswith('README')]
    readme = None
    if len(readme_list)==1:
        readme = readme_list[0]
    delta.kwargs['readme_location'] = readme


    #Set source KV value
    set_source = stack[22]
    set_source.kwargs['source_kv'] = 230
    set_source.kwargs['source_names'] = ['st_mat']

    #Write to CYME
    final = stack[23]
    final.args[0] = os.path.join('.','results_v2',region,'base','cyme')

    #Dump to Ditto json
    final_json = stack[24]
    final_json.kwargs['base_dir'] = os.path.join('.','results_v2',region,'base','json_cyme')

    #Write Tags 
    tags = stack[25]
    tags.kwargs['output_folder'] = os.path.join('.','results_v2',region,'base','cyme')
    tags.kwargs['tag_file'] = os.path.join(dataset_dir,region,'Auxiliary','FeederStats.txt')

    #Write validation
    validation = stack[26]
    validation.kwargs['output_folder'] = os.path.join('.','results_v2',region,'base','cyme')
    validation.kwargs['input_folder'] = os.path.join('.','results_v2',region,'base','cyme')
    validation.kwargs['rscript_folder'] = os.path.join('..','..','smartdsR-analysis-lite')
    validation.kwargs['output_name'] = region

    stack.save(os.path.join(stack_library_dir,'rnm_to_cyme_stack_'+region+'.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_cyme_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]
    #dataset_map = {'dataset_4':'20180727','dataset_3':'20180910','dataset_2':'20180716'}
    dataset_map = {'dataset_4':'20181120','dataset_3':'20181130','dataset_2':'20181130'}
    create_rnm_to_cyme_stack(os.path.join('..','..','{dset}_{date}'.format(dset=dataset,date = dataset_map[dataset])), region)
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/rnm_to_cyme_stack_'+region+'.json')
    if not os.path.isdir(os.path.join('.','results_v2',region,'base','cyme')):
        os.makedirs(os.path.join('.','results_v2',region,'base','cyme'))
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
