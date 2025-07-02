@echo off
chcp 65001 > NUL:
rd /s/q output
mkdir output
python vred_render_test.py "one_frame" "ここにテキストを入力.vpb"
python vred_render_test.py "one_frame" "LightweightWith Spaces.vpb"