import os
import sys
cnt = 1
all_dirs =[d for d in os.listdir(os.path.join('..','..','dataset_4_20180920')) if os.path.isdir(os.path.join('..','..','dataset_4_20180920',d))]
sorted_dirs = []
for d in all_dirs:
    tot = sum( os.path.getsize(os.path.join(dirpath,filename)) for dirpath, dirnames, filenames in os.walk(os.path.join('..','..','dataset_4_20180920',d)) for filename in filenames )
    sorted_dirs.append((tot,d))
sorted_dirs = sorted(sorted_dirs)
for sz,i in sorted_dirs:
    f=open('run_'+str(cnt)+'.sh','w')
    cnt+=1
    f.write('source activate py36\n')
    f.write('export PYTHONPATH=/projects/solfor/SMART-DS/layerstack:/projects/solfor/SMART-DS/ditto\n')
    f.write('python create_rnm_to_cyme_stack.py '+i+' dataset_4')



"""
for i in [d for d in os.listdir(os.path.join('..','..','dataset_3_20180716')) if os.path.isdir(os.path.join('..','..','dataset_3_20180716',d))]:
    f=open('run_'+str(cnt)+'.sh','w')
    cnt+=1
    f.write('source activate py36\n')
    f.write('export PYTHONPATH=/projects/solfor/SMART-DS/layerstack:/projects/solfor/SMART-DS/ditto\n')
    f.write('python create_rnm_to_cyme_stack_dataset3.py '+i)

for i in [d for d in os.listdir(os.path.join('..','..','dataset_2_20180716')) if os.path.isdir(os.path.join('..','..','dataset_2_20180716',d))]:
    f=open('run_'+str(cnt)+'.sh','w')
    cnt+=1
    f.write('source activate py36\n')
    f.write('export PYTHONPATH=/projects/solfor/SMART-DS/layerstack:/projects/solfor/SMART-DS/ditto\n')
    f.write('python create_rnm_to_cyme_stack_dataset2.py '+i)
"""
