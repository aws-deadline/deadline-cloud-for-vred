# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#!/bin/bash
rm -rf output
mkdir output
python tile_assembler_test.py "7x5_tiles"
python tile_assembler_test.py "5x2_tiles"