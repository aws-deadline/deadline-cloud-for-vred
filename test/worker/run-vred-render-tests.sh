# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#!/bin/bash
rm -rf output
mkdir output
python vred_render_test.py "one_frame" "AutomotiveGenesis.vpb"
python vred_render_test.py "one_frame" "LightweightWith Spaces.vpb"