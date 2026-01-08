#!/usr/bin/env python3
"""
CARLA RGB + LiDAR 오버레이 뷰
- 메인: RGB 카메라
- 미니맵: LiDAR (우하단)
- 선택: Depth, Semantic Segmentation
"""

import carla
import pygame
import numpy as np
import sys
import random
import math

sys.path.append('/mnt/data/Carla-0.10.0-Linux-Shipping/PythonAPI/carla')
from agents.navigation.behavior_agent import BehaviorAgent

# 설정
WIDTH, HEIGHT = 1280, 720
LIDAR_SIZE = 250  # 미니맵 크기

class MultiSensorView:
    def __init__(self, world, vehicle):
        self.vehicle = vehicle
        self.rgb_image = None
        self.depth_image = None
        self.semantic_image = None
        self.lidar_image = None
        self.cameras = []

        bp_lib = world.get_blueprint_library()

        # RGB 카메라
        rgb_bp = bp_lib.find('sensor.camera.rgb')
        rgb_bp.set_attribute('image_size_x', str(WIDTH))
        rgb_bp.set_attribute('image_size_y', str(HEIGHT))
        rgb_bp.set_attribute('fov', '100')
        rgb_cam = world.spawn_actor(rgb_bp,
            carla.Transform(carla.Location(x=1.5, z=2.4)),
            attach_to=vehicle)
        rgb_cam.listen(lambda img: self._process_rgb(img))
        self.cameras.append(rgb_cam)

        # Depth 카메라
        depth_bp = bp_lib.find('sensor.camera.depth')
        depth_bp.set_attribute('image_size_x', str(LIDAR_SIZE))
        depth_bp.set_attribute('image_size_y', str(LIDAR_SIZE))
        depth_cam = world.spawn_actor(depth_bp,
            carla.Transform(carla.Location(x=1.5, z=2.4)),
            attach_to=vehicle)
        depth_cam.listen(lambda img: self._process_depth(img))
        self.cameras.append(depth_cam)

        # Semantic Segmentation 카메라
        seg_bp = bp_lib.find('sensor.camera.semantic_segmentation')
        seg_bp.set_attribute('image_size_x', str(LIDAR_SIZE))
        seg_bp.set_attribute('image_size_y', str(LIDAR_SIZE))
        seg_cam = world.spawn_actor(seg_bp,
            carla.Transform(carla.Location(x=1.5, z=2.4)),
            attach_to=vehicle)
        seg_cam.listen(lambda img: self._process_semantic(img))
        self.cameras.append(seg_cam)

        # LiDAR
        lidar_bp = bp_lib.find('sensor.lidar.ray_cast')
        lidar_bp.set_attribute('range', '50')
        lidar_bp.set_attribute('rotation_frequency', '20')
        lidar_bp.set_attribute('channels', '32')
        lidar_bp.set_attribute('points_per_second', '100000')
        lidar = world.spawn_actor(lidar_bp,
            carla.Transform(carla.Location(x=0, z=2.5)),
            attach_to=vehicle)
        lidar.listen(lambda data: self._process_lidar(data))
        self.cameras.append(lidar)

    def _process_rgb(self, image):
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((HEIGHT, WIDTH, 4))[:, :, :3]
        self.rgb_image = array

    def _process_depth(self, image):
        image.convert(carla.ColorConverter.LogarithmicDepth)
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((LIDAR_SIZE, LIDAR_SIZE, 4))[:, :, :3]
        self.depth_image = array

    def _process_semantic(self, image):
        image.convert(carla.ColorConverter.CityScapesPalette)
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((LIDAR_SIZE, LIDAR_SIZE, 4))[:, :, :3]
        self.semantic_image = array

    def _process_lidar(self, data):
        points = np.frombuffer(data.raw_data, dtype=np.float32)
        points = points.reshape((-1, 4))[:, :2]  # x, y만

        # BEV 이미지 생성
        img = np.zeros((LIDAR_SIZE, LIDAR_SIZE, 3), dtype=np.uint8)

        # 포인트를 이미지 좌표로 변환
        scale = LIDAR_SIZE / 100.0  # 50m 범위
        points_img = points * scale + LIDAR_SIZE / 2
        points_img = points_img.astype(np.int32)

        # 범위 내 포인트만
        mask = (points_img[:, 0] >= 0) & (points_img[:, 0] < LIDAR_SIZE) & \
               (points_img[:, 1] >= 0) & (points_img[:, 1] < LIDAR_SIZE)
        points_img = points_img[mask]

        # 포인트 그리기 (녹색)
        for p in points_img:
            img[p[1], p[0]] = [0, 255, 0]

        # 차량 위치 (중앙, 빨간색)
        cv = LIDAR_SIZE // 2
        img[cv-3:cv+3, cv-2:cv+2] = [255, 0, 0]

        self.lidar_image = img

    def destroy(self):
        for cam in self.cameras:
            cam.destroy()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CARLA RGB + LiDAR View")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30)
    small_font = pygame.font.Font(None, 20)

    client = carla.Client('localhost', 2000)
    client.set_timeout(30.0)
    world = client.get_world()

    # 차량 스폰
    bp = world.get_blueprint_library().filter('vehicle.tesla.model3')[0]
    spawn_points = world.get_map().get_spawn_points()
    vehicle = world.spawn_actor(bp, random.choice(spawn_points))

    # 센서
    sensors = MultiSensorView(world, vehicle)

    # 자율주행
    agent = BehaviorAgent(vehicle, behavior='normal')
    agent.set_destination(random.choice(spawn_points).location)

    autopilot = True
    minimap_mode = 0  # 0: LiDAR, 1: Depth, 2: Semantic

    print("=" * 50)
    print("CARLA RGB + LiDAR View")
    print("=" * 50)
    print("P: 자율주행 ON/OFF")
    print("M: 미니맵 전환 (LiDAR/Depth/Semantic)")
    print("ESC: 종료")
    print("=" * 50)

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_p:
                        autopilot = not autopilot
                        print(f"Autopilot: {'ON' if autopilot else 'OFF'}")
                    if event.key == pygame.K_m:
                        minimap_mode = (minimap_mode + 1) % 3
                        mode_name = ['LiDAR BEV', 'Depth', 'Semantic'][minimap_mode]
                        print(f"Minimap: {mode_name}")

            # 자율주행
            if autopilot:
                if agent.done():
                    dest = random.choice(spawn_points).location
                    agent.set_destination(dest)
                    print("New destination")
                control = agent.run_step()
                vehicle.apply_control(control)

            # 메인 RGB 렌더링
            screen.fill((0, 0, 0))
            if sensors.rgb_image is not None:
                surface = pygame.surfarray.make_surface(sensors.rgb_image.swapaxes(0, 1))
                screen.blit(surface, (0, 0))

            # 미니맵 (우하단)
            minimap_img = None
            minimap_label = ""
            if minimap_mode == 0 and sensors.lidar_image is not None:
                minimap_img = sensors.lidar_image
                minimap_label = "LiDAR BEV"
            elif minimap_mode == 1 and sensors.depth_image is not None:
                minimap_img = sensors.depth_image
                minimap_label = "Depth"
            elif minimap_mode == 2 and sensors.semantic_image is not None:
                minimap_img = sensors.semantic_image
                minimap_label = "Semantic"

            if minimap_img is not None:
                minimap_surface = pygame.surfarray.make_surface(minimap_img.swapaxes(0, 1))
                # 테두리
                border_rect = pygame.Rect(WIDTH - LIDAR_SIZE - 15, HEIGHT - LIDAR_SIZE - 35, LIDAR_SIZE + 10, LIDAR_SIZE + 30)
                pygame.draw.rect(screen, (50, 50, 50), border_rect)
                pygame.draw.rect(screen, (255, 255, 255), border_rect, 2)
                # 미니맵
                screen.blit(minimap_surface, (WIDTH - LIDAR_SIZE - 10, HEIGHT - LIDAR_SIZE - 10))
                # 라벨
                label = small_font.render(minimap_label, True, (255, 255, 255))
                screen.blit(label, (WIDTH - LIDAR_SIZE - 10, HEIGHT - LIDAR_SIZE - 30))

            # HUD
            vel = vehicle.get_velocity()
            speed = 3.6 * np.sqrt(vel.x**2 + vel.y**2 + vel.z**2)

            # 상단 HUD 바
            hud_rect = pygame.Rect(0, 0, WIDTH, 40)
            pygame.draw.rect(screen, (0, 0, 0, 128), hud_rect)

            hud_text = font.render(
                f"Speed: {speed:.0f} km/h | Autopilot: {'ON' if autopilot else 'OFF'} | Minimap: {['LiDAR','Depth','Seg'][minimap_mode]} (M)",
                True, (255, 255, 255))
            screen.blit(hud_text, (10, 10))

            pygame.display.flip()
            clock.tick(30)

    finally:
        sensors.destroy()
        vehicle.destroy()
        pygame.quit()

if __name__ == '__main__':
    main()
