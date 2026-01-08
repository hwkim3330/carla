#!/bin/bash
# CARLA RGB + LiDAR 뷰 원클릭 실행

CARLA_ROOT="/mnt/data/Carla-0.10.0-Linux-Shipping"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

pkill -f CarlaUnreal 2>/dev/null
sleep 1

echo "CARLA 서버 시작..."
$CARLA_ROOT/Linux/CarlaUnreal.sh &

echo "서버 로딩 대기 (30초)..."
sleep 30

echo "RGB + LiDAR 뷰 시작!"
echo "P=자율주행, M=미니맵전환, ESC=종료"

source ~/miniconda3/bin/activate carla
python $SCRIPT_DIR/custom_views/view_rgb_lidar.py

pkill -f CarlaUnreal 2>/dev/null
