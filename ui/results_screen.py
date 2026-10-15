"""
Race Results and Score Recap Screen for GestureDrive AI.
Celebrates new high score records, summarizes performance metrics,
and offers one-click quick restart for college expo demonstrations.
"""

import math
import pygame
from typing import Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from game.scoring import ScoringSystem
from ui.components import UIButton
from utils.helpers import draw_rounded_rect, draw_glow_rect, draw_glass_rect, render_text_with_shadow


class ResultsScreen:
    """Displays final race statistics, rank grading, and restart options."""

    def __init__(self, on_restart: Callable[[], None], on_menu: Callable[[], None]):
        self.on_restart = on_restart
        self.on_menu = on_menu
        self.anim_timer = 0.0

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 58)
        self.font_record = pygame.font.SysFont("Verdana", 18, bold=True)
        self.font_score_val = pygame.font.SysFont("Impact", 68)
        self.font_label = pygame.font.SysFont("Verdana", 12, bold=True)
        self.font_val = pygame.font.SysFont("Verdana", 22, bold=True)
        self.font_btn = pygame.font.SysFont("Verdana", 16, bold=True)
        self.font_rank = pygame.font.SysFont("Impact", 42)

        # Buttons
        btn_w, btn_h = 240, 50
        cx = WINDOW_WIDTH // 2
        btn_y = WINDOW_HEIGHT - 85

        self.btn_again = UIButton(
            pygame.Rect(cx - btn_w - 20, btn_y, btn_w, btn_h),
            "PLAY AGAIN", self.font_btn, self.on_restart,
            primary=True, accent_color=COLOR_NEON_GREEN, shortcut="[SPACE]"
        )
        self.btn_menu = UIButton(
            pygame.Rect(cx + 20, btn_y, btn_w, btn_h),
            "MAIN MENU", self.font_btn, self.on_menu,
            shortcut="[ESC]"
        )

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                self.on_restart()
                return
            elif event.key == pygame.K_ESCAPE:
                self.on_menu()
                return

        self.btn_again.handle_event(event)
        self.btn_menu.handle_event(event)

    def update(self, dt: float):
        self.anim_timer += dt
        mouse_pos = pygame.mouse.get_pos()
        self.btn_again.update(dt, mouse_pos)
        self.btn_menu.update(dt, mouse_pos)

    def draw(self, surface: pygame.Surface, scoring: ScoringSystem, top_speed: float):
        surface.fill((8, 10, 16))

        # Title
        title_surf = render_text_with_shadow(self.font_title, "RACE TELEMETRY SUMMARY", COLOR_NEON_CYAN, (0, 0, 0), (3, 3))
        surface.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, 35))

        # New High Score Celebration Banner
        if scoring.is_new_high_score:
            pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 4.0)
            star_color = (int(255 * (0.8 + 0.2 * pulse)), int(180 * (0.8 + 0.2 * pulse)), 30)
            rec_surf = render_text_with_shadow(self.font_record, "★ NEW EXPO HIGH SCORE RECORD! ★", star_color, (0, 0, 0), (2, 2))
            surface.blit(rec_surf, (WINDOW_WIDTH // 2 - rec_surf.get_width() // 2, 105))

        # Main Score Card (Center)
        card_w, card_h = 580, 125
        card_x = WINDOW_WIDTH // 2 - card_w // 2
        card_y = 145
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        draw_glass_rect(surface, card_rect, bg_rgba=(16, 22, 36, 230), border_color=COLOR_NEON_GREEN, radius=12, border_width=2)

        lbl_score = self.font_label.render("FINAL RACE SCORE", True, COLOR_TEXT_MUTED)
        surface.blit(lbl_score, (WINDOW_WIDTH // 2 - lbl_score.get_width() // 2, card_y + 14))

        val_score = self.font_score_val.render(f"{scoring.score:,}", True, COLOR_NEON_GREEN)
        surface.blit(val_score, (WINDOW_WIDTH // 2 - val_score.get_width() // 2, card_y + 36))

        # Performance Rank Calculation
        if scoring.score >= 5000:
            rank_str, rank_color = "S - LEGENDARY", COLOR_NEON_AMBER
        elif scoring.score >= 2500:
            rank_str, rank_color = "A - EXPERT", COLOR_NEON_CYAN
        elif scoring.score >= 1000:
            rank_str, rank_color = "B - SKILLED", COLOR_NEON_GREEN
        else:
            rank_str, rank_color = "C - ROOKIE", COLOR_TEXT_MUTED

        # Telemetry Grid (2 rows x 3 columns)
        grid_y = card_y + card_h + 24
        cell_w, cell_h = 240, 78
        gap_x = 20
        gap_y = 15
        total_grid_w = cell_w * 3 + gap_x * 2
        grid_start_x = WINDOW_WIDTH // 2 - total_grid_w // 2

        stats = [
            ("TOTAL DISTANCE", scoring.get_formatted_distance(), COLOR_TEXT_WHITE),
            ("RACE TIME", scoring.get_formatted_time(), COLOR_NEON_CYAN),
            ("TOP SPEED", f"{int(top_speed)} KM/H", COLOR_NEON_AMBER),
            ("OBSTACLES PASSED", f"{scoring.near_misses} DODGED", COLOR_NEON_GREEN),
            ("MAX MULTIPLIER", f"{scoring.speed_multiplier:.1f}x", COLOR_NEON_CYAN),
            ("DRIVER RATING", rank_str, rank_color),
        ]

        for i, (label, val, color) in enumerate(stats):
            col = i % 3
            row = i // 3
            cx = grid_start_x + col * (cell_w + gap_x)
            cy = grid_y + row * (cell_h + gap_y)

            rect = pygame.Rect(cx, cy, cell_w, cell_h)
            draw_glass_rect(surface, rect, bg_rgba=(16, 20, 32, 220), border_color=(35, 48, 70), radius=8)

            l_s = self.font_label.render(label, True, COLOR_TEXT_MUTED)
            surface.blit(l_s, (cx + 16, cy + 12))

            v_s = self.font_val.render(val, True, color)
            surface.blit(v_s, (cx + 16, cy + 34))

        # Buttons
        self.btn_again.draw(surface)
        self.btn_menu.draw(surface)
