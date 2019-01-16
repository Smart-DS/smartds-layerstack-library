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

    #Create residential placement for PV
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))

    #Create commercial placement for PV
    stack.append(Layer(os.path.join(layer_library_dir,'create_placement')))

    #Add Load PV
    stack.append(Layer(os.path.join(layer_library_dir,'add_pv')))

    #Add Utility PV
    stack.append(Layer(os.path.join(layer_library_dir,'add_pv')))

    #Create residential placement for Storage
    stack.append(Layer(os.path.join(layer_library_dir,'create_nested_placement')))

    #Create utility placement for Storage
    stack.append(Layer(os.path.join(layer_library_dir,'create_placement')))

    #Add Load Storage
    stack.append(Layer(os.path.join(layer_library_dir,'add_storage')))

    #Add Utility Storage
    stack.append(Layer(os.path.join(layer_library_dir,'add_storage')))

    if timeseries == 'timeseries':
        #Add Timeseries Solar
        stack.append(Layer(os.path.join(layer_library_dir,'connect_solar_timeseries')))
    
        #Add Timeseries loads
        stack.append(Layer(os.path.join(layer_library_dir,'connect_timeseries_loads')))

    #Find missing coordinates
    stack.append(Layer(os.path.join(layer_library_dir,'find_missing_coords')))

    #Write to OpenDSS
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

    #Write to json
    stack.append(Layer(os.path.join(layer_library_dir,'to_json')))

    #Run OpenDSS
    stack.append(Layer(os.path.join(layer_library_dir,'run_dss')))

    timeseries_layer_cnt = 0
    if timeseries == 'timeseries':
        timeseries_layer_cnt = 2

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    #Read from json
    from_json = stack[0]
    from_json.kwargs['input_filename'] = 'full_model.json'
    from_json.kwargs['base_dir'] = os.path.join('.','results_v3',region,'base','json_opendss')

    #Create Placement for PV
    load_selection_mapping = {'none':None, 'low':[('Random',0,15)],'medium':[('Random',0,15),('Random',15,35)], 'high':[('Random',0,15),('Random',15,35),('Random',35,65)],'extreme':[('Random',0,15),('Random',15,35),('Random',35,65),('Random',65,85)]}
    utility_selection_mapping = {'none':None,'low':None,'medium':('Reclosers',1,2), 'high':('Reclosers',2,2),'extreme':('Reclosers',2,2)} #(Reclosers,1,2) means algorithm will select 2 Reclosers that are not upstream of each other and return the first. Useful for consistency with larger selections
    utility_feeder_mapping = {'none':None,'low':None,'medium':[50],'high':[100,75],'extreme':[100,75]}
    load_feeder_mapping = {'none':None,'low':[100],'medium':[100,100],'high':[100,100,100],'extreme':[100,100,100,100]}
    utility_max_feeder_sizing = {'none':None,'low':None,'medium':33,'high':80,'extreme':100}
    load_max_feeder_sizing = {'none':None,'low':15,'medium':75,'high':150, 'extreme':None}
    

    powerfactor_mapping = {'none':None, 'low':[1], 'medium':[1,-0.95], 'high':[1,-0.95,1], 'extreme':[1,-0.95,1,1]} #the pf=1 in the last two should be overridden by the controllers
    #powerfactor_mapping = {'none':None, 'low':[1], 'medium':[1,-0.95], 'high':[1,-0.95,1,1]} #the pf=1 in the last two should be overridden by the controllers
    inverter_control_mapping = {'none':None, 'low':['powerfactor'], 'medium': ['powerfactor','powerfactor'], 'high':['powerfactor','powerfactor','powerfactor'], 'extreme':['powerfactor','powerfactor','powerfactor','powerfactor']}
    #inverter_control_mapping = {'none':None, 'low':['powerfactor'], 'medium': ['powerfactor','powerfactor'], 'high':['powerfactor','powerfactor','voltvar','voltwatt']}
    cutin_mapping = {'none':None, 'low':[0.1], 'medium': [0.1,0.1], 'high':[0.1,0.1,0.1], 'extreme':[0.1,0.1,0.1,0.1]}
    #cutin_mapping = {'none':None, 'low':[0.1], 'medium': [0.1,0.1], 'high':[0.1,0.1,0.1,0.1]}
    cutout_mapping = {'none':None, 'low':[0.1], 'medium': [0.1,0.1], 'high':[0.1,0.1,0.1], 'extreme':[0.1,0.1,0.1,0.1]}
    #cutout_mapping = {'none':None, 'low':[0.1], 'medium': [0.1,0.1], 'high':[0.1,0.1,0.1,0.1]}
    kvar_percent_mapping = {'none':None, 'low':[None], 'medium': [None,None], 'high':[None,None,44],'extreme':[None,None,44,44]}
    #kvar_percent_mapping = {'none':None, 'low':[None], 'medium': [None,None], 'high':[None,None,44,44]}
    oversizing_mapping = {'none':None, 'low':[1.1], 'medium': [1.1,1.1], 'high':[1.1,1.1,1.2], 'extreme':[1.1,1.1,1.2,1.2]}
    #oversizing_mapping = {'none':None, 'low':[1.1], 'medium': [1.1,1.1], 'high':[1.1,1.1,1.2,1.2]}
    load_equipment_type = 'ditto.models.load.Load'
    utility_equipment_type = 'ditto.models.node.Node'

    load_placement_names = {'none': None, 'low':'pvroof=L.json','medium':'pvroof=M.json','high':'pvroof=H.json','extreme':'pvroof=E.json'}
    load_pv_placement_names = {'none':[None], 'low':['pvroof=L.json'], 'medium':['pvroof=L.json','pvroof=M.json'], 'high':['pvroof=L.json','pvroof=M.json','pvroof=H.json'], 'extreme':['pvroof=L.json','pvroof=M.json','pvroof=H.json','pvroof=E.json']}
    utility_placement_name = {'none': None, 'low':None,'medium':'pvlg=M.json','high':'pvlg=H.json','extreme':'pvlg=E.json'}

    seed = 1
    placement_folder = os.path.join(placement_library_dir,region)




    load_solar_placement = stack[1]
    load_solar_placement.args[0] = load_feeder_mapping[solar]
    load_solar_placement.args[1] = load_equipment_type
    load_solar_placement.args[2] = load_selection_mapping[solar]
    load_solar_placement.args[3] = seed
    load_solar_placement.args[4] = placement_folder
    load_solar_placement.args[5] = load_placement_names[solar]

    utility_solar_placement = stack[2]
    utility_solar_placement.args[0] = utility_feeder_mapping[solar] # Length should equal selection[1]. values should be in decreasing order
    utility_solar_placement.args[1] = None
    utility_solar_placement.args[2] = utility_selection_mapping[solar]
    utility_solar_placement.args[3] = None
    utility_solar_placement.args[4] = placement_folder
    utility_solar_placement.args[5] = utility_placement_name[solar]

    add_load_pv = stack[3]
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
    add_load_pv.kwargs['placement_names'] = load_pv_placement_names[solar]
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



    add_utility_pv = stack[4]
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
    add_utility_pv.kwargs['placement_names'] = [utility_placement_name[solar]]
    add_utility_pv.kwargs['single_size'] = 2000000
    add_utility_pv.kwargs['max_feeder_sizing_percent'] = utility_max_feeder_sizing[solar] # total_pv <= max_feeder_size*total_feeder_load
    add_utility_pv.kwargs['power_factors'] = [0.95]
    add_utility_pv.kwargs['inverters'] = ['voltvar'] #Note that in Opendss this needs kvar to be set to 0
    add_utility_pv.kwargs['cutin'] = [0.1]
    add_utility_pv.kwargs['cutout'] = [0.1]
    add_utility_pv.kwargs['kvar_percent'] = [44]
    add_utility_pv.kwargs['oversizing'] = [1.1]

    #Create Placement for Storage
    load_selection_mapping = {'none':None, 'low':[('Random',0,5)], 'high':[('Random',0,5),('Random',5,35)]}
    # TODO put second utility BESS at substation
    utility_selection_mapping = {'none':None,'low':('Substation',1), 'high':('Substation',1,2)} #(Substation,1,2) means algorithm will select use 1 storage on the first feeder selection set and 2 storage units 
    utility_feeder_mapping = {'none':None,'low':[50],'high':[100,75]}
    load_feeder_mapping = {'none':None,'low':[100],'high':[100,100]}

    load_placement_names = {'none': None, 'low':'batsm=L.json','high':'batsm=H.json'}
    load_storage_placement_names = {'none': [None], 'low':['batsm=L.json'],'high':['batsm=L.json','batsm=H.json']}
    utility_placement_name = {'none': None, 'low':'batlg=L.json','high':'batlg=H.json'}

    load_storage_placement = stack[5]
    load_storage_placement.args[0] = load_feeder_mapping[batteries]
    load_storage_placement.args[1] = load_equipment_type
    load_storage_placement.args[2] = load_selection_mapping[batteries]
    load_storage_placement.args[3] = seed
    load_storage_placement.args[4] = placement_folder
    load_storage_placement.args[5] = load_placement_names[batteries]

    utility_storage_placement = stack[6]
    utility_storage_placement.args[0] = utility_feeder_mapping[batteries] # Length should equal selection[1]. values should be in decreasing order. This is done for the recloser selection
    utility_storage_placement.args[1] = None
    utility_storage_placement.args[2] = utility_selection_mapping[batteries]
    utility_storage_placement.args[3] = None
    utility_storage_placement.args[4] = placement_folder
    utility_storage_placement.args[5] = utility_placement_name[batteries]

    add_load_storage = stack[7]
    add_load_storage.kwargs['placement_folder'] = placement_folder
    add_load_storage.kwargs['placement_names'] = load_storage_placement_names[batteries]
    add_load_storage.kwargs['single_kw'] = 8
    add_load_storage.kwargs['single_kwh'] = 16
    add_load_storage.kwargs['kw_values'] =[4,8,25,100]
    add_load_storage.kwargs['kwh_values'] =[8,16,50,200]
    add_load_storage.kwargs['connected_pv_threshold'] =[4,10,150]
    add_load_storage.kwargs['starting_percentage'] = 50
    add_load_storage.kwargs['charge_efficiency'] = 95
    add_load_storage.kwargs['discharge_efficiency'] = 95
    add_load_storage.kwargs['oversizing'] = 1.1
    add_load_storage.kwargs['power_factor'] = 1.0
    add_load_storage.kwargs['kvar_percent'] = 65
    add_load_storage.kwargs['is_substation'] = False


    add_utility_storage = stack[8]
    add_utility_storage.kwargs['placement_folder'] = placement_folder
    add_utility_storage.kwargs['placement_names'] = [utility_placement_name[batteries]]
    add_utility_storage.kwargs['single_kw'] = 1000
    add_utility_storage.kwargs['single_kwh'] = 2000
    add_utility_storage.kwargs['starting_percentage'] = 50
    add_utility_storage.kwargs['charge_efficiency'] = 95
    add_utility_storage.kwargs['discharge_efficiency'] = 95
    add_utility_storage.kwargs['oversizing'] = 1.1
    add_utility_storage.kwargs['power_factor'] = 1.0
    add_utility_storage.kwargs['kvar_percent'] = 65
    add_utility_storage.kwargs['is_substation'] = True


    if timeseries == 'timeseries':

        #Timeseries Solar
        add_solar_timeseries = stack[9]
        dataset = dataset_dir.split('/')[2][:9] #Warning - tightly coupled to dataset naming convention
        add_solar_timeseries.kwargs['dataset'] = dataset
        add_solar_timeseries.kwargs['base_folder'] = os.path.join('..','..','Solar')
        add_solar_timeseries.kwargs['output_folder'] = os.path.join('.','results_v2',region,'timeseries_solar_'+solar+'_battery_'+batteries,'cyme')
        add_solar_timeseries.kwargs['write_cyme_file'] = False
        add_solar_timeseries.kwargs['write_opendss_file'] = True
    
        #Timeseries Loads
        add_timeseries = stack[10]
        add_timeseries.kwargs['customer_file'] = os.path.join(dataset_dir,region,'Inputs','customers_ext.txt')
        county = None
        lower_case_county = None
        if dataset == 'dataset_4':
            try: 
                f = open(os.path.join(dataset_dir,region,'Inputs','customers_ext.txt'),'r')
                line = f.readlines()[0].split(';')
                county = 'CA - '+line[-1].strip()
                lower_case_county = line[-1].strip().lower()
            except:
                county = 'CA - SanFrancisco'
                print('Warning - county not found. Using San Francisco as default')
                lower_case_county = 'sanfrancisco'
                
        if dataset == 'dataset_3':
            county = 'NC - Guilford'
            lower_case_county = 'guilford'
        if dataset == 'dataset_2':
            county = 'NM - Santa Fe'
            lower_case_county = 'santafe'
    
    
        load_map = {'dataset_4':'SanFrancisco','dataset_3':'Greensboro','dataset_2':'SantaFe'}
        load_location = load_map[dataset]
        add_timeseries.kwargs['residential_load_data'] = os.path.join('..','..','Loads','residential',load_location,'datapoints_elec_only.h5')
        add_timeseries.kwargs['residential_load_metadata'] = os.path.join('..','..','Loads','residential',load_location,'results_fips.csv')
        add_timeseries.kwargs['commercial_load_data'] = os.path.join('..','..','Loads','commercial',county,'com_'+lower_case_county+'_electricity_only.dsg')
        add_timeseries.kwargs['commercial_load_metadata'] = os.path.join('..','..','Loads','commercial',county,'results.csv')
        add_timeseries.kwargs['output_folder'] = os.path.join('.','results_v2',region,'timeseries_solar_'+solar+'_battery_'+batteries,'cyme')
        add_timeseries.kwargs['write_cyme_file'] = False
        add_timeseries.kwargs['write_opendss_file'] = True
        add_timeseries.kwargs['dataset'] = dataset

    #Write to OpenDSS
    final = stack[10+timeseries_layer_cnt]
    final.args[0] = os.path.join('.','results_v4',region,'solar_'+solar+'_batteries_'+batteries+'_'+timeseries,'opendss')
    final.kwargs['separate_feeders'] = True
    final.kwargs['separate_substations'] = True

    #Dump to Ditto json
    final_json = stack[11+timeseries_layer_cnt]
    final_json.kwargs['base_dir'] = os.path.join('.','results_v4',region, 'solar_'+solar+'_batteries_'+batteries+'_'+timeseries,'json_opendss')

    # Run OpenDSSDirect and get plots
    run_dss = stack[12+timeseries_layer_cnt]
    run_dss.kwargs['master_file'] = os.path.join('.','results_v4',region,'solar_'+solar+'_batteries_'+batteries+'_'+timeseries,'opendss','Master.dss')
    run_dss.kwargs['plot_profile'] = True
    run_dss.kwargs['output_folder'] = os.path.join('.','results_v4',region,'solar_'+solar+'_batteries_'+batteries+'_'+timeseries,'opendss','analysis')
    run_dss.kwargs['region'] = region

    stack.save(os.path.join(stack_library_dir,'json_to_opendss_stack_'+region+'_solar_'+solar+'_batteries_'+batteries+'_'+timeseries+'.json'))


def main():
    # Based on the structure in the dataset3 repo: https://github.com/Smart-DS/dataset3
#create_rnm_to_opendss_stack(os.path.join('..','..','dataset3', 'MixedHumid'), 'industrial')
    region= sys.argv[1]
    dataset = sys.argv[2]
    timeseries = sys.argv[3]

    #dataset_map = {'dataset_4':'20180727','dataset_3':'20180910','dataset_2':'20180716'}
    dataset_map = {'dataset_4':'20181120','dataset_3':'20181130','dataset_2':'20181130'}
    solar_options = ['none','low','medium','high','extreme']
    battery_options = ['none','low','high']
    timeseries_options = ['timeseries','peak']
    if timeseries not in timeseries_options:
        raise("Invalid arguments " +timeseries)

    for batteries in battery_options: #Need to create smaller areas first since they're referenced by larger areas
        for solar in solar_options:
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
