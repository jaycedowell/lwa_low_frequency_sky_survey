#!/bin/bash

filename=${1}
outname=`basename ${filename} | sed -e 's/\..*//g;' `
outname=`echo "${outname}_Multi" `

wsclean -size 350 350 -scale 20amin -niter 10000 -weight natural -multiscale -multiscale-threshold-bias 0.8 -mgain 0.8 -nonegative -joinpolarizations -pol xx,yy -channelrange 300 1140 -joinchannels -no-update-model-required -fitsmask mask_350.fits -name ${outname} ${filename}
