for i in `seq 1 60`; do
    chmod u+x batch_run_scenarios_"$i".sh
    qsub -A smartds -l walltime=48:00:00 -l qos=high -q batch-h -j oe  ./v2_batch_run_scenarios_"$i".sh
done
for i in `seq 80 -1 61`; do
    chmod u+x batch_run_scenarios_"$i".sh
    qsub -A smartds -l walltime=96:00:00  -l feature=256GB -l qos=high -q bigmem -j oe  ./v2_batch_run_scenarios_"$i".sh
done
