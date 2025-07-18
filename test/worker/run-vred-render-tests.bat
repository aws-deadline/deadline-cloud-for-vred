@echo off
chcp 65001 > NUL:
rd /s/q output
mkdir output
python test_vred_render.py "one_frame" "ここにテキストを入力.vpb"
python test_vred_render.py "one_frame" "LightweightWith Spaces.vpb"