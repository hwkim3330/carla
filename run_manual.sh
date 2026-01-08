#!/bin/bash
# CARLA 수동 운전 원클릭 실행

CARLA_ROOT="/mnt/data/Carla-0.10.0-Linux-Shipping"

pkill -f CarlaUnreal 2>/dev/null
sleep 1

echo "CARLA 서버 시작..."
$CARLA_ROOT/Linux/CarlaUnreal.sh &

echo "서버 로딩 대기 (30초)..."
sleep 30

echo "수동 운전 시작!"
echo "W/S=가속/브레이크, A/D=조향, P=자율주행, TAB=카메라, ESC=종료"

source ~/miniconda3/bin/activate carla
export PYTHONPATH="$CARLA_ROOT/PythonAPI/carla:$PYTHONPATH"
cd $CARLA_ROOT/PythonAPI/examples
python manual_control.py

pkill -f CarlaUnreal 2>/dev/null
