import os
import sys
cnt = 1
all_dirs =[d for d in os.listdir(os.path.join('..','..','dataset_3_20181010')) if os.path.isdir(os.path.join('..','..','dataset_3_20181010',d))]
sorted_dirs = []
for d in all_dirs:
    tot = sum( os.path.getsize(os.path.join(dirpath,filename)) for dirpath, dirnames, filenames in os.walk(os.path.join('..','..','dataset_3_20181010',d)) for filename in filenames )
    sorted_dirs.append((tot,d))
sorted_dirs = [(0,'P4U_tst')]
sorted_dirs = [(1,'rural'),(0,'industrial'),(2,'urban-suburban')]
sorted_dirs = sorted(sorted_dirs)
dataset = 'dataset_4'
dataset = 'dataset_3'
scenario_commands = ['create_rnm_to_cyme_stack.py', 'create_rnm_to_cyme_stack_pv_pct.py','create_rnm_to_cyme_stack_pv_pct.py','create_rnm_to_cyme_stack_timeseries.py', 'create_rnm_to_cyme_stack_pv_pct_timeseries.py', 'create_rnm_to_cyme_stack_pv_pct_timeseries.py','create_rnm_to_opendss_stack.py', 'create_rnm_to_opendss_stack_pv_pct.py','create_rnm_to_opendss_stack_pv_pct.py','create_rnm_to_opendss_stack_timeseries.py', 'create_rnm_to_opendss_stack_pv_pct_timeseries.py', 'create_rnm_to_opendss_stack_pv_pct_timeseries.py']
scenario_params = ['',' 15',' 85','',' 15',' 85','',' 15',' 85','',' 15',' 85']
folder_names = ['base','15.0_pv', '85.0_pv', 'timeseries', 'timeseries_15.0_pv', 'timeseries_85.0_pv','base','15.0_pv', '85.0_pv', 'timeseries', 'timeseries_15.0_pv', 'timeseries_85.0_pv']
types = ['cyme','cyme','cyme','cyme', 'cyme', 'cyme', 'opendss','opendss', 'opendss', 'opendss', 'opendss','opendss']
for sz,i in sorted_dirs:
    for j in range(len(scenario_commands)):
        f=open('run_scenarios_'+str(cnt)+'.sh','w')
        cnt+=1
        f.write('source activate py36\n')
        f.write('export PYTHONPATH=/projects/solfor/SMART-DS/layerstack:/projects/solfor/SMART-DS/ditto\n')
        if not os.path.exists(os.path.join('results',i,folder_names[j],types[j])):
            os.makedirs(os.path.join('results',i,folder_names[j],types[j]))

        f.write('rm -rf results/'+i+'/'+folder_names[j]+'/'+types[j]+'/*\n')
        f.write('python '+scenario_commands[j]+' '+i+' '+dataset + scenario_params[j])


