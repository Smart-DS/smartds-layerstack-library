import sys
import os
path_to_data = os.path.join('..', '..', 'duke_data','Cleaned_DUKE_data')
cnt = 1
for area in os.listdir(path_to_data):
    if not os.path.exists(os.path.join('./results', 'duke', area)):
        os.makedirs(os.path.join('./results', 'duke', area))
    output = open('wrapper_%d.sh'%cnt,'w')
    output.write('export PYTHONPATH=/scratch/telgindy/SMART-DS/layerstack:/scratch/telgindy/SMART-DS/ditto\n') 
    output.write('source activate py36\n')
    output.write('python create_compute_metrics_from_duke_stack.py {dir}'.format(dir=area))
    output.close()
    cnt+=1



    
