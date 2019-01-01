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

def create_rnm_to_opendss_stack(dataset_dir, region):
    '''Create the stack to convert json models in OpenDSS to Opendss.'''

    stack = Stack(name='JSON to OpenDSS Stack')

    #Read the OpenDSS input model
    stack.append(Layer(os.path.join(layer_library_dir,'from_json')))


    #Write to OpenDSS
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))


    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Read from json
    from_json = stack[0]
    from_json.kwargs['input_filename'] = 'full_model.json'
    from_json.kwargs['base_dir'] = os.path.join('.','results_v2',region,'base','json_opendss')

    #Write to OpenDSS
    final = stack[1]
    final.args[0] = os.path.join('.','results_v2',region,'base','json_opendss_rerun')
    final.kwargs['separate_feeders'] = True
    final.kwargs['separate_substations'] = True

    stack.save(os.path.join(stack_library_dir,'json_to_opendss_stack_'+region+'.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_opendss_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]
    #dataset_map = {'dataset_4':'20180727','dataset_3':'20180910','dataset_2':'20180716'}
    dataset_map = {'dataset_4':'20181120','dataset_3':'20181130','dataset_2':'20181130'}
    create_rnm_to_opendss_stack(os.path.join('..','..','{dset}_{date}'.format(dset=dataset,date = dataset_map[dataset])), region)
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/json_to_opendss_stack_'+region+'.json')
    if not os.path.isdir(os.path.join('.','results_v2',region,'base','json_opendss_rerun')):
        os.makedirs(os.path.join('.','results_v2',region,'base','json_opendss_rerun'))
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
