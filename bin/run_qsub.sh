#for i in `seq 1 20`; do
#    chmod u+x run_"$i".sh
#    qsub -A solfor -l walltime=48:00:00 -q batch -j oe  ./run_"$i".sh
#done
#
#for i in `seq 21 40`; do
#    chmod u+x run_"$i".sh
#    qsub -A solfor -l walltime=120:00:00 -q bigmem -j oe  ./run_"$i".sh
#done

arr=( 17 19 20 32 34 37 )
for i in ${arr[@]}; do
    chmod u+x run_"$i".sh
    qsub -A solfor -l walltime=120:00:00 -l feature=256GB -q bigmem -j oe  ./run_"$i".sh
done
