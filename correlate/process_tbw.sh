#!/bin/bash

# Path to correlateTBW.py and the correct SSMIF
SCRIPT_PATH=`realpath ${0} | xargs dirname`

# The actual correlator call with:
#  -p for the PFB
#  -l 3920 to get 25 kHz wide channels
#  -2 for only XX and YY
#  --casa for measurement sets
python3 ${SCRIPT_PATH}/correlateTBW.py -m ${SCRIPT_PATH}/SSMIF_181022.txt -p -l 3920 -2 --casa ${1}
