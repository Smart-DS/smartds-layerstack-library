for i in `seq 1 50`; do
    chmod u+x batch_run_scenarios_"$i".sh
    qsub -A smartds -l walltime=48:00:00 -l qos=high -q batch-h -j oe  ./batch_run_scenarios_"$i".sh
done
for i in `seq 51 80`; do
    chmod u+x batch_run_scenarios_"$i".sh
    qsub -A smartds -l walltime=96:00:00  -l feature=256GB -l qos=high -q bigmem -j oe  ./batch_run_scenarios_"$i".sh
done
