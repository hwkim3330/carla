# CARLA UE5 시뮬레이터 가이드

CARLA 0.10.0 (Unreal Engine 5) 자율주행 시뮬레이터 설치 및 사용 가이드

## 설치

### 1. CARLA 다운로드
```bash
# CARLA 0.10.0 Linux 다운로드
wget https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/Carla-0.10.0-Linux-Shipping.tar.gz
tar -xzf Carla-0.10.0-Linux-Shipping.tar.gz
```

### 2. Python 환경 설정 (Conda)
```bash
# Python 3.10 환경 생성 (필수 - CARLA 0.10.0은 Python 3.10 필요)
conda create -n carla python=3.10 -y
conda activate carla

# CARLA Python 패키지 설치
pip install Carla-0.10.0-Linux-Shipping/PythonAPI/carla/dist/carla-0.10.0-cp310-cp310-linux_x86_64.whl

# 필수 패키지
pip install pygame numpy shapely networkx
```

### 3. 환경 변수 설정
```bash
# ~/.bashrc에 추가
export CARLA_ROOT=/path/to/Carla-0.10.0-Linux-Shipping
export PYTHONPATH=$CARLA_ROOT/PythonAPI/carla:$PYTHONPATH
```

## 원클릭 실행 (권장)

```bash
# 이 레포지토리 클론
git clone https://github.com/hwkim3330/carla.git
cd carla

# 실행 권한 부여
chmod +x *.sh

# 메뉴 선택 실행
./run_carla.sh

# 또는 바로가기 스크립트
./run_manual.sh      # 수동 운전
./run_autopilot.sh   # 자율주행 무한
```

### 스크립트 설명

| 스크립트 | 설명 |
|---------|------|
| `run_carla.sh` | 메뉴에서 모드 선택 |
| `run_manual.sh` | 수동 운전 바로 시작 |
| `run_autopilot.sh` | 자율주행 무한 바로 시작 |

> **Note:** 스크립트가 자동으로 서버 시작 → 로딩 대기 → 클라이언트 실행 → 종료 시 서버 정리까지 처리합니다.

## 수동 실행

### CARLA 서버 시작
```bash
# 서버 실행 (UE5 창이 열림)
./Carla-0.10.0-Linux-Shipping/Linux/CarlaUnreal.sh
```

### Python 클라이언트 실행
```bash
conda activate carla
cd Carla-0.10.0-Linux-Shipping/PythonAPI/examples

# 수동 운전
python manual_control.py

# 자율주행 (무한 반복)
python automatic_control.py --loop

# 멀티 센서 뷰
python visualize_multiple_sensors.py
```

## 단축키

### manual_control.py

#### 차량 조작
| 키 | 기능 |
|---|---|
| `W` | 가속 |
| `S` | 브레이크 |
| `A` / `D` | 좌/우 조향 |
| `Q` | 후진 전환 |
| `Space` | 핸드브레이크 |
| `P` | 자율주행 ON/OFF |
| `M` | 수동 변속 모드 |
| `,` / `.` | 기어 다운/업 |
| `Ctrl + W` | 정속 주행 (60km/h) |

#### 카메라/센서
| 키 | 기능 |
|---|---|
| `TAB` | 카메라 위치 변경 |
| `` ` `` 또는 `N` | 다음 센서 |
| `1` - `9` | 센서 직접 선택 |
| `G` | 레이더 시각화 |

#### 센서 목록
1. RGB 카메라
2. Depth (Raw)
3. Depth (Gray Scale)
4. Depth (Logarithmic)
5. Semantic Segmentation (Raw)
6. Semantic Segmentation (CityScapes)
7. LiDAR

#### 조명
| 키 | 기능 |
|---|---|
| `L` | 다음 라이트 타입 |
| `Shift + L` | 상향등 |
| `Z` / `X` | 우/좌 방향지시등 |
| `I` | 실내등 |

#### 환경/기타
| 키 | 기능 |
|---|---|
| `C` | 날씨 변경 |
| `Shift + C` | 날씨 역순 변경 |
| `Backspace` | 차량 변경 |
| `O` | 문 열기/닫기 |
| `T` | 텔레메트리 표시 |
| `V` | 맵 레이어 선택 |
| `B` | 맵 레이어 로드 |
| `R` | 이미지 녹화 |

#### 시뮬레이션 녹화
| 키 | 기능 |
|---|---|
| `Ctrl + R` | 시뮬레이션 녹화 시작 |
| `Ctrl + P` | 녹화 재생 |
| `Ctrl + +` | 재생 시작 시간 +1초 |
| `Ctrl + -` | 재생 시작 시간 -1초 |

#### UI
| 키 | 기능 |
|---|---|
| `F1` | HUD 토글 |
| `H` / `?` | 도움말 |
| `ESC` | 종료 |

### automatic_control.py

| 키 | 기능 |
|---|---|
| `ESC` | 종료 |
| `Q` + `Ctrl` | 종료 |

#### 명령줄 옵션
```bash
# 무한 자율주행 (목적지 도착 시 새 목적지 설정)
python automatic_control.py --loop

# 동기화 모드
python automatic_control.py --sync

# 해상도 설정
python automatic_control.py --res 1920x1080

# 에이전트 타입 선택
python automatic_control.py --agent Behavior  # 기본값
python automatic_control.py --agent Basic
python automatic_control.py --agent Constant

# 운전 스타일
python automatic_control.py --behavior cautious
python automatic_control.py --behavior normal   # 기본값
python automatic_control.py --behavior aggressive
```

## 구조

```
CARLA 구조:
┌─────────────────────┐     ┌─────────────────────┐
│  CARLA UE5 서버     │◄───►│  Python 클라이언트  │
│  (CarlaUnreal.sh)   │     │  (pygame 창)        │
│                     │     │                     │
│  - 물리 시뮬레이션  │     │  - 시각화           │
│  - 렌더링           │     │  - 차량 제어        │
│  - 센서 시뮬레이션  │     │  - 자율주행 에이전트│
└─────────────────────┘     └─────────────────────┘
      (백엔드)                    (프론트엔드)
```

## 문제 해결

### pygame 검정 화면
```bash
# SDL 드라이버 설정
export SDL_VIDEODRIVER=x11
```

### 연결 거부 (Connection refused)
- CARLA 서버가 완전히 로드될 때까지 기다림 (30초~1분)
- 서버 창에서 맵이 보이는지 확인

### Python 버전 오류
- CARLA 0.10.0은 Python 3.10 필요
- conda 환경 사용 권장

## 요구사항

- Ubuntu 20.04 / 22.04 / 24.04
- NVIDIA GPU (RTX 2060 이상 권장)
- NVIDIA 드라이버 515+
- Python 3.10
- 최소 12GB VRAM (UE5)

## 참고

- [CARLA 공식 문서](https://carla.readthedocs.io/)
- [CARLA GitHub](https://github.com/carla-simulator/carla)
