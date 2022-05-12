#!/bin/bash
cd $WORKDIR
pwd
echo "SUCCESS!"
python ./gqrx2dp.py -m ./models/german_model.pbmm -s ./models/german_model.scorer -r 48000 -i host.docker.internal -p 7355
