#!/usr/bin/env python3
"""
CARLA 360도 VR 뷰

TODO: 현재 검정 화면 이슈 있음 - 추후 수정 필요
- pygame 카메라 렌더링이 안되는 문제
- manual_control.py는 되는데 커스텀 스크립트는 안됨
- 가능한 원인: Vulkan 드라이버, headless 모드, 센서 타이밍

실행: python view_360_vr.py
"""

import carla
import pygame
import numpy as np
import random
import sys
import weakref
import time

sys.path.append('/mnt/data/Carla-0.10.0-Linux-Shipping/PythonAPI/carla')
from agents.navigation.behavior_agent import BehaviorAgent

# 설정
CAM_SIZE = 400
WINDOW_W = CAM_SIZE * 4
WINDOW_H = CAM_SIZE


class CameraManager:
    def __init__(self, world, vehicle, yaw, display_pos):
        self.surface = None
        self.display_pos = display_pos
        self.frame_count = 0

        bp = world.get_blueprint_library().find('sensor.camera.rgb')
        bp.set_attribute('image_size_x', str(CAM_SIZE))
        bp.set_attribute('image_size_y', str(CAM_SIZE))
        bp.set_attribute('fov', '90')

        transform = carla.Transform(
            carla.Location(x=0, z=2.4),
            carla.Rotation(yaw=yaw)
        )

        self.sensor = world.spawn_actor(bp, transform, attach_to=vehicle)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda image: CameraManager._on_image(weak_self, image))

    @staticmethod
    def _on_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        self.frame_count += 1
        image.convert(carla.ColorConverter.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3][:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (self.display_pos * CAM_SIZE, 0))

    def destroy(self):
        if self.sensor and self.sensor.is_alive:
            self.sensor.stop()
            self.sensor.destroy()


def main():
    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.HWSURFACE | pygame.DOUBLEBUF)
    display.fill((0, 0, 0))
    pygame.display.flip()
    pygame.display.set_caption('CARLA 360 View')
    font = pygame.font.Font(None, 30)

    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    vehicle = None
    cameras = []

    try:
        # 차량 스폰
        bp = random.choice(list(world.get_blueprint_library().filter('vehicle.*')))
        spawn_points = world.get_map().get_spawn_points()
        vehicle = world.spawn_actor(bp, random.choice(spawn_points))
        print(f"Vehicle: {vehicle.type_id}")

        # 4방향 카메라
        cameras = [
            CameraManager(world, vehicle, -90, 0),   # 좌
            CameraManager(world, vehicle, 0, 1),     # 전
            CameraManager(world, vehicle, 90, 2),    # 우
            CameraManager(world, vehicle, 180, 3),   # 후
        ]

        # 자율주행 에이전트
        agent = BehaviorAgent(vehicle, behavior='normal')
        agent.set_destination(random.choice(spawn_points).location)

        print("=" * 40)
        print("CARLA 360 View")
        print("P: 자율주행 ON/OFF")
        print("ESC: 종료")
        print("=" * 40)

        autopilot = True
        clock = pygame.time.Clock()

        # 센서 초기화 대기
        time.sleep(0.5)
        world.wait_for_tick()

        while True:
            world.wait_for_tick()
            clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        return
                    if event.key == pygame.K_p:
                        autopilot = not autopilot
                        print(f"Autopilot: {'ON' if autopilot else 'OFF'}")

            if autopilot:
                if agent.done():
                    agent.set_destination(random.choice(spawn_points).location)
                control = agent.run_step()
                vehicle.apply_control(control)

            # 렌더링
            display.fill((0, 0, 0))
            for cam in cameras:
                cam.render(display)

            # HUD
            v = vehicle.get_velocity()
            speed = 3.6 * (v.x**2 + v.y**2 + v.z**2)**0.5
            frames = sum(c.frame_count for c in cameras)
            text = font.render(f'{speed:.0f} km/h | Auto: {"ON" if autopilot else "OFF"} | Frames: {frames}', True, (255, 255, 255))
            display.blit(text, (10, WINDOW_H - 30))

            pygame.display.flip()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Cleaning up...")
        for cam in cameras:
            try:
                cam.destroy()
            except:
                pass
        if vehicle:
            try:
                vehicle.destroy()
            except:
                pass
        pygame.quit()


if __name__ == '__main__':
    main()
