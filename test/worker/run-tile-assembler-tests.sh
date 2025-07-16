# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#!/bin/bash
rm -rf output
mkdir output
python test_tile_assembler.py "7x5_tiles"
python test_tile_assembler.py "5x2_tiles"