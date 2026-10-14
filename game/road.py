"""
Pseudo-3D Road Projection and Track Generation Engine for GestureDrive AI.
Implements curved road rendering, elevation changes (hills), road markings, and roadside sprite management.
"""

import math
import random
from typing import List, Tuple, Dict, Any, Optional
import pygame

from config import (
    ROAD_WIDTH, SEGMENT_LENGTH, RUMBLE_LENGTH, LANES,
    CAMERA_HEIGHT, CAMERA_DEPTH, DRAW_DISTANCE, TRACK_LENGTH,
    ROAD_COLORS, WINDOW_WIDTH, WINDOW_HEIGHT
)


class RoadSegment:
    """A single discrete cross-section of the 3D race track."""

    def __init__(self, index: int, z: float, curve: float = 0.0, y: float = 0.0):
        self.index = index
        self.world_z = z
        self.curve = curve
        self.world_y = y  # Elevation (hills)

        # Projected 2D screen coordinates (updated during render)
        self.screen_x = 0.0
        self.screen_y = 0.0
        self.screen_w = 0.0
        self.scale = 0.0
        self.clip = float(WINDOW_HEIGHT)

        # Color key
        self.is_dark = (index // RUMBLE_LENGTH) % 2 == 1
        self.color = ROAD_COLORS["dark" if self.is_dark else "light"]

        # Attached sprites and obstacles
        self.sprites: List[Dict[str, Any]] = []
        self.opponent_car = None
        self.obstacle = None

    def project(self, camera_x: float, camera_y: float, camera_z: float, depth: float, width: int, height: int):
        """Project 3D world coordinates into 2D screen coordinates."""
        dz = self.world_z - camera_z
        if dz <= 0:
            dz = 0.001

        self.scale = depth / dz
        self.screen_x = (width * 0.5) + (self.scale * (0 - camera_x) * (width * 0.5))
        self.screen_y = (height * 0.5) - (self.scale * (self.world_y - camera_y) * (height * 0.5))
        self.screen_w = self.scale * ROAD_WIDTH * (width * 0.5)


class TrackManager:
    """Generates procedural race tracks with curves, rolling hills, and roadside scenery."""

    def __init__(self):
        self.segments: List[RoadSegment] = []
        self.track_length = TRACK_LENGTH
        self.total_world_length = TRACK_LENGTH * SEGMENT_LENGTH
        self._build_track()

    def _build_track(self):
        """Construct a varied, exciting race course."""
        self.segments.clear()

        # Track sections: (length_in_segments, curve, hill_height)
        sections = [
            (50, 0.0, 0.0),       # Start line straight
            (60, 2.0, 0.0),       # Gentle right curve
            (50, 0.0, 400.0),     # Uphill crest
            (60, -2.5, -400.0),   # Downhill left sweeper
            (40, 0.0, 0.0),       # Flat straight
            (70, -3.5, 200.0),    # Sharp left turn over ridge
            (50, 3.0, 0.0),       # Right chicane
            (60, -2.0, 0.0),      # Left chicane
            (80, 0.0, 600.0),     # Big rollercoaster hill
            (80, 2.5, -600.0),    # High-speed descent
            (60, -1.8, 0.0),      # Technical turn
            (70, 0.0, 0.0),       # Grandstand final straight
        ]

        current_y = 0.0
        seg_idx = 0

        for num_segs, target_curve, target_y in sections:
            for i in range(num_segs):
                z = seg_idx * SEGMENT_LENGTH
                # Smooth curve and hill transitions using ease-in-out cosine
                ratio = i / max(1, num_segs)
                curve = target_curve * math.sin(ratio * math.pi)
                y = current_y + (target_y * math.sin(ratio * math.pi * 0.5))

                segment = RoadSegment(index=seg_idx, z=z, curve=curve, y=y)

                # Add roadside scenery (trees, lampposts, billboards)
                if seg_idx % 4 == 0:
                    side = -1.6 if random.random() < 0.5 else 1.6
                    sprite_type = random.choice(["tree", "lamp", "billboard", "rock"])
                    segment.sprites.append({
                        "type": sprite_type,
                        "offset": side,
                        "color": random.choice([(40, 180, 80), (30, 150, 60), (220, 180, 50)])
                    })

                self.segments.append(segment)
                seg_idx += 1

            current_y += target_y

        self.track_length = len(self.segments)
        self.total_world_length = self.track_length * SEGMENT_LENGTH

    def get_segment(self, z: float) -> RoadSegment:
        """Retrieve segment at world position z, wrapping around for infinite looping."""
        wrapped_z = z % self.total_world_length
        idx = int(wrapped_z / SEGMENT_LENGTH) % self.track_length
        return self.segments[idx]

    def render(self, surface: pygame.Surface, player_x: float, player_z: float, player_y: float):
        """Render the pseudo-3D road perspective."""
        w, h = WINDOW_WIDTH, WINDOW_HEIGHT
        base_segment = self.get_segment(player_z)
        base_idx = base_segment.index

        camera_x = player_x * ROAD_WIDTH
        camera_y = CAMERA_HEIGHT + player_y
        camera_z = player_z - (CAMERA_DEPTH * 1000)

        # Track curve offset accumulation
        dx = -(base_segment.curve * (player_z % SEGMENT_LENGTH) / SEGMENT_LENGTH)
        x = 0.0
        max_y = float(h)

        # 1. Draw distant sky gradient and horizon
        self._render_sky_and_horizon(surface, player_x)

        # 2. Project road segments from camera forward
        projected = []
        for n in range(DRAW_DISTANCE):
            seg_idx = (base_idx + n) % self.track_length
            segment = self.segments[seg_idx]

            # Adjust segment world_z if wrapping around
            loop_offset = self.total_world_length if (base_idx + n) >= self.track_length else 0
            temp_z = segment.world_z + loop_offset

            # Apply curve accumulator
            segment.project(camera_x - x, camera_y, camera_z, CAMERA_DEPTH, w, h)
            x += dx
            dx += segment.curve

            if segment.screen_y >= max_y:
                continue

            max_y = segment.screen_y
            projected.append(segment)

        # 3. Draw road polygons back-to-front
        for i in range(len(projected) - 1, 0, -1):
            seg1 = projected[i]
            seg2 = projected[i - 1]

            # Road clipping against hills
            if seg1.screen_y >= seg2.screen_y:
                continue

            # Draw Grass, Rumble strips, Road asphalt, and Lane stripes
            self._render_segment_poly(surface, seg1, seg2)

        # 4. Draw Roadside Sprites and Obstacles back-to-front
        for i in range(len(projected) - 1, -1, -1):
            seg = projected[i]
            for sprite in seg.sprites:
                self._render_sprite(surface, seg, sprite)

    def _render_sky_and_horizon(self, surface: pygame.Surface, player_x: float):
        """Draw gradient sky, horizon mountains, and cyber grid."""
        w, h = WINDOW_WIDTH, WINDOW_HEIGHT
        horizon_y = h // 2

        # Sky gradient: Deep space purple-blue down to cyan twilight
        pygame.draw.rect(surface, (14, 16, 32), (0, 0, w, horizon_y))
        pygame.draw.rect(surface, (28, 32, 60), (0, horizon_y - 80, w, 80))

        # Distant mountain silhouettes that shift with player steering (parallax effect)
        parallax_shift = int(-player_x * 80) % w
        for mountain_x in range(-w, w * 2, 240):
            mx = mountain_x + parallax_shift
            pts = [(mx, horizon_y), (mx + 120, horizon_y - 75), (mx + 240, horizon_y)]
            pygame.draw.polygon(surface, (20, 24, 46), pts)

    def _render_segment_poly(self, surface: pygame.Surface, seg1: RoadSegment, seg2: RoadSegment):
        """Draw trapezoids for grass, rumble curbs, asphalt, and white lane dashes."""
        w = WINDOW_WIDTH
        y1, y2 = seg1.screen_y, seg2.screen_y
        x1, x2 = seg1.screen_x, seg2.screen_x
        w1, w2 = seg1.screen_w, seg2.screen_w

        rumble_w1 = w1 * 0.15
        rumble_w2 = w2 * 0.15

        colors = seg1.color

        # 1. Grass (entire background width)
        pygame.draw.polygon(surface, colors["grass"], [(0, y1), (w, y1), (w, y2), (0, y2)])

        # 2. Rumble Strips (curbs)
        pygame.draw.polygon(surface, colors["rumble"], [
            (x1 - w1 - rumble_w1, y1), (x1 - w1, y1),
            (x2 - w2, y2), (x2 - w2 - rumble_w2, y2)
        ])
        pygame.draw.polygon(surface, colors["rumble"], [
            (x1 + w1, y1), (x1 + w1 + rumble_w1, y1),
            (x2 + w2 + rumble_w2, y2), (x2 + w2, y2)
        ])

        # 3. Road Surface (asphalt)
        pygame.draw.polygon(surface, colors["road"], [
            (x1 - w1, y1), (x1 + w1, y1),
            (x2 + w2, y2), (x2 - w2, y2)
        ])

        # 4. White Lane Divider Dashes (if light segment)
        if not seg1.is_dark:
            lane_w1 = w1 * 0.03
            lane_w2 = w2 * 0.03
            for lane in range(1, LANES):
                lane_offset = (lane / LANES) * 2 - 1  # -0.33, +0.33 for 3 lanes
                lx1 = x1 + w1 * lane_offset
                lx2 = x2 + w2 * lane_offset
                pygame.draw.polygon(surface, colors["lane"], [
                    (lx1 - lane_w1, y1), (lx1 + lane_w1, y1),
                    (lx2 + lane_w2, y2), (lx2 - lane_w2, y2)
                ])

    def _render_sprite(self, surface: pygame.Surface, seg: RoadSegment, sprite: Dict[str, Any]):
        """Render a scaled roadside decoration (tree, streetlight, sign)."""
        offset = sprite["offset"]
        sprite_type = sprite["type"]

        # Calculate screen x for sprite
        sprite_x = seg.screen_x + (seg.screen_w * offset)
        sprite_y = seg.screen_y

        scale = seg.scale * 1600.0
        if scale < 2.0 or scale > 300.0:
            return

        if sprite_type == "tree":
            # Palm/Pine tree: trunk + lush foliage
            trunk_w = max(2, int(scale * 0.12))
            trunk_h = max(6, int(scale * 0.8))
            foliage_r = max(4, int(scale * 0.45))

            # Trunk
            pygame.draw.rect(surface, (80, 50, 30), (sprite_x - trunk_w // 2, sprite_y - trunk_h, trunk_w, trunk_h))
            # Foliage layers
            foliage_color = sprite.get("color", (35, 160, 65))
            pygame.draw.circle(surface, foliage_color, (int(sprite_x), int(sprite_y - trunk_h)), foliage_r)
            pygame.draw.circle(surface, (50, 200, 90), (int(sprite_x), int(sprite_y - trunk_h - foliage_r * 0.4)), int(foliage_r * 0.75))

        elif sprite_type == "lamp":
            # Cyber streetlight pole with neon light bulb
            pole_w = max(2, int(scale * 0.06))
            pole_h = max(8, int(scale * 1.0))
            pygame.draw.rect(surface, (140, 150, 170), (sprite_x - pole_w // 2, sprite_y - pole_h, pole_w, pole_h))
            # Neon lamp head
            bulb_r = max(3, int(scale * 0.15))
            lamp_color = (0, 240, 255)
            pygame.draw.circle(surface, lamp_color, (int(sprite_x), int(sprite_y - pole_h)), bulb_r)

        elif sprite_type == "billboard":
            # Sponsor racing billboard
            bb_w = max(10, int(scale * 0.9))
            bb_h = max(6, int(scale * 0.5))
            pole_h = max(4, int(scale * 0.35))
            # Stand
            pygame.draw.rect(surface, (100, 105, 115), (sprite_x - 3, sprite_y - pole_h, 6, pole_h))
            # Board
            rect = pygame.Rect(sprite_x - bb_w // 2, sprite_y - pole_h - bb_h, bb_w, bb_h)
            pygame.draw.rect(surface, (20, 24, 38), rect)
            pygame.draw.rect(surface, (0, 240, 255), rect, width=max(1, int(scale * 0.04)))
