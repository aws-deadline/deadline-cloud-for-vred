@echo off
chcp 65001 > NUL:
rd /s/q output
mkdir output
python tile_assembler_test.py "7x5_tiles"
python tile_assembler_test.py "5x2_tiles"