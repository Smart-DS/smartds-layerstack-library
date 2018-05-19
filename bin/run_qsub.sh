for i in `seq 1 18`; do
    chmod u+x wrapper_"$i".sh
    qsub -A igms -l walltime=48:00:00 -q bigmem -l qos=high -j oe ./wrapper_"$i".sh
done
