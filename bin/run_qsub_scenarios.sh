for i in `seq 1 24`; do
    chmod u+x run_scenarios_"$i".sh
    qsub -A igms -l walltime=48:00:00 -l qos=high -q batch-h -j oe  ./run_scenarios_"$i".sh
done
for i in `seq 25 36`; do
    chmod u+x run_scenarios_"$i".sh
    qsub -A solfor -l walltime=48:00:00 -l qos=high -l feature=256GB -q bigmem -j oe  ./run_scenarios_"$i".sh
done
