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

def create_rnm_to_opendss_stack(dataset_dir, region, dataset, solar, batteries, timeseries):
    '''Create the stack to convert json models in OpenDSS to Opendss.'''

    stack = Stack(name='JSON to OpenDSS Stack')

    #Read the OpenDSS input model
    stack.append(Layer(os.path.join(layer_library_dir,'from_json')))

    #Create residential placement for Controllable Loads
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))

    #Create commercial placement for Controllable Loads
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))

    #Create residential placement for Load Measurement
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))


    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Read from json
    from_json = stack[0]
    from_json.kwargs['input_filename'] = 'full_model.json'
    from_json.kwargs['base_dir'] = os.path.join('.','results_v3',region,'base','json_opendss')

    #Create Placement for controllable Loads
    load_selection_mapping = {'none':None, 'low':[('Random',0,5)],'medium':[('Random',0,5),('Random',5,30)], 'high':[('Random',0,5),('Random',5,30),('Random',30,75)]}
    commercial_selection_mapping = {'none':None,'low':[('Sized_Loads',200,0,15)],'medium':[('Sized_Loads',200,0,15),('Sized_Loads',200,15,50)], 'high':[('Sized_Loads',200,0,15),('Sized_Loads',200,15,50),('Sized_Loads',200,50,100)]} 

    load_equipment_type = 'ditto.models.load.Load'
    commercial_equipment_type = 'ditto.models.node.Load'

    load_placement_names = {'none': None, 'low':['drres=L.json'],'medium':['drres=L.json','drres=M.json'],'high':['drres=L.json','drres=M.json','drres=H.json']}
    commercial_placement_names = {'none': None, 'low':['drcom=L.json'],'medium':['drcom=L.json','drcom=M.json'],'high':['drcom=L.json','drcom=M.json','drcom=H.json']}

    load_feeder_mapping = {'none':None,'low':[100],'medium':[100,100],'high':[100,100,100,100]}
    commercial_feeder_mapping = {'none':None,'low':[100],'medium':[100,100],'high':[100,100,100,100]}

    seed = 2 # Seed of 1 used for PV and Storage
    placement_folder = os.path.join(placement_library_dir,region)

    load_dr_placement = stack[1]
    load_dr_placement.args[0] = load_feeder_mapping['high']
    load_dr_placement.args[1] = load_equipment_type
    load_dr_placement.args[2] = load_selection_mapping['high']
    load_dr_placement.args[3] = seed
    load_dr_placement.args[4] = placement_folder
    load_dr_placement.args[5] = load_placement_names['high']

    commercial_dr_placement = stack[2]
    commercial_dr_placement.args[0] = commercial_feeder_mapping['high']
    commercial_dr_placement.args[1] = commercial_equipment_type
    commercial_dr_placement.args[2] = commercial_selection_mapping['high']
    commercial_dr_placement.args[3] = seed
    commercial_dr_placement.args[4] = placement_folder
    commercial_dr_placement.args[5] = commercial_placement_names['high']

    seed = 2 #Same sets as controllable loads. Should it be different?
    load_selection_mapping = { 'all':[('Random',0,5),('Random',5,15),('Random',15,75),('Random',75,100)]}
    load_equipment_type = 'ditto.models.load.Load'
    load_placement_names = {'all':['visami=L.json','visami=M.json','visami=H.json','visami=A.json']}
    load_feeder_mapping = {'all':[100,100,100,100,100]}

    load_ami_placement = stack[3]
    load_ami_placement.args[0] = load_feeder_mapping['all']
    load_ami_placement.args[1] = load_equipment_type
    load_ami_placement.args[2] = load_selection_mapping['all']
    load_ami_placement.args[3] = seed
    load_ami_placement.args[4] = placement_folder
    load_ami_placement.args[5] = load_placement_names['all']

    stack.save(os.path.join(stack_library_dir,'json_to_opendss_stack_'+region+'_solar_'+solar+'_batteries_'+batteries+'_'+timeseries+'.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_opendss_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]
    solar = sys.argv[3]
    batteries = sys.argv[4]
    timeseries = sys.argv[5]

    #dataset_map = {'dataset_4':'20180727','dataset_3':'20180910','dataset_2':'20180716'}
    dataset_map = {'dataset_4':'20181120','dataset_3':'20181130','dataset_2':'20181130'}
    solar_options = ['none','low','medium','high']
    battery_options = ['none','low','high']
    timeseries_options = ['timeseries','peak']
    if batteries not in battery_options or solar not in solar_options or timeseries not in timeseries_options:
        raise("Invalid arguments "+solar+" "+batteries+' '+timeseries)

    create_rnm_to_opendss_stack(os.path.join('..','..','{dset}_{date}'.format(dset=dataset,date = dataset_map[dataset])), region, dataset, solar,batteries, timeseries)
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/json_to_opendss_stack_'+region+'_solar_'+solar+'_batteries_'+batteries+'_'+timeseries+'.json')
    if not os.path.isdir(os.path.join('.','results_v4',region,'solar_'+solar+'_batteries_'+batteries+'_'+timeseries,'opendss')):
        os.makedirs(os.path.join('.','results_v4',region,'solar_'+solar+'_batteries_'+batteries+'_'+timeseries,'opendss'))
    if not os.path.isdir(os.path.join('.','results_v4',region,'solar_'+solar+'_batteries_'+batteries+'_'+timeseries,'json_opendss')):
        os.makedirs(os.path.join('.','results_v4',region,'solar_'+solar+'_batteries_'+batteries+'_'+timeseries,'json_opendss'))
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
