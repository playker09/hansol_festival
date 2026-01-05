"""Bridson Poisson-disc Sampling (2D)

간단한 구현: poisson_disc_samples(width, height, radius, k=30)
- width, height: 샘플링 영역 크기
- radius: 샘플 간 최소 거리
- k: 후보 생성 반복 횟수 (보통 30)

반환값: (x, y) 좌표 튜플의 리스트 (float)
"""
import math
import random

PI = math.pi


def poisson_disc_samples(width, height, radius, k=30, rng=None):
    if rng is None:
        rng = random

    cell_size = radius / math.sqrt(2)
    grid_width = int(math.ceil(width / cell_size))
    grid_height = int(math.ceil(height / cell_size))

    grid = [None] * (grid_width * grid_height)

    def grid_coords(pt):
        x, y = pt
        return int(x // cell_size), int(y // cell_size)

    def fits(pt):
        gx, gy = grid_coords(pt)
        rx = range(max(0, gx - 2), min(grid_width, gx + 3))
        ry = range(max(0, gy - 2), min(grid_height, gy + 3))
        for ix in rx:
            for iy in ry:
                v = grid[iy * grid_width + ix]
                if v is None:
                    continue
                dx = v[0] - pt[0]
                dy = v[1] - pt[1]
                if dx * dx + dy * dy < radius * radius:
                    return False
        return True

    samples = []
    spawn_points = []

    # 첫 샘플
    first = (rng.uniform(0, width), rng.uniform(0, height))
    samples.append(first)
    spawn_points.append(first)
    gx, gy = grid_coords(first)
    grid[gy * grid_width + gx] = first

    while spawn_points:
        idx = rng.randrange(len(spawn_points))
        center = spawn_points[idx]
        found = False
        for _ in range(k):
            ang = rng.uniform(0, 2 * PI)
            rad = rng.uniform(radius, 2 * radius)
            x = center[0] + math.cos(ang) * rad
            y = center[1] + math.sin(ang) * rad
            if not (0 <= x < width and 0 <= y < height):
                continue
            pt = (x, y)
            if fits(pt):
                samples.append(pt)
                spawn_points.append(pt)
                gx, gy = grid_coords(pt)
                grid[gy * grid_width + gx] = pt
                found = True
        if not found:
            spawn_points.pop(idx)

    return samples
