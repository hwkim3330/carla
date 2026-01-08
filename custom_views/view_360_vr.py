#!/usr/bin/env python3
"""
CARLA 360도 VR 카메라 뷰
- 갤럭시 XR 등 VR 헤드셋용 equirectangular 파노라마
- 6방향 카메라로 360도 뷰 생성
"""

import carla
import pygame
import numpy as np
import sys
import random

sys.path.append('/mnt/data/Carla-0.10.0-Linux-Shipping/PythonAPI/carla')
from agents.navigation.behavior_agent import BehaviorAgent

# 설정
WIDTH, HEIGHT = 1920, 960  # 2:1 equirectangular 비율
CAM_SIZE = 480
FOV = 90

class Camera360VR:
    def __init__(self, world, vehicle):
        self.vehicle = vehicle
        # 6방향: 전/후/좌/우/상/하
        self.images = {}
        self.cameras = []

        bp = world.get_blueprint_library().find('sensor.camera.rgb')
        bp.set_attribute('image_size_x', str(CAM_SIZE))
        bp.set_attribute('image_size_y', str(CAM_SIZE))
        bp.set_attribute('fov', str(FOV))

        # 6방향 카메라 설정 (큐브맵)
        directions = {
            'front': (0, 0),
            'back': (180, 0),
            'left': (-90, 0),
            'right': (90, 0),
            'up': (0, -90),
            'down': (0, 90),
        }

        for name, (yaw, pitch) in directions.items():
            transform = carla.Transform(
                carla.Location(x=0.3, z=1.7),
                carla.Rotation(yaw=yaw, pitch=pitch)
            )
            cam = world.spawn_actor(bp, transform, attach_to=vehicle)
            cam.listen(lambda img, n=name: self._process(img, n))
            self.cameras.append(cam)
            self.images[name] = None

    def _process(self, image, name):
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((CAM_SIZE, CAM_SIZE, 4))[:, :, :3]
        self.images[name] = array

    def get_panorama(self):
        """4방향 파노라마 (좌-전-우-후)"""
        if any(self.images[k] is None for k in ['front', 'back', 'left', 'right']):
            return None

        # 수평 파노라마
        panorama = np.hstack([
            self.images['left'],
            self.images['front'],
            self.images['right'],
            self.images['back'],
        ])

        # 2:1 비율로 리사이즈
        panorama = np.array(pygame.transform.scale(
            pygame.surfarray.make_surface(panorama.swapaxes(0,1)),
            (WIDTH, HEIGHT)
        ).get_view().raw)

        return panorama

    def get_full_360(self):
        """상/하 포함 전체 360 뷰 (3x2 그리드)"""
        if any(v is None for v in self.images.values()):
            return None

        # 3x2 그리드: [상단: 좌/전/우] [하단: 하/후/상]
        top = np.hstack([self.images['left'], self.images['front'], self.images['right']])
        bottom = np.hstack([self.images['down'], self.images['back'], self.images['up']])
        full = np.vstack([top, bottom])
        return full

    def destroy(self):
        for cam in self.cameras:
            cam.destroy()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CARLA 360° VR View")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    client = carla.Client('localhost', 2000)
    client.set_timeout(30.0)
    world = client.get_world()

    # 차량 스폰
    bp = world.get_blueprint_library().filter('vehicle.tesla.model3')[0]
    spawn_points = world.get_map().get_spawn_points()
    vehicle = world.spawn_actor(bp, random.choice(spawn_points))

    # 360 카메라
    cam360 = Camera360VR(world, vehicle)

    # 자율주행
    agent = BehaviorAgent(vehicle, behavior='normal')
    agent.set_destination(random.choice(spawn_points).location)

    autopilot = True
    view_mode = 0  # 0: 파노라마, 1: 큐브맵

    print("=" * 50)
    print("CARLA 360° VR View")
    print("=" * 50)
    print("P: 자율주행 ON/OFF")
    print("V: 뷰 모드 전환 (파노라마/큐브맵)")
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
                    if event.key == pygame.K_v:
                        view_mode = (view_mode + 1) % 2
                        mode_name = ['Panorama', 'Cubemap'][view_mode]
                        print(f"View: {mode_name}")

            # 자율주행
            if autopilot:
                if agent.done():
                    dest = random.choice(spawn_points).location
                    agent.set_destination(dest)
                    print("New destination")
                control = agent.run_step()
                vehicle.apply_control(control)

            # 렌더링
            screen.fill((0, 0, 0))

            if view_mode == 0:
                img = cam360.get_panorama()
                if img is not None:
                    surface = pygame.surfarray.make_surface(img.swapaxes(0, 1))
                    screen.blit(surface, (0, 0))
            else:
                img = cam360.get_full_360()
                if img is not None:
                    surface = pygame.surfarray.make_surface(img.swapaxes(0, 1))
                    # 화면에 맞게 스케일
                    surface = pygame.transform.scale(surface, (WIDTH, HEIGHT))
                    screen.blit(surface, (0, 0))

            # HUD
            vel = vehicle.get_velocity()
            speed = 3.6 * np.sqrt(vel.x**2 + vel.y**2 + vel.z**2)
            hud_text = font.render(f"Speed: {speed:.0f} km/h | Auto: {'ON' if autopilot else 'OFF'}", True, (255, 255, 255))
            screen.blit(hud_text, (10, 10))

            pygame.display.flip()
            clock.tick(30)

    finally:
        cam360.destroy()
        vehicle.destroy()
        pygame.quit()

if __name__ == '__main__':
    main()
