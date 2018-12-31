import os
import sys
cnt = 1
all_dirs =[d for d in os.listdir(os.path.join('..','..','dataset_4_20181115')) if os.path.isdir(os.path.join('..','..','dataset_4_20181115',d))]
sorted_dirs = []
for d in all_dirs:
    tot = sum( os.path.getsize(os.path.join(dirpath,filename)) for dirpath, dirnames, filenames in os.walk(os.path.join('..','..','dataset_4_20181115',d)) for filename in filenames )
    sorted_dirs.append((tot,d))
#sorted_dirs = [(1,'rural'),(0,'industrial'),(2,'urban-suburban')]
sorted_dirs = sorted(sorted_dirs)
dataset = 'dataset_4'

#scenario_commands = ['create_rnm_to_cyme_stack.py', 'create_rnm_to_cyme_stack_pv_pct.py','create_rnm_to_cyme_stack_pv_pct.py','create_rnm_to_cyme_stack_timeseries.py', 'create_rnm_to_cyme_stack_pv_pct_timeseries.py', 'create_rnm_to_cyme_stack_pv_pct_timeseries.py','create_rnm_to_opendss_stack.py', 'create_rnm_to_opendss_stack_pv_pct.py','create_rnm_to_opendss_stack_pv_pct.py','create_rnm_to_opendss_stack_timeseries.py', 'create_rnm_to_opendss_stack_pv_pct_timeseries.py', 'create_rnm_to_opendss_stack_pv_pct_timeseries.py']
#folder_names = ['base','15.0_pv', '85.0_pv', 'timeseries', 'timeseries_15.0_pv', 'timeseries_85.0_pv','base','15.0_pv', '85.0_pv', 'timeseries', 'timeseries_15.0_pv', 'timeseries_85.0_pv']
#scenario_params = ['',' 15',' 85','',' 15',' 85','',' 15',' 85','',' 15',' 85']
#types = ['cyme','cyme','cyme','cyme', 'cyme', 'cyme', 'opendss','opendss', 'opendss', 'opendss', 'opendss','opendss']


scenario_commands = ['create_rnm_to_cyme_stack.py', 'create_rnm_to_opendss_stack.py']
scenario_params = ['','']
folder_names = ['base','base']
types = ['cyme', 'opendss']

for sz,i in sorted_dirs:
    for j in range(len(scenario_commands)):
        f=open('v2_batch_run_scenarios_'+str(cnt)+'.sh','w')
        cnt+=1
        f.write('source activate py36\n')
        f.write('export PYTHONPATH=/projects/solfor/SMART-DS/layerstack:/projects/solfor/SMART-DS/ditto\n')
        if not os.path.exists(os.path.join('results_v2',i,folder_names[j],types[j])):
            os.makedirs(os.path.join('results_v2',i,folder_names[j],types[j]))

        f.write('rm -rf results_v2/'+i+'/'+folder_names[j]+'/'+types[j]+'/*\n')
        f.write('time python '+scenario_commands[j]+' '+i+' '+dataset + scenario_params[j])


