#!/bin/bash
# CARLA 원클릭 실행 스크립트

CARLA_ROOT="/mnt/data/Carla-0.10.0-Linux-Shipping"
CONDA_ENV="carla"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}   CARLA UE5 시뮬레이터${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 기존 CARLA 프로세스 종료
pkill -f CarlaUnreal 2>/dev/null
pkill -f "python.*control" 2>/dev/null
sleep 1

# 메뉴
echo -e "${YELLOW}실행 모드 선택:${NC}"
echo "  1) 수동 운전 (manual_control.py)"
echo "  2) 자율주행 무한 (automatic_control.py --loop)"
echo "  3) 멀티 센서 뷰 (visualize_multiple_sensors.py)"
echo "  4) 서버만 실행"
echo "  5) 종료"
echo ""
read -p "선택 [1-5]: " choice

if [ "$choice" == "5" ]; then
    echo "종료합니다."
    exit 0
fi

# CARLA 서버 시작
echo -e "\n${GREEN}[1/3] CARLA 서버 시작 중...${NC}"
$CARLA_ROOT/Linux/CarlaUnreal.sh &
SERVER_PID=$!

# 서버 로딩 대기
echo -e "${GREEN}[2/3] 서버 로딩 대기 (약 30초)...${NC}"
sleep 30

# 서버 확인
if ! pgrep -f CarlaUnreal > /dev/null; then
    echo -e "${RED}서버 시작 실패!${NC}"
    exit 1
fi

echo -e "${GREEN}[3/3] 서버 준비 완료!${NC}"

if [ "$choice" == "4" ]; then
    echo -e "\n${GREEN}서버만 실행 중. 종료하려면 Ctrl+C${NC}"
    wait $SERVER_PID
    exit 0
fi

# Conda 환경 활성화 및 클라이언트 실행
echo -e "\n${GREEN}Python 클라이언트 시작...${NC}"

source ~/miniconda3/bin/activate $CONDA_ENV
export PYTHONPATH="$CARLA_ROOT/PythonAPI/carla:$PYTHONPATH"
cd $CARLA_ROOT/PythonAPI/examples

case $choice in
    1)
        echo -e "${YELLOW}수동 운전 모드${NC}"
        echo "단축키: W/S=가속/브레이크, A/D=조향, P=자율주행, TAB=카메라, ESC=종료"
        python manual_control.py
        ;;
    2)
        echo -e "${YELLOW}자율주행 무한 모드${NC}"
        echo "단축키: ESC=종료"
        python automatic_control.py --loop
        ;;
    3)
        echo -e "${YELLOW}멀티 센서 뷰${NC}"
        python visualize_multiple_sensors.py
        ;;
esac

# 클라이언트 종료 시 서버도 종료
echo -e "\n${YELLOW}서버 종료 중...${NC}"
pkill -f CarlaUnreal 2>/dev/null
echo -e "${GREEN}완료!${NC}"
