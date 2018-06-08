import logging
import os

logger = logging.getLogger(__name__)

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack
#from .helpers import layer_library_dir, stack_library_dir, placement_library_dir
layer_library_dir = '../layer_library'
stack_library_dir = '../stack_library'

def create_compute_metrics_sce(path, feeder_name):
    '''
        Create the stack to compute the metrics for SCE feeders (in CYME format).
    '''

    stack = Stack(name='SCE metrics Stack')

    #Read the CYME input model
    stack.append(Layer(os.path.join(layer_library_dir,'from_cyme')))

    #Compute the metrics
    stack.append(Layer(os.path.join(layer_library_dir,'sce_metric_computation_layer')))

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Read CYME layer
    from_cyme = stack[0]
    from_cyme.kwargs['base_dir'] = os.path.join(path,feeder_name)
    from_cyme.kwargs['network_filename'] = 'net.txt'
    from_cyme.kwargs['equipment_filename'] = 'eqt.txt'
    from_cyme.kwargs['load_filename'] = 'load.txt'

    #Compute metrics layer
    metric_computation = stack[1]
    metric_computation.kwargs['feeder_name'] = feeder_name
    metric_computation.kwargs['output_filename_xlsx'] = os.path.join(path,feeder_name,"metrics_{}.xlsx".format(feeder_name))
    metric_computation.kwargs['output_filename_json'] = os.path.join(path,feeder_name,"metrics_{}.json".format(feeder_name))

    stack.save(os.path.join(stack_library_dir,'compute_metrics_sce.json'))


def main():
    #Set the path to the folder which contains the SCE feeders.
    #This folder is assumed to have one subfolder per sce feeder.
    path = '/Users/ngensoll/all_sce/' #CHANGE THAT....

    #Get the list of folders holding the sce feeders.
    #Each folder is a number and contains one feeder in CYME format (so, three files...)
    folder_list = [d for d in os.listdir(path) if '.' not in d]

    from layerstack.stack import Stack
    #Loop over the feeders
    for folder in folder_list:
        create_compute_metrics_sce(path,folder)
        s = Stack.load('../stack_library/compute_metrics_sce.json')
        s.run_dir = 'run_dir'
        s.run()

if __name__ == "__main__":
    main()
