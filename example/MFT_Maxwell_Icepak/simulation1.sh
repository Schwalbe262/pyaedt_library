#!/bin/bash
#SBATCH --nodes=1
#SBATCH --partition=gpu5,gpu4,gpu3,gpu6,gpu2,gpu1,cpu1
#SBATCH --cpus-per-task=50

#SBATCH --job-name=ANSYS
#SBATCH -o ./log/SLURM.%N.%j.out         # STDOUT
#SBATCH -e ./log/SLURM.%N.%j.err         # STDERR


module purge

source ~/miniconda3/etc/profile.d/conda.sh
conda activate pyaedt_015

module load ansys-electronics/v242

# export ANSYSEM_ROOT242=/opt/ohpc/pub/Electronics/v242/Linux64
# export PATH=$ANSYSEM_ROOT242/ansysedt/bin:$PATH
# export ANSYSLMD_LICENSE_FILE=1055@172.16.10.81

# unset DISPLAY
# export QT_QPA_PLATFORM=offscreen


# export HOME=/gpfs/home1/r1jae262
# cd /gpfs/home1/r1jae262/ANSYS

python subprocess_run.py