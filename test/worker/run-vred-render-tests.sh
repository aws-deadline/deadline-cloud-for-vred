# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#!/bin/bash
rm -rf output
mkdir output
python test_vred_render.py "one_frame" "AutomotiveGenesis.vpb"
python test_vred_render.py "one_frame" "LightweightWith Spaces.vpb"