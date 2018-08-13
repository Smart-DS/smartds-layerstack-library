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

def create_rnm_to_opendss_stack_pv(dataset_dir, region, pct_pv=15):
    '''Create the stack to convert RNM models in OpenDSS to OpenDSS.'''

    stack = Stack(name='RNM to OpenDSS Stack')

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
    stack.append(Layer(os.path.join(layer_library_dir,'add_cyme_substations')))

    #Add ltc control settings
    stack.append(Layer(os.path.join(layer_library_dir,'set_ltc_controls')))

    #Add fuse control settings
    stack.append(Layer(os.path.join(layer_library_dir,'set_fuse_controls')))

    #Create placement for PV
    stack.append(Layer(os.path.join(layer_library_dir,'create_placement')))

    #Add PV
    stack.append(Layer(os.path.join(layer_library_dir,'add_pv')))


    #Find missing coordinates
    stack.append(Layer(os.path.join(layer_library_dir,'find_missing_coords')))

    #Write to CYME
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))


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

    #Modify layer
    #No input except the model. Nothing to do here...
    post_processing = stack[3]
    post_processing.kwargs['path_to_feeder_file'] = os.path.join(dataset_dir,region,'Auxiliary','Feeder.txt')
    post_processing.kwargs['path_to_switching_devices_file'] = os.path.join(dataset_dir,region,'OpenDSS','SwitchingDevices.dss')
    post_processing.kwargs['center_tap_postprocess'] = False
    post_processing.kwargs['switch_to_recloser'] = True

    #Merging Load layer
    merging_load = stack[4]
    merging_load.kwargs['filename'] = os.path.join(dataset_dir,region,'IntermediateFormat','Loads_IntermediateFormat2.csv')

    #Merging Capacitor Layer
    merging_caps = stack[5]
    merging_caps.kwargs['filename'] = os.path.join(dataset_dir,region,'IntermediateFormat','Capacitors_IntermediateFormat2.csv')

    #Splitting layer
    split = stack[6]
    split.kwargs['path_to_feeder_file'] = os.path.join(dataset_dir,region,'Auxiliary','Feeder.txt')

    #Intermediate node layer
    inter = stack[7]
    inter.kwargs['filename'] = os.path.join(dataset_dir,region,'OpenDSS','LineCoord.txt')

    #Substations

    add_substations = stack[8]
    readme_list = [os.path.join(dataset_dir,region,'Inputs',f) for f in os.listdir(os.path.join(dataset_dir,region,'Inputs')) if f.startswith('README')]
    readme = None
    if len(readme_list)==1:
        readme = readme_list[0]
    add_substations.args[0] = os.path.join(dataset_dir,region,'Auxiliary', 'Feeder.txt')
    add_substations.kwargs['base_dir'] = dataset_dir
    add_substations.kwargs['readme_file'] = readme

    #LTC Controls

    ltc_controls = stack[9]
    ltc_controls.kwargs['setpoint'] = 105

    #Fuse Controls

    ltc_controls = stack[10]
    ltc_controls.kwargs['current_rating'] = 65

    #Create Placement for PV
    feeders = 'all'
    equipment_type = 'ditto.models.load.Load'
    selection = ('Random',pct_pv)
    seed = 1
    placement_folder = os.path.join(placement_library_dir,region)
    file_name = feeders+'_'+equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'_'+str(seed)+'.txt'


    create_placement = stack[11]
    create_placement.args[0] = feeders
    create_placement.args[1] = equipment_type
    create_placement.args[2] = selection
    create_placement.args[3] = seed
    create_placement.args[4] = placement_folder
    create_placement.args[5] = file_name

    add_pv = stack[12]
    add_pv.args[0] = os.path.join(placement_folder,file_name) # placement
    add_pv.args[1] = 4000                                     # rated power (Watts)
    add_pv.args[2] = 1.0                                      # power factor


    # Missing coords
    # No args/kwargs for this layer

    #Write to OpenDSS
    final = stack[14]
    final.args[0] = os.path.join('.','results',region,'{pct}_pv'.format(pct=pct_pv))
    final.kwargs['separate_feeders'] = False
    final.kwargs['separate_substations'] = False

    stack.save(os.path.join(stack_library_dir,'rnm_to_opendss_stack_pv_'+region+'_'+str(pct_pv)+'_pct.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_opendss_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]
    percent = float(sys.argv[3])
    dataset_map = {'dataset_4':'20180727','dataset_3':'20180716','dataset_2':'20180727'}
    if not os.path.isdir(os.path.join('.','results',region,'{pct}_pv'.format(pct=percent))):
        os.makedirs(os.path.join('.','results',region,'{pct}_pv'.format(pct=percent)))
    create_rnm_to_opendss_stack_pv(os.path.join('..','..','{dset}_{date}'.format(dset=dataset,date = dataset_map[dataset])), region,percent)
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/rnm_to_opendss_stack_pv_'+region+'_'+str(percent)+'_pct.json')
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
