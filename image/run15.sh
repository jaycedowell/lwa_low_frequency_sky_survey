#!/bin/bash

filename=${1}
outname=`basename ${filename} | sed -e 's/\..*//g;' `
outname=`echo "${outname}_15MHz" `

#wsclean -size 350 350 -scale 20amin -niter 10000 -weight natural -mgain 0.8 -nonegative -joinpolarizations -pol xx,yy -channelrange 308 318 -no-update-model-required -name ${outname} ${filename}

isSim=`basename ${filename} | grep _SIM `
if [[ "${isSim}" == "" ]]; then
	threshold=26.4
else
	threshold=`echo "2.25*1658.9" | bc -l `
fi

shmDir=`mktemp --tmpdir=/dev/shm -d wsclean.XXXXXX `
cp -r ${filename} ${shmDir}
shmname=`basename ${filename} | xargs -n1 -i{} echo "${shmDir}/{}" `

wsclean -size 350 350 -scale 20amin -niter 75000 -threshold ${threshold} -weight natural -multiscale -multiscale-scale-bias 0.9 -mgain 0.6 -nonegative -joinpolarizations -pol xx,yy -joinchannels -channelrange 100 140 -no-update-model-required -fitsmask mask_350.fits -name ${outname} ${shmname} > ${outname}.log 2>&1

rm -rf ${shmDir}
