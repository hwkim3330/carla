#!/bin/bash
# CARLA 자율주행 무한 원클릭 실행

CARLA_ROOT="/mnt/data/Carla-0.10.0-Linux-Shipping"

pkill -f CarlaUnreal 2>/dev/null
sleep 1

echo "CARLA 서버 시작..."
$CARLA_ROOT/Linux/CarlaUnreal.sh &

echo "서버 로딩 대기 (30초)..."
sleep 30

echo "자율주행 무한 모드 시작!"
echo "ESC=종료"

source ~/miniconda3/bin/activate carla
export PYTHONPATH="$CARLA_ROOT/PythonAPI/carla:$PYTHONPATH"
cd $CARLA_ROOT/PythonAPI/examples
python automatic_control.py --loop

pkill -f CarlaUnreal 2>/dev/null
