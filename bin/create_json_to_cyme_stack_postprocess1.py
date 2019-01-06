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

def create_rnm_to_cyme_stack(dataset_dir, region, dataset):
    '''Create the stack to convert RNM models in OpenDSS to CYME.'''

    stack = Stack(name='JSON to CYME Stack')

    #Read the OpenDSS input model
    stack.append(Layer(os.path.join(layer_library_dir,'from_json')))

    #Set pu and source impedance
    stack.append(Layer(os.path.join(layer_library_dir,'set_source_impedance')))

    #Increase MVA of low transformers
    stack.append(Layer(os.path.join(layer_library_dir,'boost_transformers')))

    #Fix delta phases
    stack.append(Layer(os.path.join(layer_library_dir,'fix_delta_phases')))

    #Set maximum name size
    stack.append(Layer(os.path.join(layer_library_dir,'shorten_long_names')))

    #Write to CYME
    stack.append(Layer(os.path.join(layer_library_dir,'to_cyme')))

    #Write to json
    stack.append(Layer(os.path.join(layer_library_dir,'to_json')))


    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Read from json
    from_json = stack[0]
    from_json.kwargs['input_filename'] = 'full_model.json'
    from_json.kwargs['base_dir'] = os.path.join('.','results_v2',region,'base','json_cyme')

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

    dataset_map = {'dataset_4':'dataset_4_20181120','dataset_3':'dataset_3_20181130','dataset_2':'dataset_2_20181130'}
    readme_list = [os.path.join('..','..',dataset_map[dataset],region,'Inputs',f) for f in os.listdir(os.path.join('..','..',dataset_map[dataset],region,'Inputs')) if f.startswith('README')]
    readme = None
    if len(readme_list)==1:
        readme = readme_list[0]
    fix_delta_phases = stack[3]
    fix_delta_phases.kwargs['readme_location'] = readme
    fix_delta_phases.kwargs['transformer_file'] = os.path.join('..','..',dataset_map[dataset],region,'OpenDSS','Transformers.dss')
    

    # Set maximum name sizes
    max_size = stack[4]
    max_size.kwargs['max_size'] = 48

    #Write to CYME
    final = stack[5]
    final.args[0] = os.path.join('.','results_v3',region,'base','cyme')

    #Dump to Ditto json
    final_json = stack[6]
    final_json.kwargs['base_dir'] = os.path.join('.','results_v3',region, 'base','json_cyme')

    stack.save(os.path.join(stack_library_dir,'json_to_cyme_stack_'+region+'.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_cyme_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]
    #dataset_map = {'dataset_4':'20180727','dataset_3':'20180910','dataset_2':'20180716'}
    dataset_map = {'dataset_4':'20181120','dataset_3':'20181130','dataset_2':'20181130'}
    create_rnm_to_cyme_stack(os.path.join('..','..','{dset}_{date}'.format(dset=dataset,date = dataset_map[dataset])), region, dataset)
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/json_to_cyme_stack_'+region+'.json')
    if not os.path.isdir(os.path.join('.','results_v3',region,'base','cyme')):
        os.makedirs(os.path.join('.','results_v3',region,'base','cyme'))
    if not os.path.isdir(os.path.join('.','results_v3',region,'base','json_cyme')):
        os.makedirs(os.path.join('.','results_v3',region,'base','json_cyme'))
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
