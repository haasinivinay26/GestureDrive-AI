"""
Race Results and Score Recap Screen for GestureDrive AI.
Celebrates new high score records, summarizes performance metrics,
and offers one-click quick restart for college expo demonstrations.
"""

import pygame
from typing import Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from game.scoring import ScoringSystem
from ui.components import UIButton
from utils.helpers import draw_rounded_rect, draw_glow_rect, render_text_with_shadow


class ResultsScreen:
    """Displays final race statistics and restart options."""

    def __init__(self, on_restart: Callable[[], None], on_menu: Callable[[], None]):
        self.on_restart = on_restart
        self.on_menu = on_menu

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 64)
        self.font_record = pygame.font.SysFont("Verdana", 20, bold=True)
        self.font_score_val = pygame.font.SysFont("Impact", 72)
        self.font_label = pygame.font.SysFont("Verdana", 14)
        self.font_val = pygame.font.SysFont("Verdana", 24, bold=True)
        self.font_btn = pygame.font.SysFont("Verdana", 18, bold=True)

        # Buttons
        btn_w, btn_h = 240, 52
        cx = WINDOW_WIDTH // 2
        self.btn_again = UIButton(pygame.Rect(cx - btn_w - 20, WINDOW_HEIGHT - 90, btn_w, btn_h), "RACE AGAIN", self.font_btn, self.on_restart, primary=True)
        self.btn_menu = UIButton(pygame.Rect(cx + 20, WINDOW_HEIGHT - 90, btn_w, btn_h), "MAIN MENU", self.font_btn, self.on_menu)

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
        mouse_pos = pygame.mouse.get_pos()
        self.btn_again.update(dt, mouse_pos)
        self.btn_menu.update(dt, mouse_pos)

    def draw(self, surface: pygame.Surface, scoring: ScoringSystem, top_speed: float):
        surface.fill((14, 16, 24))

        # Title
        title_surf = render_text_with_shadow(self.font_title, "RACE COMPLETE", COLOR_NEON_CYAN, (0, 0, 0), (3, 3))
        surface.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, 45))

        # New High Score Celebration Banner
        if scoring.is_new_high_score:
            rec_surf = render_text_with_shadow(self.font_record, "★ NEW HIGH SCORE RECORD! ★", COLOR_NEON_AMBER, (0, 0, 0), (2, 2))
            surface.blit(rec_surf, (WINDOW_WIDTH // 2 - rec_surf.get_width() // 2, 125))

        # Main Score Display Card
        card_w, card_h = 560, 130
        card_x = WINDOW_WIDTH // 2 - card_w // 2
        card_y = 165
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        draw_glow_rect(surface, card_rect, (20, 24, 36), COLOR_NEON_GREEN, radius=10, glow_spread=3)

        lbl_score = self.font_label.render("FINAL RACE SCORE", True, COLOR_TEXT_MUTED)
        surface.blit(lbl_score, (WINDOW_WIDTH // 2 - lbl_score.get_width() // 2, card_y + 16))

        val_score = self.font_score_val.render(f"{scoring.score:,}", True, COLOR_NEON_GREEN)
        surface.blit(val_score, (WINDOW_WIDTH // 2 - val_score.get_width() // 2, card_y + 38))

        # Stats Grid (2x2)
        grid_y = card_y + card_h + 30
        cell_w, cell_h = 265, 80

        stats = [
            ("TOTAL DISTANCE", scoring.get_formatted_distance(), card_x, grid_y, COLOR_TEXT_WHITE),
            ("RACE TIME", scoring.get_formatted_time(), card_x + cell_w + 30, grid_y, COLOR_NEON_CYAN),
            ("TOP SPEED", f"{int(top_speed)} KM/H", card_x, grid_y + cell_h + 15, COLOR_NEON_AMBER),
            ("NEAR MISSES DODGED", f"{scoring.near_misses}", card_x + cell_w + 30, grid_y + cell_h + 15, COLOR_NEON_GREEN),
        ]

        for label, val, x, y, color in stats:
            rect = pygame.Rect(x, y, cell_w, cell_h)
            draw_rounded_rect(surface, rect, (20, 24, 36), radius=8, border_color=COLOR_PANEL_BORDER, border_width=1)
            l_s = self.font_label.render(label, True, COLOR_TEXT_MUTED)
            surface.blit(l_s, (x + 18, y + 14))
            v_s = self.font_val.render(val, True, color)
            surface.blit(v_s, (x + 18, y + 36))

        # Buttons
        self.btn_again.draw(surface)
        self.btn_menu.draw(surface)
