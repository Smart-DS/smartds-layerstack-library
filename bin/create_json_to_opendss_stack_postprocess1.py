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

def create_rnm_to_opendss_stack(dataset_dir, region, dataset):
    '''Create the stack to convert json models in OpenDSS to Opendss.'''

    stack = Stack(name='JSON to OpenDSS Stack')

    #Read the OpenDSS input model
    stack.append(Layer(os.path.join(layer_library_dir,'from_json')))

    #Set pu and source impedance
    stack.append(Layer(os.path.join(layer_library_dir,'set_source_impedance')))

    #Increase MVA of low transformers
    stack.append(Layer(os.path.join(layer_library_dir,'boost_transformers')))

    #Increase ltc setpoint
    stack.append(Layer(os.path.join(layer_library_dir,'boost_setpoints')))

    #Reduce the load of select load locations
    stack.append(Layer(os.path.join(layer_library_dir,'reduce_lv_loads')))

    #Fix delta phases
    stack.append(Layer(os.path.join(layer_library_dir,'fix_delta_phases')))

    #Fix single phase regulator voltages
    stack.append(Layer(os.path.join(layer_library_dir,'fix_regulator_voltage')))

    #Set maximum name size
    stack.append(Layer(os.path.join(layer_library_dir,'shorten_long_names')))

    #Write to OpenDSS
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

    #Write to json
    stack.append(Layer(os.path.join(layer_library_dir,'to_json')))

    #Set buscoords in latlong
    stack.append(Layer(os.path.join(layer_library_dir,'add_lat_longs')))

    #write substation information to a file
    stack.append(Layer(os.path.join(layer_library_dir,'list_substations')))

    #Run OpenDSS
    stack.append(Layer(os.path.join(layer_library_dir,'run_dss')))


    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Read from json
    from_json = stack[0]
    from_json.kwargs['input_filename'] = 'full_model.json'
    from_json.kwargs['base_dir'] = os.path.join('.','results_v2',dataset_dir,region,'base','json_opendss')

    # Set source impedances and p.u. value
    set_source_impedance = stack[1]
    set_source_impedance.kwargs['x1'] = 0.00001
    set_source_impedance.kwargs['x0'] = 0.00001
    set_source_impedance.kwargs['r1'] = 0.00001
    set_source_impedance.kwargs['r0'] = 0.00001
    set_source_impedance.kwargs['pu'] = 1.0

    # Boost selected transformers
    boost_transformers = stack[2]
    boost_transformers.kwargs['mva'] = 30
    boost_transformers.kwargs['resistance'] = 0.33831264
    boost_transformers.kwargs['reactance'] = 6.76625
    boost_transformers.kwargs['input_file'] = os.path.join('extra_inputs',region,'extra_transformers.csv')

    # Boost selected setpoints
    boost_transformers = stack[3]
    boost_transformers.kwargs['setpoint'] = 105
    boost_transformers.kwargs['input_file'] = os.path.join('extra_inputs',region,'setpoints.csv')

    # Reduce selected loads
    boost_transformers = stack[4]
    boost_transformers.kwargs['scale_factor'] = 2.0
    boost_transformers.kwargs['input_file'] = os.path.join('extra_inputs',region,'lv_nodes.csv')

    dataset_map = {'dataset_4':'dataset_4_20181120','dataset_3':'dataset_3_20181130','dataset_2':'dataset_2_20181130','t_and_d':'t_and_d_20190514','houston':'houston_20190722','texas_rural':'texas_rural_20191104'}
    readme_list = [os.path.join('..','..',dataset_map[dataset],region,'Inputs',f) for f in os.listdir(os.path.join('..','..',dataset_map[dataset],region,'Inputs')) if f.startswith('README')]
    readme = None
    if len(readme_list)==1:
        readme = readme_list[0]


    # Fix delta systems
    fix_delta_phases = stack[5]
    fix_delta_phases.kwargs['readme_location'] = readme
    fix_delta_phases.kwargs['transformer_file'] = os.path.join('..','..',dataset_map[dataset],region,'OpenDSS','Transformers.dss')
    
    # No params for fix_regulator_voltage

    # Set maximum name sizes
    max_size = stack[7]
    max_size.kwargs['max_size'] = 48
    


    #Write to OpenDSS
    final = stack[8]
    final.args[0] = os.path.join('.','results_v3',dataset_dir,region,'base','opendss')
    final.kwargs['separate_feeders'] = True
    final.kwargs['separate_substations'] = True

    #Dump to Ditto json
    final_json = stack[9]
    final_json.kwargs['base_dir'] = os.path.join('.','results_v3',dataset_dir,region, 'base','json_opendss')

    #Walk through folders and write lats/longs
    lat_longs = stack[10]
    lat_longs.kwargs['folder_location'] = os.path.join('.','results_v3',dataset_dir,region, 'base','opendss')
    lat_longs.kwargs['dataset'] = dataset

    #Create substation information
    lat_longs = stack[11]
    lat_longs.kwargs['output_folder'] = os.path.join('.','results_v3',dataset_dir,region, 'base','opendss')
    lat_longs.kwargs['dataset'] = dataset

    # Run OpenDSSDirect and get plots
    run_dss = stack[12]
    run_dss.kwargs['master_file'] = os.path.join('.','results_v3',dataset_dir,region,'base','opendss','Master.dss')
    run_dss.kwargs['plot_profile'] = True
    run_dss.kwargs['output_folder'] = os.path.join('.','results_v3',dataset_dir,region,'base','opendss','analysis')
    run_dss.kwargs['region'] = region

    stack.save(os.path.join(stack_library_dir,'json_to_opendss_stack_'+region+'.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_opendss_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]
    #dataset_map = {'dataset_4':'20180727','dataset_3':'20180910','dataset_2':'20180716'}
    dataset_map = {'dataset_4':'20181120','dataset_3':'20181130','dataset_2':'20181130','t_and_d':'20190514','houston':'20190722','texas_rural':'20191104'}
    dataset_dir =os.path.join('..','..','{dset}_{date}'.format(dset=dataset,date = dataset_map[dataset])) 
    create_rnm_to_opendss_stack(dataset_dir, region, dataset)
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/json_to_opendss_stack_'+region+'.json')
    if not os.path.isdir(os.path.join('.','results_v3',dataset_dir,region,'base','opendss')):
        os.makedirs(os.path.join('.','results_v3',dataset_dir,region,'base','opendss'))
    if not os.path.isdir(os.path.join('.','results_v3',dataset_dir,region,'base','json_opendss')):
        os.makedirs(os.path.join('.','results_v3',dataset_dir,region,'base','json_opendss'))
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
