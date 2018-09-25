for i in `seq 1 36`; do
    chmod u+x run_scenarios_"$i".sh
    qsub -A solfor -l walltime=48:00:00 -q batch -j oe  ./run_scenarios_"$i".sh
done
