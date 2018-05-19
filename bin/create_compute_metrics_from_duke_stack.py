import logging
import sys
import os

logger = logging.getLogger(__name__)

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack
#from .helpers import layer_library_dir, stack_library_dir, placement_library_dir
layer_library_dir = '../layer_library'
stack_library_dir = '../stack_library'

def create_compute_metrics_from_duke_stack(dataset_dir, region):
    '''
        Create the stack to compute the metrics from the Duke feeders in CYME format.
    '''

    stack = Stack(name='Metrics_from_Duke')

    #Read from cyme
    stack.append(Layer(os.path.join(layer_library_dir,'from_cyme')))

    #Compute metrics from duke
    stack.append(Layer(os.path.join(layer_library_dir,'compute_metrics_from_duke')))

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Read from cyme layer
    from_cyme = stack[0]
    from_cyme.kwargs['base_dir'] = os.path.join(dataset_dir, region)
    from_cyme.kwargs['network_filename'] = 'network.txt'
    from_cyme.kwargs['equipment_filename'] = 'equipment.txt'
    from_cyme.kwargs['load_filename'] = 'load.txt'

    #Compute metrics from duke layer
    metrics = stack[1]
    metrics.kwargs['data_folder_path'] = os.path.join(dataset_dir,region)
    metrics.kwargs['network_filename'] = 'network.txt'
    metrics.kwargs['equipment_filename'] = 'equipment.txt'
    metrics.kwargs['excel_output_filename'] = os.path.join('./results/duke', region, 'metrics.xlsx')
    metrics.kwargs['json_output_filename'] = os.path.join('./results/duke', region, 'metrics.json')
    metrics.kwargs['compute_kva_density_with_transformers'] = False

    stack.save(os.path.join(stack_library_dir,'compute_metrics_from_duke_{dirname}.json'.format(dirname=region)))


def main():
    '''
        TODO.
    '''
    from layerstack.stack import Stack
    #path_to_data = os.path.join('..', '..', '..', 'Projects/DiTTo/data/Cyme/Cleaned_DUKE_data')
    path_to_data = os.path.join('..', '..', 'duke_data','Cleaned_DUKE_data')
    #Loop over the folders here
    #for area in os.listdir(path_to_data):
    #.   if not os.path.exists(os.path.join('./results', area)):
    #.       os.makedirs(os.path.join('./results', area))
    #.   create_compute_metrics_from_duke_stack(path_to_data, area)
    #.   s = Stack.load('../stack_library/compute_metrics_from_duke.json')
    #.   s.run_dir = 'run_dir'
    #.   s.run()
    dirname = sys.argv[1]
    create_compute_metrics_from_duke_stack(path_to_data, dirname)
    
    s = Stack.load('../stack_library/compute_metrics_from_duke_{dirname}.json'.format(dirname=dirname))
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
