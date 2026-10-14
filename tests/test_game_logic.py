"""
Unit tests for core game simulation logic:
- Car acceleration, braking, coasting, and off-road penalties
- Priority of brake over throttle
- Track projection segment wrapping
- Collision detection and near-miss bonuses
- Scoring metrics and multiplier escalation
"""

import pytest
from game.car import PlayerCar
from game.road import TrackManager
from game.obstacles import TrafficManager, OpponentCar
from game.collision import CollisionSystem
from game.scoring import ScoringSystem
from config import MAX_SPEED_KMH, MAX_OFFROAD_SPEED


def test_car_acceleration_and_braking():
    """Car should smoothly accelerate with throttle and decelerate with brakes."""
    car = PlayerCar()
    assert car.speed == 0.0

    # Accelerate for 1 second
    car.update(dt=1.0, steer_input=0.0, is_accel=True, is_brake=False, road_curve=0.0)
    assert car.speed > 0.0
    initial_speed = car.speed

    # Accelerate more
    car.update(dt=1.0, steer_input=0.0, is_accel=True, is_brake=False, road_curve=0.0)
    assert car.speed > initial_speed

    # Brake for 1 second
    car.update(dt=1.0, steer_input=0.0, is_accel=False, is_brake=True, road_curve=0.0)
    assert car.speed < car.max_speed


def test_brake_strictly_overrides_accel():
    """If both accel and brake flags are passed, brake MUST dominate."""
    car = PlayerCar()
    car.speed = 100.0

    # Both active -> should slow down as brake overrides
    car.update(dt=1.0, steer_input=0.0, is_accel=True, is_brake=True, road_curve=0.0)
    assert car.speed < 100.0


def test_car_offroad_penalty():
    """Offroad driving (|x| > 1.0) must heavily limit top speed."""
    car = PlayerCar()
    car.speed = 180.0
    car.x = 1.3  # Out on grass

    for _ in range(20):
        car.update(dt=0.1, steer_input=0.0, is_accel=True, is_brake=False, road_curve=0.0)

    # Speed should drop down towards MAX_OFFROAD_SPEED
    assert car.speed <= MAX_OFFROAD_SPEED + 15.0


def test_track_wrapping():
    """Segments should wrap around continuously without index out of bounds."""
    track = TrackManager()
    total_len = track.total_world_length

    seg_0 = track.get_segment(0)
    seg_wrap = track.get_segment(total_len)
    assert seg_0.index == seg_wrap.index

    # Check way beyond track
    seg_far = track.get_segment(total_len * 5 + 400)
    assert seg_far is not None
    assert 0 <= seg_far.index < track.track_length


def test_collision_detection():
    """Direct impact between player car and opponent car must register a crash."""
    car = PlayerCar()
    car.speed = 120.0
    car.x = 0.0
    car.z = 1000.0

    traffic = TrafficManager(track_length=1500, total_world_len=300000.0)
    traffic.cars.clear()
    traffic.obstacles.clear()

    # Place opponent right in player's path
    traffic.cars.append(OpponentCar(z=1020.0, x=0.0, speed_kmh=60.0))

    collision = CollisionSystem()
    has_collided, is_near_miss = collision.check_collisions(car, traffic, 300000.0)

    assert has_collided is True
    # Car speed should be penalized
    assert car.speed < 120.0


def test_near_miss_bonus():
    """Passing close to an opponent without hitting triggers a near-miss."""
    car = PlayerCar()
    car.speed = 120.0
    car.x = 0.0
    car.z = 1000.0

    traffic = TrafficManager(track_length=1500, total_world_len=300000.0)
    traffic.cars.clear()
    traffic.obstacles.clear()

    # Place opponent laterally close (dx = 0.40, collision threshold is 0.32)
    traffic.cars.append(OpponentCar(z=1020.0, x=0.40, speed_kmh=60.0))

    collision = CollisionSystem()
    has_collided, is_near_miss = collision.check_collisions(car, traffic, 300000.0)

    assert has_collided is False
    assert is_near_miss is True


def test_scoring_system():
    """Scoring should accumulate distance, scale multipliers with speed, and record high scores."""
    scoring = ScoringSystem()
    scoring.reset()

    # Driving at 150 km/h
    scoring.update(dt=1.0, speed_kmh=150.0)
    assert scoring.distance_meters > 0.0
    assert scoring.score > 0
    assert scoring.speed_multiplier >= 1.5

    # Near miss adds bonus
    score_before = scoring.score
    scoring.add_near_miss()
    assert scoring.score > score_before
    assert scoring.near_misses == 1
