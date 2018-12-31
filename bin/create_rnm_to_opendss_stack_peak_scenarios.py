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
placement_library_dir = '../placement_library'

def create_rnm_to_opendss_stack_scenarios(dataset_dir, region, solar, batteries):
    '''Create the stack to convert RNM models in OpenDSS to OpenDSS.'''

    stack = Stack(name='RNM to OpenDSS Stack')

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

    #Create residential placement for PV
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))

    #Create commercial placement for PV
    stack.append(Layer(os.path.join(layer_library_dir,'create_placement')))

    #Add Load PV
    stack.append(Layer(os.path.join(layer_library_dir,'add_pv')))

    #Add Utility PV
    stack.append(Layer(os.path.join(layer_library_dir,'add_pv')))

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

    #Write to OpenDSS
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

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
    post_processing.kwargs['center_tap_postprocess'] = False

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
    split.kwargs['excel_output'] = os.path.join('.', 'results_v2', region, 'peak_solar_'+solar+'_battery_'+batteries,'opendss', 'metrics.csv')
    split.kwargs['json_output'] = os.path.join('.', 'results_v2', region, 'peak_solar_'+solar+'_battery_'+batteries, 'opendss','metrics.json')

    #Customer per Transformer plotting layer
    transformer_metrics = stack[10]
    transformer_metrics.kwargs['customer_file'] = os.path.join(dataset_dir,region,'Inputs','customers_ext.txt') 
    transformer_metrics.kwargs['output_folder'] = os.path.join('.','results_v2',region,'peak_solar_'+solar+'_battery_'+batteries,'opendss')

    #Intermediate node layer
    inter = stack[11]
    inter.kwargs['filename'] = os.path.join(dataset_dir,region,'OpenDSS','LineCoord.txt')

    #Create Placement for PV
    load_selection_mapping = {'none':None, 'low':[('Random',0,15)],'medium':[('Random',0,15),('Random',15,35)], 'high':[('Random',0,15),('Random',15,35),('Random',35,55),('Random',55,75)]}
    utility_selection_mapping = {'none':None,'low':None,'medium':('Reclosers',1,2), 'high':('Reclosers',2,2)} #(Reclosers,1,2) means algorithm will select 2 Reclosers that are not upstream of each other and return the first. Useful for consistency with larger selections
    utility_feeder_mapping = {'none':None,'low':None,'medium':[50],'high':[100,75]}
    load_feeder_mapping = {'none':None,'low':[100],'medium':[100,100],'high':[100,100,100,100]}
    utility_max_feeder_sizing = {'none':None,'low':None,'medium':33,'high':80}
    load_max_feeder_sizing = {'none':None,'low':75,'medium':150,'high':None}
    

    powerfactor_mapping = {'none':None, 'low':[1], 'medium':[1,-0.95], 'high':[1,-0.95,1,1]} #the pf=1 in the last two should be overridden by the controllers
    inverter_control_mapping = {'none':None, 'low':['powerfactor'], 'medium': ['powerfactor','powerfactor'], 'high':['powerfactor','powerfactor','voltvar','voltwatt']}
    cutin_mapping = {'none':None, 'low':[0.1], 'medium': [0.1,0.1], 'high':[0.1,0.1,0.1,0.1]}
    cutout_mapping = {'none':None, 'low':[0.1], 'medium': [0.1,0.1], 'high':[0.1,0.1,0.1,0.1]}
    kvar_percent_mapping = {'none':None, 'low':[None], 'medium': [None,None], 'high':[None,None,44,44]}
    oversizing_mapping = {'none':None, 'low':[1.1], 'medium': [1.1,1.1], 'high':[1.1,1.1,1.2,1.2]}
    load_equipment_type = 'ditto.models.load.Load'
    utility_equipment_type = 'ditto.models.node.Node'
    seed = 1
    placement_folder = os.path.join(placement_library_dir,region)




    load_solar_placement = stack[12]
    load_solar_placement.args[0] = load_feeder_mapping[solar]
    load_solar_placement.args[1] = load_equipment_type
    load_solar_placement.args[2] = load_selection_mapping[solar]
    load_solar_placement.args[3] = seed
    load_solar_placement.args[4] = placement_folder

    utility_solar_placement = stack[13]
    utility_solar_placement.args[0] = utility_feeder_mapping[solar] # Length should equal selection[1]. values should be in decreasing order
    utility_solar_placement.args[1] = None
    utility_solar_placement.args[2] = utility_selection_mapping[solar]
    utility_solar_placement.args[3] = None
    utility_solar_placement.args[4] = placement_folder

    add_load_pv = stack[14]
    load_file_names = None #Do nothing if this is the case
    powerfactors = None
    inverters = None
    cutin = None
    cutout = None
    kvar_percent = None
    oversizing = None
    if load_selection_mapping[solar] is not None:
        load_file_names = []
        powerfactors = []
        for selection in load_selection_mapping[solar]:
            file_name = str(load_feeder_mapping[solar][-1])+'_'+load_equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'-'+str(selection[2])+'_'+str(seed)+'.json' # Note - assume all subregions are using all feeders
            load_file_names.append(file_name)
        powerfactors = powerfactor_mapping[solar]
        inverters = inverter_control_mapping[solar]
        cutin = cutin_mapping[solar]
        cutout = cutin_mapping[solar]
        kvar_percent = kvar_percent_mapping[solar]
        oversizing = oversizing_mapping[solar]
    add_load_pv.kwargs['placement_folder'] = placement_folder
    add_load_pv.kwargs['placement_names'] = load_file_names
    add_load_pv.kwargs['residential_sizes'] =[3000,5000,8000]
    add_load_pv.kwargs['residential_areas'] =[75,300]
    add_load_pv.kwargs['commercial_sizes'] = [3000,6000,8000,40000,100000,300000]
    add_load_pv.kwargs['commercial_areas'] = [100,300,600,1000,2000]
    add_load_pv.kwargs['customer_file'] = os.path.join(dataset_dir,region,'Inputs','customers_ext.txt')
    add_load_pv.kwargs['max_feeder_sizing_percent'] = load_max_feeder_sizing[solar] # total_pv <= max_feeder_size*total_feeder_load. 
    add_load_pv.kwargs['power_factors'] = powerfactors
    add_load_pv.kwargs['inverters'] = inverters
    add_load_pv.kwargs['cutin'] = cutin
    add_load_pv.kwargs['cutout'] = cutout
    add_load_pv.kwargs['kvar_percent'] = kvar_percent
    add_load_pv.kwargs['oversizing'] = oversizing



    add_utility_pv = stack[15]
    utility_file_name = None
    if utility_selection_mapping[solar] is not None:
        feeders_str = str(utility_feeder_mapping[solar])
        if isinstance(utility_feeder_mapping[solar],list):
            feeders_str = ''
            for f in utility_feeder_mapping[solar]:
                feeders_str = feeders_str+str(f)+'-'
            feeders_str = feeders_str.strip('-')
        utility_file_name = [feeders_str+'_Node_'+utility_selection_mapping[solar][0]+'-'+str(utility_selection_mapping[solar][1])+'-'+str(utility_selection_mapping[solar][2])+'.json']
    add_utility_pv.kwargs['placement_folder'] = placement_folder
    add_utility_pv.kwargs['placement_names'] = utility_file_name
    add_utility_pv.kwargs['single_size'] = 2000000
    add_utility_pv.kwargs['max_feeder_sizing_percent'] = utility_max_feeder_sizing[solar] # total_pv <= max_feeder_size*total_feeder_load
    add_utility_pv.kwargs['power_factors'] = [0.95]
    add_utility_pv.kwargs['inverters'] = ['voltvar'] #Note that in Opendss this needs kvar to be set to 0
    add_utility_pv.kwargs['cutin'] = [0.1]
    add_utility_pv.kwargs['cutout'] = [0.1]
    add_utility_pv.kwargs['kvar_percent'] = [44]
    add_utility_pv.kwargs['oversizing'] = [1.1]




    # Missing coords
    # No args/kwargs for this layer

    # Move overlayed node layer
    adjust = stack[17]
    adjust.kwargs['delta_x'] = 10
    adjust.kwargs['delta_y'] = 10

    #Substations

    add_substations = stack[18]
    readme_list = [os.path.join(dataset_dir,region,'Inputs',f) for f in os.listdir(os.path.join(dataset_dir,region,'Inputs')) if f.startswith('README')]
    readme = None
    if len(readme_list)==1:
        readme = readme_list[0]
    add_substations.args[0] = os.path.join(dataset_dir,region,'Auxiliary', 'Feeder.txt')
    add_substations.kwargs['base_dir'] = dataset_dir
    add_substations.kwargs['readme_file'] = readme

    #LTC Controls

    ltc_controls = stack[19]
    ltc_controls.kwargs['setpoint'] = 103

    #Fuse Controls

    fuse_controls = stack[20]
    fuse_controls.kwargs['current_rating'] = 100
    fuse_controls.kwargs['high_current_rating'] = 600

    #Add switch in long lines

    switch_cut = stack[21]
    switch_cut.kwargs['cutoff_length'] = 800

    #Add additional regulators

    additional_regs = stack[22]
    additional_regs.kwargs['file_location'] = os.path.join(dataset_dir,region,'Auxiliary','additional_regs.csv')
    additional_regs.kwargs['setpoint'] = 103

    # Capacitor controls
    cap_controls = stack[23]
    cap_controls.kwargs['delay'] = 100
    cap_controls.kwargs['lowpoint'] = 120.5
    cap_controls.kwargs['highpoint'] = 125

    # Reduce overloaded nodes
    overload_nodes = stack[24]
    overload_nodes.kwargs['powerflow_file'] = os.path.join(dataset_dir,region,'Auxiliary','powerflow.csv')
    overload_nodes.kwargs['threshold'] = 0.94
    overload_nodes.kwargs['scale_factor'] = 2.0

    # Set delta loads and transformers   
    delta = stack[25]
    readme_list = [os.path.join(dataset_dir,region,'Inputs',f) for f in os.listdir(os.path.join(dataset_dir,region,'Inputs')) if f.startswith('README')]
    readme = None
    if len(readme_list)==1:
        readme = readme_list[0]
    delta.kwargs['readme_location'] = readme

    #Set source KV value
    set_source = stack[26]
    set_source.kwargs['source_kv'] = 230
    set_source.kwargs['source_names'] = ['st_mat']

    #Write to OpenDSS
    final = stack[27]
    final.args[0] = os.path.join('.','results_v2',region, 'peak_solar_'+solar+'_battery_'+batteries,'opendss')
    final.kwargs['separate_feeders'] = True
    final.kwargs['separate_substations'] = True

    #Dump to Ditto json
    final_json = stack[28]
    final_json.kwargs['base_dir'] = os.path.join('.','results_v2',region, 'peak_solar_'+solar+'_battery_'+batteries,'json_opendss')

    #Write Tags 
    tags = stack[29]
    tags.kwargs['output_folder'] = os.path.join('.','results_v2',region, 'peak_solar_'+solar+'_battery_'+batteries,'opendss')
    tags.kwargs['tag_file'] = os.path.join(dataset_dir,region,'Auxiliary','FeederStats.txt')

    #Write validation
    validation = stack[30]
    validation.kwargs['output_folder'] = os.path.join('.','results_v2',region, 'peak_solar_'+solar+'_battery_'+batteries,'opendss')
    validation.kwargs['input_folder'] = os.path.join('.','results_v2',region, 'peak_solar_'+solar+'_battery_'+batteries,'opendss')
    validation.kwargs['rscript_folder'] = os.path.join('..','..','smartdsR-analysis-lite')
    validation.kwargs['output_name'] = region


    stack.save(os.path.join(stack_library_dir,'rnm_to_opendss_stack_peak_'+region+'solar_'+solar+'_batteries_'+batteries+'.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_opendss_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]
    solar = sys.argv[3]
    batteries = sys.argv[4]
    #dataset_map = {'dataset_4':'20180727','dataset_3':'20180910','dataset_2':'20180716'}
    dataset_map = {'dataset_4':'20181120','dataset_3':'20181130','dataset_2':'20181130'}
    solar_options = ['none','low','medium','high']
    battery_options = ['none','low','high']
    if batteries not in battery_options or solar not in solar_options:
        raise("Invalid arguments "+solar+" "+batteries)
    create_rnm_to_opendss_stack_scenarios(os.path.join('..','..','{dset}_{date}'.format(dset=dataset,date = dataset_map[dataset])), region,solar,batteries)
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/rnm_to_opendss_stack_peak_'+region+'solar_'+solar+'_batteries_'+batteries+'.json')
    if not os.path.isdir(os.path.join('.','results_v2',region, 'peak_solar_'+solar+'_battery_'+batteries,'opendss')):
        os.makedirs(os.path.join('.','results_v2',region, 'peak_solar_'+solar+'_battery_'+batteries,'opendss'))
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()

