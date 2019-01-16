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

def create_rnm_to_opendss_stack(dataset_dir, region, dataset, placement_dictionary):
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

    #Create residential placement for EVs
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))

    #Create commercial placement for EVs
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))

    #Create outage placement
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))


    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE
    
    customer_file = os.path.join(dataset_dir,region,'Inputs','customers_ext.txt')
    #Read from json
    from_json = stack[0]
    from_json.kwargs['input_filename'] = 'full_model.json'
    from_json.kwargs['base_dir'] = os.path.join('.','results_v3',region,'base','json_opendss')

    #Create Placement for controllable Loads
    load_selection_mapping = {'none':None, 'low':[('Random',0,5)],'medium':[('Random',0,5),('Random',5,30)], 'high':[('Random',0,5),('Random',5,30),('Random',30,75)]}
    commercial_selection_mapping = {'none':None,'low':[('Sized_Loads',200,0,15)],'medium':[('Sized_Loads',200,0,15),('Sized_Loads',200,15,50)], 'high':[('Sized_Loads',200,0,15),('Sized_Loads',200,15,50),('Sized_Loads',200,50,100)]} 

    load_equipment_type = 'ditto.models.load.Load'
    commercial_equipment_type = 'ditto.models.load.Load'

    load_placement_names = {'none': None, 'low':'drres=L.json','medium':'drres=M.json','high':'drres=H.json'}
    commercial_placement_names = {'none': None, 'low':'drcom=L.json','medium':'drcom=M.json','high':'drcom=H.json'}

    load_feeder_mapping = {'none':None,'low':[100],'medium':[100,100],'high':[100,100,100,100]}
    commercial_feeder_mapping = {'none':None,'low':[100],'medium':[100,100],'high':[100,100,100,100]}

    seed = 2 # Seed of 1 used for PV and Storage
    placement_folder = os.path.join(placement_library_dir,region)

    dr_com_placement = placement_dictionary['drcom']
    dr_res_placement = placement_dictionary['drres']
    load_dr_placement = stack[1]
    load_dr_placement.args[0] = load_feeder_mapping[dr_res_placement]
    load_dr_placement.args[1] = load_equipment_type
    load_dr_placement.args[2] = load_selection_mapping[dr_res_placement]
    load_dr_placement.args[3] = seed
    load_dr_placement.args[4] = placement_folder
    load_dr_placement.args[5] = load_placement_names[dr_res_placement]

    commercial_dr_placement = stack[2]
    commercial_dr_placement.args[0] = commercial_feeder_mapping[dr_com_placement]
    commercial_dr_placement.args[1] = commercial_equipment_type
    commercial_dr_placement.args[2] = commercial_selection_mapping[dr_com_placement]
    commercial_dr_placement.args[3] = seed
    commercial_dr_placement.args[4] = placement_folder
    commercial_dr_placement.args[5] = commercial_placement_names[dr_com_placement]

    seed = 3 #Different from controllable loads
    load_selection_mapping = {'low':[('Random',0,5)],'medium':[('Random',0,5),('Random',5,15)], 'high':[('Random',0,5),('Random',5,15),('Random',15,75)], 'all':[('Random',0,5),('Random',5,15),('Random',15,75),('Random',75,100)]}
    load_equipment_type = 'ditto.models.load.Load'
    load_placement_names = {'low':'visami=L.json','medium':'visami=M.json','high':'visami=H.json', 'all':'visami=A.json'}
    load_feeder_mapping = {'low':[100],'medium':[100,100],'high':[100,100,100], 'all':[100,100,100,100,100]}

    vis_placement = placement_dictionary['visami']
    load_ami_placement = stack[3]
    load_ami_placement.args[0] = load_feeder_mapping[vis_placement]
    load_ami_placement.args[1] = load_equipment_type
    load_ami_placement.args[2] = load_selection_mapping[vis_placement]
    load_ami_placement.args[3] = seed
    load_ami_placement.args[4] = placement_folder
    load_ami_placement.args[5] = load_placement_names[vis_placement]


    seed = 4 #For EVs
    load_selection_mapping = {'low':[('Random_res',0,5)], 'medium':[('Random_res',0,5),('Random_res',5,30)], 'high':[('Random_res',0,5),('Random_res',5,30),('Random_res',30,60), ('Random_res',0,15)], 'all':[('Random_res',0,5),('Random_res',5,30),('Random_res',30,60), ('Random_res',60,75), ('Random_res',0,15),('Random_res',15,45)]} #Includes some homes with two cars
    load_equipment_type = 'ditto.models.load.Load'
    load_placement_names = {'low':'evres=L.json','medium':'evres=M.json','high':'evres=H.json', 'all':'evres=A.json'}
    load_feeder_mapping = {'low':[100],'medium':[100,100],'high':[100,100,100,100], 'all':[100,100,100,100,100,100,100]}

    resev_placement = placement_dictionary['evres']
    ev_placement = stack[4]
    ev_placement.args[0] = load_feeder_mapping[resev_placement]
    ev_placement.args[1] = load_equipment_type
    ev_placement.args[2] = load_selection_mapping[resev_placement]
    ev_placement.args[3] = seed
    ev_placement.args[4] = placement_folder
    ev_placement.args[5] = load_placement_names[resev_placement]
    ev_placement.args[6] = customer_file

    seed = 4 #For EVs
    load_selection_mapping = {'low':[('Random_com',0,5)], 'medium':[('Random_com',0,5),('Random_com',5,30)], 'high':[('Random_com',0,5),('Random_com',5,30),('Random_com',30,75)], 'all':[('Random_com',0,5),('Random_com',5,30),('Random_com',30,75), ('Random_com',75,100)]} #Includes some homes with two cars
    load_equipment_type = 'ditto.models.load.Load'
    load_placement_names = {'low':'evcom=L.json','medium':'evcom=M.json','high':'evcom=H.json', 'all':'evcom=A.json'}
    load_feeder_mapping = {'low':[100],'medium':[100,100],'high':[100,100,100], 'all':[100,100,100,100,100]}

    comev_placement = placement_dictionary['evcom']
    ev_placement = stack[5]
    ev_placement.args[0] = load_feeder_mapping[comev_placement]
    ev_placement.args[1] = load_equipment_type
    ev_placement.args[2] = load_selection_mapping[comev_placement]
    ev_placement.args[3] = seed
    ev_placement.args[4] = placement_folder
    ev_placement.args[5] = load_placement_names[comev_placement]
    ev_placement.args[6] = customer_file


    seed=1 # Different element for lines so seed of 1 is fine
    outages_selection_mapping = {'low':[('Count',1)],'medium':[('Count',3)], 'severe':[('Random',0,2)], 'extreme':[('Random',20)]}
    outages_equipment_type = 'ditto.models.line.Line'
    outage_placement_names = {'low':'outln=L.json','medium':'outln=M.json','severe':'outln=S.json','extreme':'outln=E.json'}
    outage_feeder_mapping = {'low':[100],'medium':[100],'severe':[100],'extreme':[100]}

    outage_placement = placement_dictionary['outln']
    outages = stack[6]
    outages.args[0] = outage_feeder_mapping[outage_placement]
    outages.args[1] = outages_equipment_type
    outages.args[2] = outages_selection_mapping[outage_placement]
    outages.args[3] = seed
    outages.args[4] = placement_folder
    outages.args[5] = outage_placement_names[outage_placement]

    stack.save(os.path.join(stack_library_dir,'json_to_opendss_stack_'+region+'_placements.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_opendss_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]

    #dataset_map = {'dataset_4':'20180727','dataset_3':'20180910','dataset_2':'20180716'}
    dataset_map = {'dataset_4':'20181120','dataset_3':'20181130','dataset_2':'20181130'}
    all_placement_dictionary = {'drcom':['low','medium','high'],'drres':['low','medium','high'],'visami':['low','medium','high','all'],'evres':['low','medium','high','all'],'evcom':['low','medium','high','all'],'outln':['low','medium','severe','extreme']}
    placement_dictionary = {'drcom':'high', 'drres':'high','visami':'high','evres':'high','evcom':'high','outln':'extreme'}

    for i in range(4):
        placement_dictionary = {}
        for key in all_placement_dictionary:
            placement_dictionary[key] = all_placement_dictionary[key][min(i,len(all_placement_dictionary[key])-1)]
        # warning - doesn't work well in parallel due to the basic stack name
        create_rnm_to_opendss_stack(os.path.join('..','..','{dset}_{date}'.format(dset=dataset,date = dataset_map[dataset])), region, dataset,placement_dictionary)
        from layerstack.stack import Stack
        s = Stack.load('../stack_library/json_to_opendss_stack_'+region+'_placements.json')
        s.run_dir = 'run_dir'
        s.run()

if __name__ == "__main__":
    main()
