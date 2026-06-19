#!/usr/bin/env python3
# drDOOM69GAMING
# File: main.pyc (Python 3.10)

import pygame
import random
import sys
import os
import math
import json
import glob
import tkinter as tk
from tkinter import filedialog
import copy

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(path):
    return os.path.join(BASE_DIR, path)

pygame.init()
pygame.mixer.set_num_channels(32)
pygame.mixer.init()
GAME_CAPTION = 'TetraFusion 2.1 - by drDOOM69GAMING'
last_track_index = None
MUSIC_END_EVENT = pygame.USEREVENT + 1
custom_music_playlist = []
current_track_index = 0
AUDIO_EXTENSIONS = {
    '.wma',
    '.wav',
    '.ogg',
    '.mp3',
    '.aac',
    '.flac',
    '.m4a'}

def load_sound(file_path):
    '''Attempt to load a sound file; if missing, print a warning and return None.'''
    if os.path.exists(file_path):
        try:
            return pygame.mixer.Sound(file_path)
        except Exception as e:
            print(f'Error loading sound {file_path}: {e}')
            return None
    print(f'Sound file not found: {file_path}')
    return None


_fullscreen = False


def toggle_fullscreen():
    global _fullscreen, screen
    _fullscreen = not _fullscreen
    if _fullscreen:
        screen = pygame.display.set_mode((SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    else:
        screen = pygame.display.set_mode((SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT))


def fade_transition(duration=300):
    capture = screen.copy()
    overlay = pygame.Surface((SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    start = pygame.time.get_ticks()
    while True:
        elapsed = pygame.time.get_ticks() - start
        progress = min(1.0, elapsed / duration)
        alpha = int(255 * progress)
        screen.blit(capture, (0, 0))
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        if progress >= 1.0:
            break


def get_music_files(directory):
    music_files = []
    try:
        items = os.listdir(directory)
    except Exception as e:
        print(f'Error reading directory {directory}: {e}')
        return []

    files = []
    for item in items:
        if item.startswith('.'):
            continue
        full_path = os.path.join(directory, item)
        if os.path.isfile(full_path):
            files.append(item)

    def sort_key(name):
        first_char = name[0]
        if first_char.isdigit():
            cat = 0
        elif 'A' <= first_char.upper() <= 'Z':
            cat = 1
        else:
            cat = 2
        return (cat, name.upper())

    files.sort(key=sort_key)

    for file in files:
        full_path = os.path.join(directory, file)
        ext = os.path.splitext(full_path)[1].lower()
        if ext in AUDIO_EXTENSIONS:
            music_files.append(full_path)

    if len(music_files) > 500:
        print(f'Found {len(music_files)} audio files; limiting to 500.')
        music_files = music_files[:500]

    return music_files


def update_custom_music_playlist(settings):
    '''Updates the custom music playlist based on user settings.'''
    global custom_music_playlist, current_track_index
    if not settings.get('use_custom_music', False):
        custom_music_playlist = [BACKGROUND_MUSIC_PATH]
        current_track_index = 0
        return None
    music_directory = settings['music_directory'].strip()
    if not os.path.isdir(music_directory):
        print('Invalid music directory; defaulting to default background music.')
        settings['music_directory'] = ''
        save_settings(settings)
        custom_music_playlist = [BACKGROUND_MUSIC_PATH]
        current_track_index = 0
        return None
    playlist = get_music_files(music_directory)
    if not playlist:
        print('No playable audio files found; defaulting to background music.')
        playlist = [BACKGROUND_MUSIC_PATH]
    custom_music_playlist = playlist
    current_track_index = 0
    return None


if sys.platform == 'darwin':
    try:
        from AppKit import NSOpenPanel, NSApplication
    except ImportError:
        NSOpenPanel = None

    def select_music_directory():
        if NSOpenPanel is None:
            root = tk.Tk()
            root.withdraw()
            selected = filedialog.askdirectory()
            root.destroy()
            return selected
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(False)
        panel.setCanChooseDirectories_(True)
        panel.setAllowsMultipleSelection_(False)
        result = panel.runModal()
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        if result == 1:
            return panel.URL().path()

else:

    def select_music_directory():
        global screen
        pygame.display.quit()
        try:
            import subprocess
            result = subprocess.run(
                ['zenity', '--file-selection', '--directory', '--title=Select Music Folder'],
                capture_output=True, text=True, timeout=30
            )
            selected = result.stdout.strip() if result.returncode == 0 else None
        except Exception as e:
            print(f'zenity dialog failed: {e}')
            selected = None
        w, h = SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT
        flags = pygame.FULLSCREEN | pygame.SCALED if _fullscreen else 0
        screen = pygame.display.set_mode((w, h), flags)
        return selected

SCREEN_WIDTH = 450
SCREEN_HEIGHT = 930
BLOCK_SIZE = 30
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE
SUBWINDOW_WIDTH = 369
DOUBLE_CLICK_TIME = 300
LOCK_DELAY_TIME = 500
MAX_LOCK_DELAY_RESETS = 15
CLEAR_ANIM_DURATION = 400
GAME_OVER_ANIM_DURATION = 1200
hold_piece = None
hold_used = False
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
COLORS = [
    (0, 230, 230),
    (255, 150, 0),
    (30, 70, 255),
    (230, 25, 25),
    (0, 200, 50),
    (235, 215, 0),
    (170, 30, 180)]

THEMES = [
    {'name': 'Default', 'colors': [(0, 230, 230), (255, 150, 0), (30, 70, 255), (230, 25, 25), (0, 200, 50), (235, 215, 0), (170, 30, 180)], 'grid': [200, 200, 200]},
    {'name': 'Retro', 'colors': [(0, 240, 240), (240, 160, 0), (0, 0, 240), (240, 0, 0), (0, 240, 0), (240, 240, 0), (160, 0, 240)], 'grid': [100, 100, 100]},
    {'name': 'Dark', 'colors': [(0, 200, 200), (200, 100, 0), (80, 80, 255), (200, 0, 0), (0, 200, 0), (200, 200, 0), (160, 0, 160)], 'grid': [50, 50, 50]},
    {'name': 'Pastel', 'colors': [(150, 255, 255), (255, 210, 150), (150, 150, 255), (255, 150, 150), (150, 255, 150), (255, 255, 150), (210, 150, 210)], 'grid': [200, 200, 255]},
    {'name': 'Protanopia', 'colors': [(0, 200, 200), (200, 160, 0), (0, 100, 255), (200, 100, 100), (100, 200, 0), (255, 255, 0), (150, 0, 150)], 'grid': [200, 200, 200]},
    {'name': 'Deuteranopia', 'colors': [(0, 180, 180), (200, 150, 0), (0, 80, 200), (200, 80, 80), (80, 200, 0), (230, 230, 0), (130, 0, 130)], 'grid': [200, 200, 200]},
    {'name': 'Tritanopia', 'colors': [(0, 200, 150), (200, 120, 80), (0, 60, 180), (220, 60, 60), (60, 200, 80), (255, 220, 0), (180, 0, 120)], 'grid': [200, 200, 200]},
]

def apply_theme(theme_index):
    theme = THEMES[theme_index % len(THEMES)]
    for i in range(len(COLORS)):
        COLORS[i] = theme['colors'][i]
    return tuple(theme['grid'])

AUDIO_FOLDER = resource_path('Audio')
BACKGROUND_MUSIC_PATH = os.path.join(AUDIO_FOLDER, 'Background.ogg')
LINE_CLEAR_SOUND_PATH = os.path.join(AUDIO_FOLDER, 'Lineclear.ogg')
MULTIPLE_LINE_CLEAR_SOUND_PATH = os.path.join(AUDIO_FOLDER, 'MultipleLineclear.ogg')
GAME_OVER_SOUND_PATH = os.path.join(AUDIO_FOLDER, 'GAMEOVER.ogg')
HEARTBEAT_SOUND_PATH = os.path.join(AUDIO_FOLDER, 'heartbeat_grid_almost_full.ogg')
line_clear_sound = load_sound(LINE_CLEAR_SOUND_PATH)
multiple_line_clear_sound = load_sound(MULTIPLE_LINE_CLEAR_SOUND_PATH)
game_over_sound = load_sound(GAME_OVER_SOUND_PATH)
heartbeat_sound = load_sound(HEARTBEAT_SOUND_PATH)
heartbeat_playing = False
SHAPES = [
    [
        [1, 1, 1],
        [0, 1, 0]],
    [
        [1, 1],
        [1, 1]],
    [
        [1, 1, 0],
        [0, 1, 1]],
    [
        [0, 1, 1],
        [1, 1, 0]],
    [
        [1, 1, 1, 1]],
    [
        [1, 0, 0],
        [1, 1, 1]],
    [
        [0, 0, 1],
        [1, 1, 1]]]

# SRS wall kick data - (from_state, to_state) -> list of (dx, dy) tests
# y+ = down, matching the game's coordinate system
JLSTZ_KICKS = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}

I_KICKS = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
}

def rotate_matrix(matrix):
    '''Rotates a matrix (list of lists) 90 clockwise.'''
    return [list(row) for row in zip(*matrix[::-1])]


def get_shape_index(tetromino):
    '''
    Returns the index of the given tetromino shape in the SHAPES list.
    Checks all four rotations to find a match.
    If no match is found, prints an error and returns None.
    '''
    for index, shape in enumerate(SHAPES):
        candidate = tetromino
        for _ in range(4):
            if candidate == shape:
                return index
            candidate = rotate_matrix(candidate)
    print('Error: Tetromino shape not found in SHAPES list.')

TETRIS_FONT_PATH = resource_path('assets/tetris-blocks.TTF')

try:
    tetris_font_large = pygame.font.Font(TETRIS_FONT_PATH, 40)
    tetris_font_medium = pygame.font.Font(TETRIS_FONT_PATH, 27)
    tetris_font_small = pygame.font.Font(TETRIS_FONT_PATH, 18)
    tetris_font_smaller = pygame.font.Font(TETRIS_FONT_PATH, 16)
    tetris_font_tiny = pygame.font.Font(TETRIS_FONT_PATH, 14)
except FileNotFoundError:
    print(f'Font file not found: {TETRIS_FONT_PATH}')
    sys.exit()
screen = pygame.display.set_mode((SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT))
_fullscreen = False
pygame.display.set_caption(GAME_CAPTION)
clock = pygame.time.Clock()
subwindow_visible = True
last_click_time = 0
restart_button_rect = None
menu_button_rect = None
skip_button_rect = None
sound_bar_rect = None
game_command = None

import os
import json
import pygame
import os
import json
import pygame


def data_path(filename):
    if getattr(sys, 'frozen', False):
        d = os.path.join(os.path.expanduser('~'), '.tetrafusion')
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, filename)
    return os.path.join(BASE_DIR, filename)

def load_settings(filename='settings.json'):
    '''Loads game settings from a JSON file, ensuring all required keys exist.'''
    path = data_path(filename)
    default_settings = {
        'controls': {
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'down': pygame.K_DOWN,
            'rotate': pygame.K_UP,
            'pause': pygame.K_p,
            'hard_drop': pygame.K_SPACE,
            'hold': pygame.K_c,
            'skip_track': pygame.K_x,
        },
        'controller_controls': {
            'left': 14,
            'right': 15,
            'down': 13,
            'rotate': 0,
            'hard_drop': 1,
            'hold': 2,
            'pause': 3,
            'skip_track': 4,
        },
        'controller_menu_navigation': {
            'up': 11,
            'down': 12,
            'select': 0,
            'back': 1,
        },
        'controller_settings': {
            'analog_threshold': 0.5,
            'joy_delay': 150,
            'hat_threshold': 0.5,
        },
        'difficulty': 'normal',
        'flame_trails': True,
        'effect': 'flame',
        'grid_color': [200, 200, 200],
        'grid_opacity': 255,
        'grid_lines': True,
        'ghost_piece': True,
        'ghost_opacity': 80,
        'screen_shake': True,
        'particle_density': 'medium',
        'das': 150,
        'arr': 50,
        'background': 'none',
        'music_enabled': True,
        'use_custom_music': False,
        'music_directory': '',
        'theme': 0,
        'gravity_multiplier': 1.0,
    }
    if not os.path.exists(path):
        save_settings(default_settings, filename)
        return default_settings
    try:
        with open(path, 'r') as file:
            saved_settings = json.load(file)
    except (json.JSONDecodeError, KeyError) as e:
        print(f'Error loading settings ({e}), using defaults.')
        return default_settings
    saved_settings.setdefault('controls', {})
    saved_settings.setdefault('controller_controls', default_settings['controller_controls'])
    saved_settings.setdefault('controller_menu_navigation', default_settings['controller_menu_navigation'])
    saved_settings.setdefault('controller_settings', default_settings['controller_settings'])
    for key, default_val in default_settings['controller_controls'].items():
        if saved_settings['controller_controls'].get(key) is None:
            saved_settings['controller_controls'][key] = default_val
    for key, default_val in default_settings['controller_menu_navigation'].items():
        if saved_settings['controller_menu_navigation'].get(key) is None:
            saved_settings['controller_menu_navigation'][key] = default_val
    for key, default_val in default_settings['controller_settings'].items():
        if saved_settings['controller_settings'].get(key) is None:
            saved_settings['controller_settings'][key] = default_val
    for key, default_value in default_settings['controls'].items():
        if key in saved_settings['controls']:
            val = saved_settings['controls'][key]
            if isinstance(val, str):
                try:
                    saved_settings['controls'][key] = pygame.key.key_code(val.lower())
                except KeyError:
                    print(f"Warning: Unrecognized key '{val}' in settings. Resetting to default.")
                    saved_settings['controls'][key] = default_value
            elif not isinstance(val, int):
                saved_settings['controls'][key] = default_value
        else:
            saved_settings['controls'][key] = default_value
    for key, default_value in default_settings.items():
        if key not in saved_settings:
            saved_settings[key] = default_value
    return saved_settings


def save_settings(settings, filename='settings.json'):
    '''Saves the game settings to a JSON file.'''
    path = data_path(filename)
    try:
        settings_to_save = {
            'controls': {control: pygame.key.name(key).upper() for control, key in settings['controls'].items()},
            'controller_controls': {control: settings['controller_controls'].get(control) for control in settings.get('controller_controls', {})},
            'controller_menu_navigation': {control: settings['controller_menu_navigation'].get(control) for control in settings.get('controller_menu_navigation', {})},
            'controller_settings': settings.get('controller_settings', {}),
            'difficulty': settings.get('difficulty', 'normal'),
            'flame_trails': settings.get('flame_trails', True),
            'effect': settings.get('effect', 'flame'),
            'grid_color': settings.get('grid_color', [200, 200, 200]),
            'grid_opacity': settings.get('grid_opacity', 255),
            'grid_lines': settings.get('grid_lines', True),
            'ghost_piece': settings.get('ghost_piece', True),
            'ghost_opacity': settings.get('ghost_opacity', 80),
            'screen_shake': settings.get('screen_shake', True),
            'particle_density': settings.get('particle_density', 'medium'),
            'das': settings.get('das', 150),
            'arr': settings.get('arr', 50),
            'background': settings.get('background', 'none'),
            'music_enabled': settings.get('music_enabled', True),
            'use_custom_music': settings.get('use_custom_music', False),
            'music_directory': settings.get('music_directory', ''),
            'theme': settings.get('theme', 0),
            'gravity_multiplier': settings.get('gravity_multiplier', 1.0),
        }
        with open(path, 'w') as file:
            json.dump(settings_to_save, file, indent=4)
    except Exception as e:
        print(f'Error saving settings: {e}')


class DustParticle:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = random.uniform(math.pi, math.pi * 2)
        self.speed = random.uniform(1, 3)
        self.age = 0
        self.max_age = random.randint(20, 40)
        self.size = random.randint(8, 15)
        self.color = (random.randint(100, 150), random.randint(50, 100), 0)
        self.alpha = 255

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.speed *= 0.92
        self.age += 1
        self.alpha = max(0, 255 - (self.age / self.max_age) * 255)
        self.size = max(2, self.size * 0.95)

    def draw(self, screen):
        if self.age >= self.max_age:
            return None
        surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color_with_alpha = list(self.color)
        color_with_alpha.append(int(self.alpha))
        pygame.draw.circle(surface, tuple(color_with_alpha), (int(self.size), int(self.size)), int(self.size))
        screen.blit(surface, (int(self.x - self.size), int(self.y - self.size)))


class TrailParticle:

    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        if direction == 'left':
            self.angle = random.uniform(math.pi / 2, 3 * math.pi / 2)
        elif direction == 'right':
            self.angle = random.uniform(-(math.pi) / 2, math.pi / 2)
        elif direction == 'down':
            self.angle = random.uniform(math.pi / 2 - math.pi / 8, math.pi / 2 + math.pi / 8)
        else:
            self.angle = random.uniform(-(math.pi), math.pi)
        self.speed = random.uniform(1.5, 3)
        self.age = 0
        self.max_age = random.randint(40, 60)
        self.size = random.randint(12, 20)
        self.colors = [
            (255, 240, 150),
            (255, 180, 80),
            (255, 90, 40)]
        self.turbulence = random.uniform(0.5, 1.5)
        self.gravity = -0.1
        self.drift_x = random.uniform(-0.5, 0.5)
        self.drift_y = random.uniform(-0.5, 0.5)

    def update(self, wind_force, screen=None):
        self.x += math.cos(self.angle) * self.speed + self.drift_x + wind_force[0]
        self.y += math.sin(self.angle) * self.speed + self.drift_y + wind_force[1]
        if screen:
            self.x = max(self.size, min(screen.get_width() - self.size, self.x))
            self.y = max(self.size, min(screen.get_height() - self.size, self.y))
        self.speed *= 0.92
        self.drift_x *= 0.7
        self.drift_y *= 0.7
        self.y += self.gravity
        self.age += 1
        self.size = max(5, self.size * 0.95)

    def draw(self, screen):
        if self.age >= self.max_age:
            return None
        if not (0 <= self.x <= screen.get_width()):
            return None
        if not (0 <= self.y <= screen.get_height()):
            return None
        color_progress = self.age / self.max_age
        if color_progress < 0.33:
            color = self.colors[0]
        elif color_progress < 0.66:
            color = self.colors[1]
        else:
            color = self.colors[2]
        alpha = int(255 * (1 - color_progress ** 1.5))
        radius = int(self.size)
        blended_color = (color[0], color[1], color[2], alpha)
        particle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, blended_color, (radius, radius), radius)
        screen.blit(particle_surface, (int(self.x - radius), int(self.y - radius)))


class WindParticle:

    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        if direction == 'left':
            self.vx = random.uniform(-5, -2)
            self.vy = random.uniform(-1, 1)
        elif direction == 'right':
            self.vx = random.uniform(2, 5)
            self.vy = random.uniform(-1, 1)
        else:
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(2, 5)
        self.age = 0
        self.max_age = random.randint(15, 25)
        self.size = random.uniform(1, 3)
        self.alpha = 255

    def update(self, wind_force, screen=None):
        self.x += self.vx + wind_force[0]
        self.y += self.vy + wind_force[1]
        self.age += 1
        self.alpha = max(0, 255 - (self.age / self.max_age) * 255)

    def draw(self, screen):
        if self.age >= self.max_age:
            return None
        if not (0 <= self.x <= screen.get_width()) or not (0 <= self.y <= screen.get_height()):
            return None
        alpha = int(self.alpha)
        length = int(8 + self.age * 0.5)
        color = (200, 220, 255, alpha)
        end_x = int(self.x - self.vx * length)
        end_y = int(self.y - self.vy * length)
        line_surf = pygame.Surface((abs(end_x - int(self.x)) + 4, abs(end_y - int(self.y)) + 4), pygame.SRCALPHA)
        pygame.draw.line(line_surf, color, (2, 2), (abs(end_x - int(self.x)) + 2, abs(end_y - int(self.y)) + 2), max(1, int(self.size)))
        screen.blit(line_surf, (min(int(self.x), end_x) - 2, min(int(self.y), end_y) - 2))


class WaterParticle:

    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        if direction == 'down':
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-1, 3)
        elif direction == 'left':
            self.vx = random.uniform(-3, 0)
            self.vy = random.uniform(-1, 1)
        elif direction == 'right':
            self.vx = random.uniform(0, 3)
            self.vy = random.uniform(-1, 1)
        else:
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(1, 3)
        self.gravity = 0.15
        self.age = 0
        self.max_age = random.randint(30, 50)
        self.size = random.randint(3, 6)
        blue_shade = random.randint(150, 220)
        self.color = (50, 100, blue_shade)
        self.alpha = 200

    def update(self, wind_force, screen=None):
        self.x += self.vx + wind_force[0]
        self.vy += self.gravity
        self.y += self.vy + wind_force[1]
        self.age += 1
        self.alpha = max(0, 200 - int((self.age / self.max_age) * 200))
        self.size = max(1, self.size * 0.97)

    def draw(self, screen):
        if self.age >= self.max_age:
            return None
        if not (0 <= self.x <= screen.get_width()) or not (0 <= self.y <= screen.get_height()):
            return None
        alpha = int(self.alpha)
        r = int(self.size)
        surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        color = (*self.color, alpha)
        half = r * 2
        pygame.draw.ellipse(surf, color, (half - r, 1, r * 2, max(1, r * 3)))
        screen.blit(surf, (int(self.x - half), int(self.y - r * 1.5)))


class IceParticle:

    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        if direction == 'down':
            self.vy = abs(self.vy)
        elif direction == 'left':
            self.vx = -abs(self.vx)
        elif direction == 'right':
            self.vx = abs(self.vx)
        self.age = 0
        self.max_age = random.randint(25, 45)
        self.size = random.randint(2, 5)
        self.sparkle = random.uniform(0.5, 1.0)
        self.rotation = random.uniform(0, math.pi * 2)
        self.rot_speed = random.uniform(-0.1, 0.1)

    def update(self, wind_force, screen=None):
        self.x += self.vx * 0.8 + wind_force[0]
        self.y += self.vy * 0.8 + wind_force[1]
        self.vx *= 0.98
        self.vy *= 0.98
        self.age += 1
        self.rotation += self.rot_speed
        self.size = max(1, self.size * 0.98)

    def draw(self, screen):
        if self.age >= self.max_age:
            return None
        if not (0 <= self.x <= screen.get_width()) or not (0 <= self.y <= screen.get_height()):
            return None
        progress = self.age / self.max_age
        alpha = int(255 * (1 - progress))
        r = int(self.size)
        surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        cx = cy = r * 2
        white = (255, 255, 255, alpha)
        blue = (180, 220, 255, alpha)
        pygame.draw.polygon(surf, white, [
            (cx + math.cos(self.rotation) * r, cy + math.sin(self.rotation) * r),
            (cx + math.cos(self.rotation + 2.5) * r, cy + math.sin(self.rotation + 2.5) * r),
            (cx + math.cos(self.rotation + math.pi) * r * 0.4, cy + math.sin(self.rotation + math.pi) * r * 0.4),
            (cx + math.cos(self.rotation + 3.8) * r, cy + math.sin(self.rotation + 3.8) * r),
        ])
        if self.sparkle > 0.7:
            pygame.draw.circle(surf, (255, 255, 255, alpha), (cx, cy), max(1, r // 2))
        screen.blit(surf, (int(self.x - cx), int(self.y - cy)))


class FlickerParticle:

    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        if direction == 'down':
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(1, 4)
        elif direction == 'left':
            self.vx = random.uniform(-4, -1)
            self.vy = random.uniform(-2, 2)
        elif direction == 'right':
            self.vx = random.uniform(1, 4)
            self.vy = random.uniform(-2, 2)
        else:
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-3, 3)
        self.age = 0
        self.max_age = random.randint(8, 18)
        self.size = random.randint(6, 14)
        c = random.choice([(255, 255, 100), (255, 150, 50), (200, 200, 255)])
        self.color = c
        self.flash_interval = random.randint(2, 5)

    def update(self, wind_force, screen=None):
        self.x += self.vx * 0.9 + wind_force[0]
        self.y += self.vy * 0.9 + wind_force[1]
        self.age += 1
        self.size = max(2, self.size * 0.92)

    def draw(self, screen):
        if self.age >= self.max_age:
            return None
        if not (0 <= self.x <= screen.get_width()) or not (0 <= self.y <= screen.get_height()):
            return None
        visible = (self.age // self.flash_interval) % 2 == 0
        if not visible:
            return None
        progress = self.age / self.max_age
        alpha = int(255 * (1 - progress))
        r = int(self.size)
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        color = (*self.color, alpha)
        pygame.draw.circle(surf, color, (r, r), r)
        inner = (255, 255, 255, int(alpha * 0.7))
        pygame.draw.circle(surf, inner, (r, r), max(1, r // 2))
        screen.blit(surf, (int(self.x - r), int(self.y - r)))


class MatrixParticle:

    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        if direction == 'down':
            self.vy = random.uniform(2, 6)
            self.vx = random.uniform(-0.5, 0.5)
        elif direction == 'left':
            self.vx = random.uniform(-6, -2)
            self.vy = random.uniform(-0.5, 0.5)
        elif direction == 'right':
            self.vx = random.uniform(2, 6)
            self.vy = random.uniform(-0.5, 0.5)
        else:
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(2, 5)
        self.age = 0
        self.max_age = random.randint(15, 30)
        self.length = random.randint(6, 15)
        self.green = random.randint(150, 255)
        self.tail_color = (0, max(50, self.green // 3), 0)

    def update(self, wind_force, screen=None):
        self.x += self.vx + wind_force[0]
        self.y += self.vy + wind_force[1]
        self.age += 1

    def draw(self, screen):
        if self.age >= self.max_age:
            return None
        if not (0 <= self.x <= screen.get_width()) or not (0 <= self.y <= screen.get_height()):
            return None
        progress = self.age / self.max_age
        alpha = int(255 * (1 - progress ** 0.5))
        head_color = (0, self.green, 0, alpha)
        tail_color = (*self.tail_color, int(alpha * 0.4))
        length = self.length
        head_surf = pygame.Surface((4, length), pygame.SRCALPHA)
        for i in range(length):
            t = i / length
            c = (
                int(head_color[0] * (1 - t) + tail_color[0] * t),
                int(head_color[1] * (1 - t) + tail_color[1] * t),
                int(head_color[2] * (1 - t) + tail_color[2] * t),
                int(head_color[3] * (1 - t) + tail_color[3] * t),
            )
            head_surf.set_at((1, i), c)
        screen.blit(head_surf, (int(self.x - 1), int(self.y - length)))


class Explosion:

    def __init__(self, x, y, color, particle_count, max_speed, duration=30):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []
        self.lifetime = duration
        for _ in range(particle_count):
            self.particles.append([
                x + random.uniform(-15, 15),
                y + random.uniform(-15, 15),
                random.uniform(-max_speed, max_speed),
                random.uniform(-max_speed, max_speed),
                random.uniform(0.1, 0.3),
                random.randint(200, 255)])

    def update(self):
        self.lifetime -= 1
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[4]
            p[5] = max(0, p[5] - 4)

    def draw(self, surface, offset=(0, 0)):
        for p in self.particles:
            if p[5] > 0:
                size = 4 + int(p[5] / 50)
                pygame.draw.circle(surface, self.color, (int(p[0] + offset[0]), int(p[1] + offset[1])), size)


joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()


class TetrominoBag:

    def __init__(self, shapes):
        self.shapes = shapes
        self.bag = []
        self.refill_bag()

    def refill_bag(self):
        self.bag = self.shapes[:]
        random.shuffle(self.bag)

    def get_next_tetromino(self):
        if not self.bag:
            self.refill_bag()
        return self.bag.pop()


def level_tint(color, level):
    t = level * 0.25
    dr = int(12 * math.sin(t))
    dg = int(8 * math.sin(t + 2.094))
    db = int(10 * math.sin(t + 4.189))
    return (max(0, min(255, color[0] + dr)), max(0, min(255, color[1] + dg)), max(0, min(255, color[2] + db)))

def draw_evil_face(screen, cx, cy, pulse=1.0):
    face_data = [
        "  XXXXXX  ",
        " X      X ",
        "X  X  X  X",
        "X        X",
        "X  XX  X  X",
        " X  XX  X ",
        "  XXXXXX  ",
    ]
    px = 6
    w = len(face_data[0]) * px
    h = len(face_data) * px
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    alpha = int(180 * pulse)
    green = (0, 255, 100, alpha)
    glow = (0, 255, 100, int(40 * pulse))
    for row_idx, row in enumerate(face_data):
        for col_idx, ch in enumerate(row):
            if ch == 'X':
                rect = pygame.Rect(col_idx * px, row_idx * px, px, px)
                pygame.draw.rect(surf, glow, rect.inflate(4, 4), 2)
                pygame.draw.rect(surf, green, rect)
                pygame.draw.rect(surf, green, rect, 1)
    screen.blit(surf, (cx - w // 2, cy - h // 2))

_gloss_cache = {}

def _get_gloss(block_size):
    if block_size not in _gloss_cache:
        gloss = pygame.Surface((block_size, block_size), pygame.SRCALPHA)
        cx, cy = block_size // 3, block_size // 3
        for rad in range(block_size // 3, 0, -2):
            alpha = max(0, 45 - rad * 6)
            if alpha > 0:
                pygame.draw.circle(gloss, (255, 255, 255, alpha), (cx, cy), rad)
        _gloss_cache[block_size] = gloss
    return _gloss_cache[block_size]

def draw_3d_block(screen, color, x, y, block_size, level=None):
    if level is not None:
        color = level_tint(color, level)
    r, g, b = color
    for iy in range(block_size):
        t = iy / block_size
        grad_r = int(r * (1 - t * 0.35))
        grad_g = int(g * (1 - t * 0.35))
        grad_b = int(b * (1 - t * 0.35))
        pygame.draw.line(screen, (grad_r, grad_g, grad_b), (x, y + iy), (x + block_size - 1, y + iy))
    top_col = (min(255, r + 80), min(255, g + 80), min(255, b + 80))
    pygame.draw.line(screen, top_col, (x + 1, y + 1), (x + block_size - 2, y + 1))
    left_col = (min(255, r + 50), min(255, g + 50), min(255, b + 50))
    pygame.draw.line(screen, left_col, (x + 1, y + 2), (x + 1, y + block_size - 2))
    bot_col = (max(0, r - 55), max(0, g - 55), max(0, b - 55))
    pygame.draw.line(screen, bot_col, (x + 1, y + block_size - 2), (x + block_size - 2, y + block_size - 2))
    right_col = (max(0, r - 35), max(0, g - 35), max(0, b - 35))
    pygame.draw.line(screen, right_col, (x + block_size - 2, y + 1), (x + block_size - 2, y + block_size - 2))
    screen.blit(_get_gloss(block_size), (x, y))
    pygame.draw.line(screen, (0, 0, 0), (x, y), (x + block_size - 1, y))
    pygame.draw.line(screen, (0, 0, 0), (x, y), (x, y + block_size - 1))
    pygame.draw.line(screen, (0, 0, 0), (x + block_size - 1, y), (x + block_size - 1, y + block_size - 1))
    pygame.draw.line(screen, (0, 0, 0), (x, y + block_size - 1), (x + block_size - 1, y + block_size - 1))


def draw_3d_grid(grid_surface, grid_color, grid_opacity):
    if not settings.get('grid_lines', True):
        grid_surface.fill((0, 0, 0, 0))
        return None
    grid_surface.fill((0, 0, 0, 0))
    alpha_color = (grid_color[0], grid_color[1], grid_color[2], grid_opacity)
    thickness = 2
    for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
        pygame.draw.line(grid_surface, alpha_color, (x, 0), (x, SCREEN_HEIGHT), thickness)
    for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
        pygame.draw.line(grid_surface, alpha_color, (0, y), (SCREEN_WIDTH, y), thickness)
    pygame.draw.line(grid_surface, alpha_color, (SCREEN_WIDTH - 1, 0), (SCREEN_WIDTH - 1, SCREEN_HEIGHT), thickness)


def load_high_score(filename='high_score.json'):
    try:
        path = data_path(filename)
        if os.path.exists(path):
            with open(path, 'r') as file:
                data = json.load(file)
                scores = {}
                for mode_key in ('marathon', 'sprint', 'ultra'):
                    entry = data.get(mode_key, {})
                    scores[mode_key] = {'score': entry.get('score', 0), 'name': entry.get('name', '---')}
                return scores
        return {mode: {'score': 0, 'name': '---'} for mode in ('marathon', 'sprint', 'ultra')}
    except Exception as e:
        print(f'Error loading high scores: {e}')
        return {mode: {'score': 0, 'name': '---'} for mode in ('marathon', 'sprint', 'ultra')}


def save_high_score(mode, score, name, filename='high_score.json'):
    try:
        scores = load_high_score(filename)
        if score > scores[mode]['score']:
            scores[mode] = {'score': score, 'name': name}
            with open(data_path(filename), 'w') as file:
                json.dump(scores, file, indent=4)
    except Exception as e:
        print(f'Error saving high score: {e}')


high_scores = load_high_score()

def create_grid():
    return [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]


def is_danger_zone_active(grid):
    for y in range(4):
        if any(grid[y]):
            return True
    return False


def valid_position(tetromino, offset, grid):
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = offset[0] + cx
                y = offset[1] + cy
                if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT:
                    return False
                if y >= 0 and grid[y][x]:
                    return False
    return True


def rotate_tetromino_with_kick(tetromino, offset, grid, rotation_state, shape_index):
    rotated = [list(row) for row in zip(*tetromino[::-1])]
    new_state = (rotation_state + 1) % 4
    if shape_index == 1:
        kicks = [(0, 0)]
    elif shape_index == 4:
        kicks = I_KICKS.get((rotation_state, new_state), [(0, 0)])
    else:
        kicks = JLSTZ_KICKS.get((rotation_state, new_state), [(0, 0)])
    for dx, dy in kicks:
        new_offset = [offset[0] + dx, offset[1] + dy]
        if valid_position(rotated, new_offset, grid):
            return (rotated, new_offset, new_state)
    return (tetromino, offset, rotation_state)


def clear_lines(grid):
    full_lines = [y for y in range(GRID_HEIGHT) if all(grid[y])]
    if full_lines:
        if len(full_lines) == 4 and multiple_line_clear_sound:
            multiple_line_clear_sound.play()
        elif line_clear_sound:
            line_clear_sound.play()
    for y in full_lines:
        del grid[y]
        grid.insert(0, [0 for _ in range(GRID_WIDTH)])
    return (grid, len(full_lines))


def update_score(score, lines_cleared):
    return score + lines_cleared * 100


def check_game_over(grid):
    return any(cell != 0 for cell in grid[0])


_bg_cache = {}


def draw_background(bg_type, level):
    if bg_type != 'auto':
        return
    key = ('bg', level)
    surf = _bg_cache.get(key)
    if surf is not None:
        screen.blit(surf, (0, 0))
        return
    rng = random.Random(level * 137)
    patterns = ['stars', 'gradient', 'checker', 'waves', 'aurora', 'stripes', 'plasma', 'rings', 'spiral', 'hex']
    pat = rng.choice(patterns)
    hue_base = (level * 47) % 360
    h1 = hue_base
    h2 = (hue_base + 60 + rng.randint(0, 60)) % 360

    def hsl_to_rgb(h, s, l):
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2
        if h < 60: r2, g2, b2 = c, x, 0
        elif h < 120: r2, g2, b2 = x, c, 0
        elif h < 180: r2, g2, b2 = 0, c, x
        elif h < 240: r2, g2, b2 = 0, x, c
        elif h < 300: r2, g2, b2 = x, 0, c
        else: r2, g2, b2 = c, 0, x
        return int((r2 + m) * 255), int((g2 + m) * 255), int((b2 + m) * 255)

    c1 = hsl_to_rgb(h1, 0.5, 0.08)
    c2 = hsl_to_rgb(h2, 0.4, 0.18)
    c3 = hsl_to_rgb((h1 + 30) % 360, 0.3, 0.04)

    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surf.fill(c3)

    if pat == 'stars':
        for _ in range(60 + level * 2):
            sx = rng.randint(0, SCREEN_WIDTH - 1)
            sy = rng.randint(0, SCREEN_HEIGHT - 1)
            sz = rng.randint(1, 3)
            br = rng.randint(100, 255)
            col = hsl_to_rgb((h1 + rng.randint(-30, 30)) % 360, 0.6, br / 510)
            pygame.draw.circle(surf, col, (sx, sy), sz)
    elif pat == 'gradient':
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            col = hsl_to_rgb((h1 + int(t * 40)) % 360, 0.5, 0.06 + t * 0.12)
            pygame.draw.line(surf, col, (0, y), (SCREEN_WIDTH, y))
    elif pat == 'checker':
        size = 16 + (level % 5) * 4
        for y in range(0, SCREEN_HEIGHT, size):
            for x in range(0, SCREEN_WIDTH, size):
                if (x // size + y // size) % 2:
                    col = c2 if (x // size) % 2 == 0 else c1
                    pygame.draw.rect(surf, col, (x, y, size, size))
    elif pat == 'waves':
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            phase = y * 0.04 + level * 0.3
            wave = int((math.sin(phase) * 0.5 + 0.5) * 50)
            col = hsl_to_rgb((h1 + int(t * 30) + wave) % 360, 0.5, 0.06 + t * 0.14)
            pygame.draw.line(surf, col, (0, y), (SCREEN_WIDTH, y))
    elif pat == 'aurora':
        bands = []
        for _ in range(rng.randint(4, 8)):
            y0 = rng.randint(0, SCREEN_HEIGHT)
            h = rng.randint(40, 120)
            band_hue = (h1 + rng.randint(-40, 80)) % 360
            bands.append((y0, h, band_hue))
        for y in range(SCREEN_HEIGHT):
            r_acc, g_acc, b_acc = 0, 0, 0
            for y0, h, bh in bands:
                dist = abs(y - y0)
                if dist < h:
                    alpha = 1.0 - dist / h
                    cr, cg, cb = hsl_to_rgb(bh, 0.7, 0.5 * alpha)
                    r_acc += int(cr * alpha * 0.3)
                    g_acc += int(cg * alpha * 0.3)
                    b_acc += int(cb * alpha * 0.3)
            col = hsl_to_rgb((h1 + y // 4) % 360, 0.3, 0.04)
            cr = min(col[0] + r_acc, 255)
            cg = min(col[1] + g_acc, 255)
            cb = min(col[2] + b_acc, 255)
            pygame.draw.line(surf, (cr, cg, cb), (0, y), (SCREEN_WIDTH, y))
    elif pat == 'stripes':
        spacing = 20 + (level % 8) * 4
        for i in range(0, SCREEN_HEIGHT + SCREEN_WIDTH, spacing * 2):
            pts = [(0, i), (i, 0)]
            pygame.draw.line(surf, c1, (0, i), (SCREEN_WIDTH, i + SCREEN_WIDTH), rng.randint(2, 6))
            if i > 0:
                pygame.draw.line(surf, c2, (i, 0), (i + SCREEN_HEIGHT, SCREEN_HEIGHT), rng.randint(2, 6))
    elif pat == 'plasma':
        for y in range(0, SCREEN_HEIGHT, 2):
            for x in range(0, SCREEN_WIDTH, 2):
                v = math.sin(x * 0.02 + level * 0.5) + math.sin(y * 0.03 + level * 0.3) + math.sin((x + y) * 0.015 + level * 0.7)
                v = (v + 3) / 6
                col = hsl_to_rgb(int(h1 + v * 120) % 360, 0.6, 0.05 + v * 0.15)
                pygame.draw.rect(surf, col, (x, y, 2, 2))
    elif pat == 'rings':
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        max_r = int(math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)) // 2 + 20
        for r in range(0, max_r, 12 + (level % 5) * 2):
            col = hsl_to_rgb((h1 + r * 2) % 360, 0.4, 0.06)
            pygame.draw.circle(surf, col, (cx, cy), r, 4)
    elif pat == 'spiral':
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        max_r = int(math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)) // 2 + 20
        steps = 200 + level * 5
        for i in range(steps):
            t = i / steps
            a = t * math.pi * 8
            r = t * max_r
            px = int(cx + r * math.cos(a))
            py = int(cy + r * math.sin(a))
            if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                col = hsl_to_rgb((h1 + int(t * 180)) % 360, 0.5, 0.06 + t * 0.12)
                surf.set_at((px, py), col)
    elif pat == 'hex':
        hs = 14
        hw = hs * math.sqrt(3)
        for row in range(-1, SCREEN_HEIGHT // int(hs * 1.5) + 2):
            for col in range(-1, SCREEN_WIDTH // int(hw) + 2):
                ox = col * hw + (row % 2) * hw / 2
                oy = row * hs * 1.5
                cx2 = ox + hw / 2
                cy2 = oy + hs
                col_hue = (h1 + row * 20 + col * 30) % 360
                col = hsl_to_rgb(col_hue, 0.3, 0.07)
                pts = []
                for k in range(6):
                    angle = math.pi / 3 * k - math.pi / 6
                    pts.append((ox + hw / 2 + hs * math.cos(angle), oy + hs + hs * math.sin(angle)))
                pygame.draw.polygon(surf, col, pts, 2)

    _bg_cache[key] = surf
    screen.blit(surf, (0, 0))


T_SHAPE = [[0, 1, 0],
           [1, 1, 1]]


def is_t_spin(tetromino, offset, grid):
    if tetromino != T_SHAPE:
        return False
    x, y = offset
    corners = [
        grid[y][x] if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT else 0,
        grid[y][x + 2] if 0 <= x + 2 < GRID_WIDTH and 0 <= y < GRID_HEIGHT else 0,
        grid[y + 2][x] if 0 <= y + 2 < GRID_HEIGHT and 0 <= x < GRID_WIDTH else 0,
        grid[y + 2][x + 2] if 0 <= y + 2 < GRID_HEIGHT and 0 <= x + 2 < GRID_WIDTH else 0,
    ]
    filled = sum(1 for c in corners if c)
    return filled >= 3


def draw_subwindow(score, next_pieces, level, pieces_dropped, lines_cleared_total, is_tetris, tetris_last_flash, combo_count=-1, back_to_back_active=False, mode='marathon', elapsed_ms=0, tetris_flash_time=(False, 0, 2000)):
    global sound_bar_rect, restart_button_rect, skip_button_rect, menu_button_rect
    subwindow = pygame.Surface((SUBWINDOW_WIDTH, SCREEN_HEIGHT))
    subwindow.fill(BLACK)
    score_text = tetris_font_small.render(f'''Score: {score}''', True, WHITE)
    mode_hs = high_scores.get(mode, {})
    high_score_text = tetris_font_small.render(f'''High: {mode_hs.get('score', 0)} ({mode_hs.get('name', '---')})''', True, WHITE)
    level_text = tetris_font_small.render(f'''Level: {level}''', True, WHITE)
    pieces_text = tetris_font_small.render(f'''Pieces Dropped: {pieces_dropped}''', True, WHITE)
    lines_text = tetris_font_small.render(f'''Lines Cleared: {lines_cleared_total}''', True, WHITE)
    subwindow.blit(score_text, (10, 10))
    subwindow.blit(high_score_text, (10, 40))
    subwindow.blit(level_text, (10, 70))
    subwindow.blit(pieces_text, (10, 100))
    subwindow.blit(lines_text, (10, 130))
    info_y = 155
    if mode != 'marathon':
        seconds = elapsed_ms // 1000
        minutes = seconds // 60
        secs = seconds % 60
        time_str = f'{minutes}:{secs:02d}'
        timer_text = tetris_font_small.render(time_str, True, YELLOW)
        subwindow.blit(timer_text, (10, info_y))
    if combo_count > 0:
        combo_x = 10 if mode == 'marathon' else 60
        combo_text = tetris_font_small.render(f'''Combo: {combo_count}''', True, (255, 200, 0))
        subwindow.blit(combo_text, (combo_x, info_y))
    if back_to_back_active:
        b2b_text = tetris_font_small.render('B2B', True, (0, 200, 255))
        subwindow.blit(b2b_text, (140, info_y))
    next_y = 200 if (mode != 'marathon' or combo_count > 0 or back_to_back_active) else 180
    next_label = tetris_font_small.render('Next:', True, WHITE)
    subwindow.blit(next_label, (10, next_y))
    piece_start_y = next_y + 20
    for idx, piece in enumerate(next_pieces[:5]):
        start_x = 10 + (idx * 70)
        start_y = piece_start_y
        shape_index = get_shape_index(piece)
        if shape_index is None:
            shape_index = 0
        color_index = (shape_index + level - 1) % len(COLORS) + 1
        for row_idx, row in enumerate(piece):
            for col_idx, cell in enumerate(row):
                if cell:
                    small_size = BLOCK_SIZE // 2
                    draw_3d_block(subwindow, COLORS[color_index - 1], start_x + col_idx * small_size, start_y + row_idx * small_size, small_size, level)
    separator_y = start_y + 4 * BLOCK_SIZE + 10
    pygame.draw.line(subwindow, WHITE, (10, separator_y), (SUBWINDOW_WIDTH - 10, separator_y), 2)
    hold_label = tetris_font_small.render('Hold:', True, WHITE)
    hold_y = separator_y + 10
    subwindow.blit(hold_label, (10, hold_y))
    if hold_piece is not None:
        start_x = 10
        start_y = hold_y + 20
        shape_index = get_shape_index(hold_piece)
        if shape_index is None:
            shape_index = 0
        color_index = (shape_index + level - 1) % len(COLORS) + 1
        for row_idx, row in enumerate(hold_piece):
            for col_idx, cell in enumerate(row):
                if cell:
                    draw_3d_block(subwindow, COLORS[color_index - 1], start_x + col_idx * BLOCK_SIZE, start_y + row_idx * BLOCK_SIZE, BLOCK_SIZE, level)
    else:
        placeholder = tetris_font_small.render('-', True, WHITE)
        subwindow.blit(placeholder, (10, hold_y + 20))
    if is_tetris:
        time_since_flash = pygame.time.get_ticks() - tetris_last_flash
        if time_since_flash < tetris_flash_time:
            flashing_color = random.choice(COLORS)
            flash_text = tetris_font_medium.render('TetraFusion!', True, flashing_color)
            text_x = (SUBWINDOW_WIDTH - flash_text.get_width()) // 2
            text_y = SCREEN_HEIGHT - 240
            subwindow.blit(flash_text, (text_x, text_y))
    current_volume = pygame.mixer.music.get_volume() if pygame.mixer.music.get_busy() else 0
    sound_label = tetris_font_small.render('Music:', True, WHITE)
    subwindow.blit(sound_label, (10, SCREEN_HEIGHT - 220))
    bar_x = 10
    bar_y = SCREEN_HEIGHT - 200
    bar_width = SUBWINDOW_WIDTH - 20
    bar_height = 20
    sound_bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(subwindow, WHITE, sound_bar_rect, 2)
    fill_width = int(current_volume * bar_width)
    pygame.draw.rect(subwindow, (0, 200, 0), (bar_x, bar_y, fill_width, bar_height))
    if settings.get('use_custom_music', False):
        btn_space = 40
        button_width = (SUBWINDOW_WIDTH - btn_space) // 3
        button_y = SCREEN_HEIGHT - 60
        restart_button_rect = pygame.Rect(10, button_y, button_width, 30)
        skip_button_rect = pygame.Rect(20 + button_width, button_y, button_width, 30)
        menu_button_rect = pygame.Rect(30 + 2 * button_width, button_y, button_width, 30)
        pygame.draw.rect(subwindow, (50, 50, 200), restart_button_rect)
        restart_text = tetris_font_small.render('Restart', True, WHITE)
        subwindow.blit(restart_text, (restart_button_rect.x + (restart_button_rect.width - restart_text.get_width()) // 2, restart_button_rect.y + (restart_button_rect.height - restart_text.get_height()) // 2))
        pygame.draw.rect(subwindow, (200, 200, 50), skip_button_rect)
        skip_text = tetris_font_smaller.render('Skip Track', True, WHITE)
        subwindow.blit(skip_text, (skip_button_rect.x + (skip_button_rect.width - skip_text.get_width()) // 2, skip_button_rect.y + (skip_button_rect.height - skip_text.get_height()) // 2))
        pygame.draw.rect(subwindow, (200, 50, 50), menu_button_rect)
        menu_text = tetris_font_small.render('Main Menu', True, WHITE)
        subwindow.blit(menu_text, (menu_button_rect.x + (menu_button_rect.width - menu_text.get_width()) // 2, menu_button_rect.y + (menu_button_rect.height - menu_text.get_height()) // 2))
    else:
        button_width = (SUBWINDOW_WIDTH - 30) // 2
        button_y = SCREEN_HEIGHT - 60
        restart_button_rect = pygame.Rect(10, button_y, button_width, 30)
        menu_button_rect = pygame.Rect(20 + button_width, button_y, button_width, 30)
        skip_button_rect = None
        pygame.draw.rect(subwindow, (50, 50, 200), restart_button_rect)
        restart_text = tetris_font_small.render('Restart', True, WHITE)
        subwindow.blit(restart_text, (restart_button_rect.x + (restart_button_rect.width - restart_text.get_width()) // 2, restart_button_rect.y + (restart_button_rect.height - restart_text.get_height()) // 2))
        pygame.draw.rect(subwindow, (200, 50, 50), menu_button_rect)
        menu_text = tetris_font_small.render('Main Menu', True, WHITE)
        subwindow.blit(menu_text, (menu_button_rect.x + (menu_button_rect.width - menu_text.get_width()) // 2, menu_button_rect.y + (menu_button_rect.height - menu_text.get_height()) // 2))
    screen.blit(subwindow, (SCREEN_WIDTH, 0))


def draw_ghost_piece(tetromino, offset, grid, color, level=None):
    if not settings.get('ghost_piece', True):
        return None
    ghost_y = offset[1]
    while valid_position(tetromino, [offset[0], ghost_y + 1], grid):
        ghost_y += 1
    ghost_offset = [offset[0], ghost_y]
    ghost_opacity = settings.get('ghost_opacity', 80)
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = (ghost_offset[0] + cx) * BLOCK_SIZE
                y = (ghost_offset[1] + cy) * BLOCK_SIZE
                ghost_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                draw_3d_block(ghost_surf, color, 0, 0, BLOCK_SIZE, level)
                ghost_surf.set_alpha(ghost_opacity)
                screen.blit(ghost_surf, (x, y))
    draw_shadow_reflection(tetromino, ghost_offset, grid)
    return None


def draw_shadow_reflection(tetromino, ghost_offset, grid):
    shadow_alpha = 20
    shadow_color = (30, 30, 30)
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                gx = ghost_offset[0] + cx
                gy = ghost_offset[1] + cy
                x = gx * BLOCK_SIZE
                y = gy * BLOCK_SIZE
                shadow_block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                shadow_block.fill((shadow_color[0], shadow_color[1], shadow_color[2], shadow_alpha))
                screen.blit(shadow_block, (x, y))


def play_custom_music(settings):
    global current_track_index
    if not settings.get('music_enabled', True):
        pygame.mixer.music.stop()
        return None
    update_custom_music_playlist(settings)
    if settings.get('use_custom_music', False) and last_track_index is not None and last_track_index < len(custom_music_playlist):
        current_track_index = last_track_index
    else:
        current_track_index = 0
    if custom_music_playlist:
        track = custom_music_playlist[current_track_index]
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.play(0)
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        except Exception as e:
            print(f'Error playing custom music: {e}')
    else:
        print('No music files found in the selected directory; loading default background music.')
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f'Error loading default background music: {e}')


def load_next_track(update_last_index=False):
    global current_track_index, last_track_index
    current_track_index = (current_track_index + 1) % len(custom_music_playlist)
    try:
        pygame.mixer.music.load(custom_music_playlist[current_track_index])
        pygame.mixer.music.play(0)
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        if update_last_index:
            last_track_index = current_track_index
    except Exception as e:
        print(f'Error loading next track: {e}')


def skip_current_track():
    if not settings.get('music_enabled', True):
        return None
    if custom_music_playlist:
        load_next_track(update_last_index=True)
        return None
    return None


def stop_music():
    pygame.mixer.music.stop()


def handle_music_end_event():
    if settings.get('use_custom_music', False) and custom_music_playlist:
        load_next_track(update_last_index=False)
        return None
    return None


def draw_main_menu(selected_index, menu_options):
    """
    Draws the main menu screen with a title and a list of selectable options.
    The option at index 'selected_index' is highlighted.
    Returns a list of rects for the menu options for click detection.
    """
    screen.fill(BLACK)
    title_text = tetris_font_large.render('TetraFusion', True, random.choice(COLORS))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 3 - 100))
    creator_text = tetris_font_small.render('by drDOOM69GAMING', True, (150, 150, 150))
    screen.blit(creator_text, (SCREEN_WIDTH // 2 - creator_text.get_width() // 2, SCREEN_HEIGHT // 3 - 65))
    option_rects = []
    for i, option in enumerate(menu_options):
        color = RED if i == selected_index else WHITE
        option_text = tetris_font_medium.render(option, True, color)
        x = SCREEN_WIDTH // 2 - option_text.get_width() // 2
        y = SCREEN_HEIGHT // 2 + i * 50
        screen.blit(option_text, (x, y))
        option_rects.append(pygame.Rect(x, y, option_text.get_width(), option_text.get_height()))
    pygame.display.flip()
    return option_rects


def main_menu():
    global game_command
    if settings.get('music_enabled', True):
        if settings.get('use_custom_music', False):
            if not pygame.mixer.music.get_busy():
                play_custom_music(settings)
        elif not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                pygame.mixer.music.set_volume(1)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f'Error loading default background music: {e}')
    menu_options = ['Marathon', 'Sprint', 'Ultra', 'Training', 'Options', 'Quit']
    selected_index = 0
    joy_delay = 150
    last_move = pygame.time.get_ticks()
    fallback_triggered = False
    option_rects = []
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            if event.type == MUSIC_END_EVENT:
                handle_music_end_event()
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4:
                    toggle_fullscreen()
                    continue
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected_index = (selected_index + 1) % len(menu_options)
                    continue
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected_index = (selected_index - 1) % len(menu_options)
                    continue
                if event.key == pygame.K_RETURN:
                    selected_text = menu_options[selected_index]
                    if selected_text in ('Marathon', 'Sprint', 'Ultra', 'Training'):
                        fade_transition(200)
                        return selected_text.lower()
                    if selected_text == 'Options':
                        fade_transition(200)
                        options_menu()
                        continue
                    if selected_text == 'Quit':
                        save_settings(settings)
                        pygame.quit()
                        sys.exit()
                    continue
                if event.key == pygame.K_o:
                    fade_transition(200)
                    options_menu()
                    continue
                if event.key == pygame.K_ESCAPE:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                continue
            if event.type == pygame.JOYBUTTONDOWN:
                nav = settings.get('controller_menu_navigation', {})
                up_btn = nav.get('up')
                down_btn = nav.get('down')
                select_btn = nav.get('select')
                if up_btn is not None and event.button == up_btn:
                    selected_index = (selected_index - 1) % len(menu_options)
                    continue
                if down_btn is not None and event.button == down_btn:
                    selected_index = (selected_index + 1) % len(menu_options)
                    continue
                if select_btn is not None and event.button == select_btn:
                    selected_text = menu_options[selected_index]
                    if selected_text == 'Marathon':
                        return 'marathon'
                    if selected_text == 'Sprint':
                        return 'sprint'
                    if selected_text == 'Ultra':
                        return 'ultra'
                    if selected_text == 'Training':
                        return 'training'
                    if selected_text == 'Options':
                        options_menu()
                        continue
                    if selected_text == 'Quit':
                        save_settings(settings)
                        pygame.quit()
                        sys.exit()
                continue
            if event.type == pygame.JOYHATMOTION:
                (hx, hy) = event.value
                if hy == 1:
                    selected_index = (selected_index - 1) % len(menu_options)
                    continue
                if hy == -1:
                    selected_index = (selected_index + 1) % len(menu_options)
            if event.type == pygame.MOUSEMOTION:
                for i, rect in enumerate(option_rects):
                    if rect.collidepoint(event.pos):
                        selected_index = i
                        break
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(option_rects):
                    if rect.collidepoint(event.pos):
                        selected_text = menu_options[i]
                        if selected_text == 'Marathon':
                            return 'marathon'
                        if selected_text == 'Sprint':
                            return 'sprint'
                        if selected_text == 'Ultra':
                            return 'ultra'
                        if selected_text == 'Training':
                            return 'training'
                        if selected_text == 'Options':
                            options_menu()
                            continue
                        if selected_text == 'Quit':
                            save_settings(settings)
                            pygame.quit()
                            sys.exit()
        if settings.get('use_custom_music', False):
            if not pygame.mixer.music.get_busy() and fallback_triggered:
                fallback_triggered = True
                load_next_track(update_last_index=False)
            elif pygame.mixer.music.get_busy():
                fallback_triggered = False
        if game_command == 'skip':
            skip_current_track()
            game_command = None
        option_rects = draw_main_menu(selected_index, menu_options)
        clock.tick(30)


def options_menu():
    global last_track_index
    selected_option = 0
    enter_pressed = False
    options = [
        ('keybinds', 'Keyboard Keybinds'),
        ('controller_keybinds', 'Controller Keybinds'),
        ('difficulty', 'Difficulty'),
        ('theme', 'Theme'),
        ('gravity_multiplier', 'Gravity'),
        ('effect', 'Effect'),
        ('particle_density', 'Particle Density'),
        ('screen_shake', 'Screen Shake'),
        ('grid_opacity', 'Grid Opacity'),
        ('grid_lines', 'Grid Lines'),
        ('ghost_piece', 'Ghost Piece'),
        ('ghost_opacity', 'Ghost Opacity'),
        ('das', 'DAS'),
        ('arr', 'ARR'),
        ('background', 'Background'),
        ('help', 'Help'),
        ('music_enabled', 'Music'),
        ('use_custom_music', 'Use Custom Music'),
        ('select_music_dir', 'Select Music Directory'),
        ('back', 'Back to Main Menu')]
    changing_key = None
    option_spacing = 32
    extra_bottom_padding = 0
    total_options_height = len(options) * option_spacing + extra_bottom_padding
    base_y = (SCREEN_HEIGHT - total_options_height) // 2

    def process_navigation_events(options, selected_option, changing_key, enter_pressed, option_rects=None):
        '''
        Processes both keyboard and controller (including D-pad) navigation events
        for the options menu. Returns updated values for selected_option, changing_key,
        enter_pressed, and an action flag (which will be the current option key if selected,
        or "back" if the user wants to exit).
        '''
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
                continue
            if event.type == MUSIC_END_EVENT:
                handle_music_end_event()
                continue
            if event.type == pygame.MOUSEMOTION:
                if option_rects:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            selected_option = i
                            break
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if option_rects:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            current_key = options[i][0]
                            if current_key in settings['controls']:
                                changing_key = current_key
                                continue
                            action = current_key
                            break
                continue
            if event.type == pygame.JOYBUTTONDOWN:
                if changing_key is None:
                    nav = settings.get('controller_menu_navigation', {})
                    up_btn = nav.get('up')
                    down_btn = nav.get('down')
                    select_btn = nav.get('select')
                    back_btn = nav.get('back')
                    if up_btn is not None and event.button == up_btn:
                        selected_option = (selected_option - 1) % len(options)
                        continue
                    if down_btn is not None and event.button == down_btn:
                        selected_option = (selected_option + 1) % len(options)
                        continue
                    if select_btn is not None and event.button == select_btn:
                        current_key = options[selected_option][0]
                        if current_key not in settings['controls']:
                            action = current_key
                        continue
                    if back_btn is not None and event.button == back_btn:
                        action = 'back'
                continue
            if event.type == pygame.JOYHATMOTION:
                if changing_key is None:
                    (hx, hy) = event.value
                    if hy == 1:
                        selected_option = (selected_option - 1) % len(options)
                        continue
                    if hy == -1:
                        selected_option = (selected_option + 1) % len(options)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4:
                    toggle_fullscreen()
                    continue
                if event.key == pygame.K_ESCAPE:
                    if changing_key is not None:
                        changing_key = None
                        continue
                    action = 'back'
                    continue
                if changing_key is not None:
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                    continue
                if event.key == pygame.K_RETURN and not enter_pressed:
                    enter_pressed = True
                    current_key = options[selected_option][0]
                    if current_key in settings['controls']:
                        changing_key = current_key
                        continue
                    action = current_key
                    continue
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                    continue
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                continue
            if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                enter_pressed = False
        return (selected_option, changing_key, enter_pressed, action)

    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render('Options', True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        option_rects = []
        for i, option in enumerate(options):
            key, label = option
            color = RED if i == selected_option else WHITE
            text = label
            if key in settings['controls']:
                text = f'''{label}: {pygame.key.name(settings['controls'][key]).upper()}'''
            elif key == 'difficulty':
                text = f'''Difficulty: {settings['difficulty'].capitalize()}'''
            elif key == 'effect':
                text = f'''Effect: {settings.get('effect', 'flame').capitalize()}'''
            elif key == 'particle_density':
                text = f'''Particles: {settings.get('particle_density', 'medium').capitalize()}'''
            elif key == 'screen_shake':
                text = f'''Screen Shake: {'On' if settings.get('screen_shake', True) else 'Off'}'''
            elif key == 'flame_trails':
                text = f'''Flame Trails: {'On' if settings['flame_trails'] else 'Off'}'''
            elif key == 'grid_opacity':
                text = f'''Grid Opacity: {settings['grid_opacity']}'''
            elif key == 'grid_lines':
                text = f'''Grid Lines: {'On' if settings.get('grid_lines', True) else 'Off'}'''
            elif key == 'theme':
                theme_idx = settings.get('theme', 0) % len(THEMES)
                text = f'''Theme: {THEMES[theme_idx]['name']}'''
            elif key == 'gravity_multiplier':
                gm = settings.get('gravity_multiplier', 1.0)
                text = f'''Gravity: {gm}x'''
            elif key == 'ghost_piece':
                text = f'''Ghost Piece: {'On' if settings.get('ghost_piece', True) else 'Off'}'''
            elif key == 'ghost_opacity':
                text = f'''Ghost Opacity: {settings.get('ghost_opacity', 80)}'''
            elif key == 'das':
                text = f'''DAS: {settings.get('das', 150)}ms'''
            elif key == 'arr':
                text = f'''ARR: {settings.get('arr', 50)}ms'''
            elif key == 'background':
                bg = settings.get('background', 'auto')
                text = f'''Background: {bg.capitalize()}'''
            elif key == 'music_enabled':
                text = f'''Music: {'On' if settings.get('music_enabled', True) else 'Off'}'''
            elif key == 'use_custom_music':
                text = f'''Use Custom Music: {'On' if settings.get('use_custom_music', False) else 'Off'}'''
            elif key == 'select_music_dir':
                dir_display = settings.get('music_directory', '')
                text = f'''Dir: {dir_display}''' if dir_display else 'Music Dir: Not Selected'
            option_text = tetris_font_medium.render(text, True, color)
            if key == 'select_music_dir':
                if settings.get('music_directory', ''):
                    scale_factor = 0.6
                else:
                    scale_factor = 1
                scaled_width = int(option_text.get_width() * scale_factor)
                scaled_height = int(option_text.get_height() * scale_factor)
                option_text = pygame.transform.scale(option_text, (scaled_width, scaled_height))
            y_coordinate = base_y + i * option_spacing
            screen.blit(option_text, (SCREEN_WIDTH // 2 - option_text.get_width() // 2, y_coordinate))
            option_rects.append(pygame.Rect(SCREEN_WIDTH // 2 - option_text.get_width() // 2, y_coordinate, option_text.get_width(), option_text.get_height()))
        pygame.display.flip()
        (selected_option, changing_key, enter_pressed, action) = process_navigation_events(options, selected_option, changing_key, enter_pressed, option_rects)
        if action is not None:
            current_key = action
            if current_key == 'keybinds':
                keyboard_keybinds_menu()
                pygame.event.clear()
            elif current_key == 'controller_keybinds':
                controller_keybinds_menu()
                pygame.event.clear()
            elif current_key == 'difficulty':
                difficulties = ['easy', 'normal', 'hard', 'very hard', 'master']
                new_idx = (difficulties.index(settings['difficulty']) + 1) % len(difficulties)
                settings['difficulty'] = difficulties[new_idx]
            elif current_key == 'effect':
                effects = ['flame', 'wind', 'water', 'ice', 'flicker', 'matrix', 'none']
                current = settings.get('effect', 'flame')
                idx = effects.index(current) if current in effects else 0
                settings['effect'] = effects[(idx + 1) % len(effects)]
            elif current_key == 'particle_density':
                densities = ['low', 'medium', 'high']
                current = settings.get('particle_density', 'medium')
                idx = densities.index(current) if current in densities else 1
                settings['particle_density'] = densities[(idx + 1) % len(densities)]
            elif current_key == 'screen_shake':
                settings['screen_shake'] = not settings.get('screen_shake', True)
            elif current_key == 'ghost_opacity':
                current = settings.get('ghost_opacity', 80)
                settings['ghost_opacity'] = (current + 32) if current < 255 else 32
            elif current_key == 'das':
                das_values = [100, 133, 150, 167, 200]
                current = settings.get('das', 150)
                idx = das_values.index(current) if current in das_values else 2
                settings['das'] = das_values[(idx + 1) % len(das_values)]
            elif current_key == 'arr':
                arr_values = [17, 33, 50, 67, 83, 100]
                current = settings.get('arr', 50)
                idx = arr_values.index(current) if current in arr_values else 2
                settings['arr'] = arr_values[(idx + 1) % len(arr_values)]
            elif current_key == 'background':
                bgs = ['auto', 'none', 'stars', 'gradient', 'checker', 'waves', 'aurora']
                current = settings.get('background', 'none')
                idx = bgs.index(current) if current in bgs else 0
                settings['background'] = bgs[(idx + 1) % len(bgs)]
            elif current_key == 'flame_trails':
                settings['flame_trails'] = not settings['flame_trails']
            elif current_key == 'grid_opacity':
                if settings['grid_opacity'] < 255:
                    new_opacity = settings['grid_opacity'] + 64
                    settings['grid_opacity'] = new_opacity if new_opacity <= 255 else 255
                else:
                    settings['grid_opacity'] = 0
            elif current_key == 'grid_lines':
                settings['grid_lines'] = not settings.get('grid_lines', True)
            elif current_key == 'theme':
                new_theme = (settings.get('theme', 0) + 1) % len(THEMES)
                settings['theme'] = new_theme
                apply_theme(new_theme)
            elif current_key == 'gravity_multiplier':
                multipliers = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]
                current = settings.get('gravity_multiplier', 1.0)
                idx = multipliers.index(current) if current in multipliers else 2
                settings['gravity_multiplier'] = multipliers[(idx + 1) % len(multipliers)]
            elif current_key == 'ghost_piece':
                settings['ghost_piece'] = not settings.get('ghost_piece', True)
            elif current_key == 'music_enabled':
                settings['music_enabled'] = not settings.get('music_enabled', True)
                if not settings['music_enabled']:
                    stop_music()
                elif settings.get('use_custom_music', False):
                    play_custom_music(settings)
                else:
                    try:
                        pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                        pygame.mixer.music.play(-1)
                    except Exception as e:
                        print(f'Error loading default music: {e}')
                    finally:
                        e = None
                        del e
            elif current_key == 'use_custom_music':
                settings['use_custom_music'] = not settings.get('use_custom_music', False)
                last_track_index = None
                if settings.get('music_enabled', True):
                    if settings.get('use_custom_music', False):
                        play_custom_music(settings)
                    else:
                        try:
                            pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                            pygame.mixer.music.play(-1)
                        except Exception as e:
                            print(f'Error loading default background music: {e}')
                        finally:
                            e = None
                            del e
                else:
                    stop_music()
            elif current_key == 'select_music_dir':
                selected_dir = select_music_directory()
                if selected_dir:
                    settings['music_directory'] = selected_dir
                    last_track_index = None
                    if settings.get('use_custom_music', False) and settings.get('music_enabled', True):
                        play_custom_music(settings)
            elif current_key == 'help':
                help_menu()
                pygame.event.clear()
            elif current_key == 'back':
                save_settings(settings)
                return None


def keyboard_keybinds_menu():
    selected_option = 0
    changing_key = None
    enter_pressed = False
    if 'skip_track' not in settings['controls']:
        settings['controls']['skip_track'] = pygame.K_x
    keybind_options = [
        ('left', 'Move Left'),
        ('right', 'Move Right'),
        ('down', 'Soft Drop'),
        ('rotate', 'Rotate'),
        ('hard_drop', 'Hard Drop'),
        ('hold', 'Hold Piece'),
        ('pause', 'Pause'),
        ('skip_track', 'Skip Track'),
        ('back', 'Back to Options')]
    option_spacing = 45
    base_y = 150

    def process_kb_nav_events(options, selected_option, changing_key, enter_pressed, option_rects=None):
        '''
        Processes both keyboard and controller (including D-pad) navigation events
        for the keyboard keybinds menu. Returns updated values for selected_option,
        changing_key, enter_pressed, and an action flag.

        NOTE:
          - This menu supports full controller navigation so that you can move up and down
            and use the controller "back" button to exit.
          - When the controller's select button is pressed on a bindable option,
            binding capture is triggered (changing_key is set) so that subsequent controller keys
            will not bind anything; only a keyboard key will be accepted.
          - The action flag will be "back" if the user wants to exit, or None otherwise.
        '''
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
                continue
            if event.type == MUSIC_END_EVENT:
                handle_music_end_event()
                continue
            if event.type == pygame.JOYBUTTONDOWN:
                if changing_key is None:
                    nav = settings.get('controller_menu_navigation', {})
                    up_btn = nav.get('up')
                    down_btn = nav.get('down')
                    select_btn = nav.get('select')
                    back_btn = nav.get('back')
                    if up_btn is not None and event.button == up_btn:
                        selected_option = (selected_option - 1) % len(options)
                        continue
                    if down_btn is not None and event.button == down_btn:
                        selected_option = (selected_option + 1) % len(options)
                        continue
                    if back_btn is not None and event.button == back_btn:
                        action = 'back'
                        continue
                    if select_btn is not None and event.button == select_btn:
                        current_key = options[selected_option][0]
                        if current_key == 'back':
                            action = 'back'
                            continue
                        if current_key in settings['controls']:
                            changing_key = current_key
                continue
            if event.type == pygame.JOYHATMOTION:
                if changing_key is None:
                    (hx, hy) = event.value
                    if hy == 1:
                        selected_option = (selected_option - 1) % len(options)
                        continue
                    if hy == -1:
                        selected_option = (selected_option + 1) % len(options)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4:
                    toggle_fullscreen()
                    continue
                if event.key == pygame.K_ESCAPE:
                    if changing_key is not None:
                        changing_key = None
                        continue
                    action = 'back'
                    continue
                if changing_key is not None:
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                    continue
                if event.key == pygame.K_RETURN and not enter_pressed:
                    enter_pressed = True
                    current_key = options[selected_option][0]
                    if current_key == 'back':
                        action = 'back'
                        continue
                    changing_key = current_key
                    continue
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                    continue
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                continue
            if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                enter_pressed = False
            if event.type == pygame.MOUSEMOTION:
                if option_rects:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            selected_option = i
                            break
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if option_rects:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            current_key = options[i][0]
                            if current_key == 'back':
                                action = 'back'
                                continue
                            if current_key in settings['controls']:
                                changing_key = current_key
                            break
                continue
        return (selected_option, changing_key, enter_pressed, action)

    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render('Keyboard Keybinds', True, WHITE)
        scaled_title = pygame.transform.scale(title_text, (int(title_text.get_width() * 0.8), int(title_text.get_height() * 0.8)))
        screen.blit(scaled_title, (SCREEN_WIDTH // 2 - scaled_title.get_width() // 2, 50))
        option_rects = []
        for i, option in enumerate(keybind_options):
            key, label = option
            color = RED if i == selected_option else WHITE
            y_coordinate = base_y + i * option_spacing
            x_center = SCREEN_WIDTH // 2
            if key in settings['controls']:
                label_text = label + ': '
                label_surface = tetris_font_medium.render(label_text, True, color)
                key_name = pygame.key.name(settings['controls'][key]).upper()
                key_color = YELLOW if changing_key == key else color
                key_surface = tetris_font_medium.render(key_name, True, key_color)
                combined_width = label_surface.get_width() + key_surface.get_width()
                x_start = x_center - combined_width // 2
                screen.blit(label_surface, (x_start, y_coordinate))
                screen.blit(key_surface, (x_start + label_surface.get_width(), y_coordinate))
                option_rects.append(pygame.Rect(x_start, y_coordinate, combined_width, max(label_surface.get_height(), key_surface.get_height())))
                continue
            display_text = label
            option_text = tetris_font_medium.render(display_text, True, color)
            screen.blit(option_text, (x_center - option_text.get_width() // 2, y_coordinate))
            option_rects.append(pygame.Rect(x_center - option_text.get_width() // 2, y_coordinate, option_text.get_width(), option_text.get_height()))
        pygame.display.flip()
        (selected_option, changing_key, enter_pressed, action) = process_kb_nav_events(keybind_options, selected_option, changing_key, enter_pressed, option_rects)
        if action is not None and action == 'back':
            fade_transition(200)
            return None


def controller_keybinds_menu():
    selected_option = 0
    changing_button = None
    enter_pressed = False
    if 'controller_controls' not in settings:
        settings['controller_controls'] = {
            'left': 14,
            'right': 15,
            'down': 13,
            'rotate': 0,
            'hard_drop': 1,
            'hold': 2,
            'pause': 3,
            'skip_track': 4}
    controller_options = [
        ('controller_menu_keybinds', 'Menu Nav Bindings'),
        ('left', 'Move Left'),
        ('right', 'Move Right'),
        ('down', 'Soft Drop'),
        ('rotate', 'Rotate'),
        ('hard_drop', 'Hard Drop'),
        ('hold', 'Hold Piece'),
        ('pause', 'Pause'),
        ('back', 'Back to Options')]
    bindable_keys = {
        'skip_track',
        'pause',
        'down',
        'rotate',
        'hold',
        'right',
        'left',
        'hard_drop'}
    option_spacing = 45
    base_y = 150

    def process_ctrl_nav_events(options, selected_option, changing_button, enter_pressed, option_rects=None):
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
                continue
            if event.type == MUSIC_END_EVENT:
                handle_music_end_event()
                continue
            if changing_button is not None:
                if event.type == pygame.JOYBUTTONDOWN:
                    settings['controller_controls'][changing_button] = event.button
                    changing_button = None
                    continue
                if event.type == pygame.JOYHATMOTION:
                    if event.value != (0, 0):
                        settings['controller_controls'][changing_button] = ('hat', event.value)
                        changing_button = None
                    continue
                if event.type == pygame.JOYAXISMOTION:
                    analog_threshold = settings['controller_settings'].get('analog_threshold', 0.5)
                    if event.axis in (0, 1) and abs(event.value) >= analog_threshold:
                        direction = 'positive' if event.value > 0 else 'negative'
                        settings['controller_controls'][changing_button] = ('axis', event.axis, direction)
                        changing_button = None
                continue
            if event.type == pygame.JOYBUTTONDOWN:
                nav = settings.get('controller_menu_navigation', {})
                up_btn = nav.get('up')
                down_btn = nav.get('down')
                select_btn = nav.get('select')
                back_btn = nav.get('back')
                if up_btn is not None and event.button == up_btn:
                    selected_option = (selected_option - 1) % len(options)
                    continue
                if down_btn is not None and event.button == down_btn:
                    selected_option = (selected_option + 1) % len(options)
                    continue
                if back_btn is not None and event.button == back_btn:
                    action = 'back'
                    continue
                if select_btn is not None and event.button == select_btn:
                    current_option = options[selected_option][0]
                    if current_option == 'back':
                        action = 'back'
                        continue
                    if current_option in settings['controller_controls']:
                        changing_button = current_option
                continue
            if event.type == pygame.JOYHATMOTION:
                (hx, hy) = event.value
                if hy == 1:
                    selected_option = (selected_option - 1) % len(options)
                    continue
                if hy == -1:
                    selected_option = (selected_option + 1) % len(options)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = 'back'
                    continue
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                    continue
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                    continue
                if event.key == pygame.K_RETURN and not enter_pressed:
                    enter_pressed = True
                    current_option = options[selected_option][0]
                    if current_option == 'back':
                        action = 'back'
                        continue
                    if current_option in settings['controller_controls']:
                        changing_button = current_option
                continue
            if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                enter_pressed = False
            if event.type == pygame.MOUSEMOTION:
                if option_rects:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            selected_option = i
                            break
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if option_rects:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            current_option = options[i][0]
                            if current_option == 'back':
                                action = 'back'
                                continue
                            if current_option == 'controller_menu_keybinds':
                                action = 'menu_nav'
                                continue
                            if current_option in settings['controller_controls']:
                                changing_button = current_option
                            break
                continue
        return (selected_option, changing_button, enter_pressed, action)

    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render('Controller Keybinds', True, WHITE)
        scaled_title = pygame.transform.scale(title_text, (int(title_text.get_width() * 0.8), int(title_text.get_height() * 0.8)))
        screen.blit(scaled_title, (SCREEN_WIDTH // 2 - scaled_title.get_width() // 2, 50))
        option_rects = []
        for i, option in enumerate(controller_options):
            key, label = option
            color = RED if i == selected_option else WHITE
            y_coordinate = base_y + i * option_spacing
            x_center = SCREEN_WIDTH // 2
            if key in bindable_keys:
                label_text = label + ': '
                label_surface = tetris_font_medium.render(label_text, True, color)
                current_binding = settings['controller_controls'].get(key)
                if current_binding is None:
                    binding_str = '(none)'
                elif isinstance(current_binding, tuple):
                    if current_binding[0] == 'hat':
                        binding_str = f'''Hat {current_binding[1]}'''
                    elif current_binding[0] == 'axis':
                        binding_str = f'''Axis {current_binding[1]} {current_binding[2]}'''
                    else:
                        binding_str = str(current_binding)
                else:
                    binding_str = f'''Button {current_binding}'''
                binding_color = YELLOW if changing_button == key else color
                binding_surface = tetris_font_medium.render(binding_str, True, binding_color)
                combined_width = label_surface.get_width() + binding_surface.get_width()
                x_start = x_center - combined_width // 2
                screen.blit(label_surface, (x_start, y_coordinate))
                screen.blit(binding_surface, (x_start + label_surface.get_width(), y_coordinate))
                option_rects.append(pygame.Rect(x_start, y_coordinate, combined_width, max(label_surface.get_height(), binding_surface.get_height())))
                continue
            option_text = tetris_font_medium.render(label, True, color)
            screen.blit(option_text, (x_center - option_text.get_width() // 2, y_coordinate))
            option_rects.append(pygame.Rect(x_center - option_text.get_width() // 2, y_coordinate, option_text.get_width(), option_text.get_height()))
        pygame.display.flip()
        (selected_option, changing_button, enter_pressed, action) = process_ctrl_nav_events(controller_options, selected_option, changing_button, enter_pressed, option_rects)
        if action is not None:
            if action == 'back':
                fade_transition(200)
                return None
            if action == 'menu_nav':
                fade_transition(200)
                controller_menu_nav_menu()


def controller_menu_nav_menu():
    selected_option = 0
    changing_button = None
    enter_pressed = False
    if 'controller_menu_navigation' not in settings:
        settings['controller_menu_navigation'] = {
            'up': None,
            'down': None,
            'left': None,
            'right': None,
            'select': None,
            'back': None}
    menu_nav_options = [
        ('up', 'Menu Up'),
        ('down', 'Menu Down'),
        ('select', 'Menu Select'),
        ('back', 'Menu Back'),
        ('exit', 'Back to Controller Keybinds')]
    bindable_keys = {
        'select',
        'back',
        'down',
        'up'}
    option_spacing = 45
    base_y = 150

    def process_menu_nav_events(options, selected_option, changing_button, enter_pressed, option_rects=None):
        '''
        Processes both keyboard and controller (including D-pad) navigation events
        for the controller menu navigation bindings menu. Returns updated values for
        selected_option, changing_button, enter_pressed, and an action flag.

        NOTE:
          - In this menu, binding capture is triggered by Enter (keyboard) or the controller
            select button. However, once binding mode is active (i.e. changing_button is not None),
            only controller key inputs (JOYBUTTONDOWN) will update the binding in settings["controller_menu_navigation"].
          - Keyboard events are allowed for navigation but are not used to update the binding.
          - The action flag will be "exit" (or "back") if the user selects that option.
        '''
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
                continue
            if event.type == MUSIC_END_EVENT:
                handle_music_end_event()
                continue
            if event.type == pygame.JOYBUTTONDOWN:
                if changing_button is not None:
                    settings['controller_menu_navigation'][changing_button] = event.button
                    changing_button = None
                    continue
                nav = settings.get('controller_menu_navigation', {})
                up_btn = nav.get('up')
                down_btn = nav.get('down')
                select_btn = nav.get('select')
                back_btn = nav.get('back')
                if up_btn is not None and event.button == up_btn:
                    selected_option = (selected_option - 1) % len(options)
                    continue
                if down_btn is not None and event.button == down_btn:
                    selected_option = (selected_option + 1) % len(options)
                    continue
                if back_btn is not None and event.button == back_btn:
                    action = 'back'
                    continue
                if select_btn is not None and event.button == select_btn:
                    current_option = options[selected_option][0]
                    if current_option == 'exit':
                        action = 'exit'
                        continue
                    if current_option in bindable_keys:
                        changing_button = current_option
                continue
            if event.type == pygame.JOYHATMOTION:
                if changing_button is None:
                    (hx, hy) = event.value
                    if hy == 1:
                        selected_option = (selected_option - 1) % len(options)
                        continue
                    if hy == -1:
                        selected_option = (selected_option + 1) % len(options)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if changing_button is not None:
                        changing_button = None
                        continue
                    action = 'back'
                    continue
                if changing_button is None:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(options)
                        continue
                    if event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(options)
                        continue
                    if event.key == pygame.K_RETURN and not enter_pressed:
                        enter_pressed = True
                        current_option = options[selected_option][0]
                        if current_option == 'exit':
                            action = 'exit'
                            continue
                        if current_option in bindable_keys:
                            changing_button = current_option
                continue
            if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                enter_pressed = False
            if event.type == pygame.MOUSEMOTION:
                if option_rects:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            selected_option = i
                            break
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if option_rects:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            current_option = options[i][0]
                            if current_option == 'exit':
                                action = 'exit'
                                continue
                            if current_option in bindable_keys:
                                changing_button = current_option
                            break
                continue
        return (selected_option, changing_button, enter_pressed, action)

    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render('Menu Nav Bindings', True, WHITE)
        scaled_title = pygame.transform.scale(title_text, (int(title_text.get_width() * 0.8), int(title_text.get_height() * 0.8)))
        screen.blit(scaled_title, (SCREEN_WIDTH // 2 - scaled_title.get_width() // 2, 50))
        option_rects = []
        for i, option in enumerate(menu_nav_options):
            key, label = option
            color = RED if i == selected_option else WHITE
            y_coordinate = base_y + i * option_spacing
            x_center = SCREEN_WIDTH // 2
            if key in bindable_keys:
                label_text = label + ': '
                label_surface = tetris_font_medium.render(label_text, True, color)
                current_binding = settings['controller_menu_navigation'].get(key)
                binding_str = str(current_binding) if current_binding is not None else '(none)'
                binding_color = YELLOW if changing_button == key else color
                binding_surface = tetris_font_medium.render(binding_str, True, binding_color)
                combined_width = label_surface.get_width() + binding_surface.get_width()
                x_start = x_center - combined_width // 2
                screen.blit(label_surface, (x_start, y_coordinate))
                screen.blit(binding_surface, (x_start + label_surface.get_width(), y_coordinate))
                option_rects.append(pygame.Rect(x_start, y_coordinate, combined_width, max(label_surface.get_height(), binding_surface.get_height())))
                continue
            display_text = label
            option_text = tetris_font_medium.render(display_text, True, color)
            if key == 'exit':
                option_text = pygame.transform.scale(option_text, (int(option_text.get_width() * 0.85), int(option_text.get_height() * 0.85)))
            screen.blit(option_text, (x_center - option_text.get_width() // 2, y_coordinate))
            option_rects.append(pygame.Rect(x_center - option_text.get_width() // 2, y_coordinate, option_text.get_width(), option_text.get_height()))
        pygame.display.flip()
        (selected_option, changing_button, enter_pressed, action) = process_menu_nav_events(menu_nav_options, selected_option, changing_button, enter_pressed, option_rects)
        if action is not None:
            if action == 'exit' or action == 'back':
                fade_transition(200)
                return None


def pause_game(mode='marathon'):
    options = ['Resume', 'Restart', 'Quit to Menu']
    selected = 0
    pygame.event.clear(pygame.KEYDOWN)
    pygame.mixer.music.pause()
    bg_capture = screen.copy()
    dim_surf = pygame.Surface((SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    anim_start = pygame.time.get_ticks()
    PAUSE_FADE_DURATION = 300
    while True:
        current_t = pygame.time.get_ticks()
        fade_progress = min(1.0, (current_t - anim_start) / PAUSE_FADE_DURATION)
        screen.blit(bg_capture, (0, 0))
        dim_surf.fill((0, 0, 0, int(180 * fade_progress)))
        screen.blit(dim_surf, (0, 0))
        pause_text = tetris_font_large.render('PAUSED', True, WHITE)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 3 - 50))
        rects = []
        for i, opt in enumerate(options):
            color = RED if i == selected else WHITE
            txt = tetris_font_medium.render(opt, True, color)
            x = SCREEN_WIDTH // 2 - txt.get_width() // 2
            y = SCREEN_HEIGHT // 2 + i * 50
            screen.blit(txt, (x, y))
            rects.append(pygame.Rect(x, y, txt.get_width(), txt.get_height()))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEMOTION:
                for i, r in enumerate(rects):
                    if r.collidepoint(event.pos):
                        selected = i
                        break
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(event.pos):
                        pygame.mixer.music.unpause()
                        if i == 0:
                            return None
                        if i == 1:
                            run_game(mode)
                            return None
                        if i == 2:
                            main_menu()
                            return None
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(options)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    pygame.mixer.music.unpause()
                    if selected == 0:
                        return None
                    if selected == 1:
                        run_game(mode)
                        return None
                    if selected == 2:
                        main_menu()
                        return None
                elif event.key == settings['controls']['pause'] or event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.unpause()
                    return None
            if event.type == pygame.JOYBUTTONDOWN and settings.get('controller_controls', {}).get('pause') is not None and event.button == settings['controller_controls']['pause']:
                pygame.mixer.music.unpause()
                return None


def display_game_over(score, mode='marathon', lines_cleared=0, pieces_dropped=0, level=1, elapsed_ms=0, max_combo=0, t_spin_count=0):
    global high_scores
    mode_hs = high_scores.get(mode, {}).get('score', 0)

    def restart_game():
        if settings.get('music_enabled', True):
            if settings.get('use_custom_music', False):
                play_custom_music(settings)
            else:
                try:
                    pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                except Exception as e:
                    print(f'Error loading default background music: {e}')
        run_game(mode)
        return None

    def go_to_main_menu():
        main_menu()

    seconds = elapsed_ms // 1000
    minutes = seconds // 60
    secs = seconds % 60
    time_str = f'{minutes}:{secs:02d}' if elapsed_ms > 0 else ''

    if score > mode_hs:
        initials = ''
        input_active = True
        while input_active:
            screen.fill(BLACK)
            game_over_text = tetris_font_large.render('NEW HIGH SCORE!', True, RED)
            score_text = tetris_font_medium.render(f'''Score: {score}''', True, WHITE)
            stats_text = tetris_font_small.render(f'''Lines: {lines_cleared}  Pieces: {pieces_dropped}  Lvl: {level}  Max Combo: {max_combo}''', True, WHITE)
            initials_text = tetris_font_medium.render(f'''Enter Initials: {initials}''', True, WHITE)
            menu_text = tetris_font_small.render('Press M for Menu or ENTER to Save', True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 50))
            screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 140))
            screen.blit(stats_text, (SCREEN_WIDTH // 2 - stats_text.get_width() // 2, 180))
            if time_str:
                time_display = tetris_font_small.render(f'''Time: {time_str}''', True, WHITE)
                screen.blit(time_display, (SCREEN_WIDTH // 2 - time_display.get_width() // 2, 210))
            initials_text = tetris_font_medium.render(f'''Enter Initials: {initials}''', True, WHITE)
            screen.blit(initials_text, (SCREEN_WIDTH // 2 - initials_text.get_width() // 2, 260))
            menu_text = tetris_font_small.render('Press M for Menu or ENTER to Save', True, WHITE)
            screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, 310))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and initials:
                        save_high_score(mode, score, initials)
                        high_scores = load_high_score()
                        input_active = False
                    if event.key == pygame.K_BACKSPACE:
                        initials = initials[:-1]
                    if len(initials) < 3 and event.unicode.isalnum():
                        initials += event.unicode.upper()
                    if event.key == pygame.K_m:
                        go_to_main_menu()
                        return None
                if event.type == pygame.JOYBUTTONDOWN and settings.get('controller_menu_navigation'):
                    if event.button == settings['controller_menu_navigation'].get('select'):
                        if initials:
                            save_high_score(mode, score, initials)
                            high_scores = load_high_score()
                            input_active = False
                    if event.button == settings['controller_menu_navigation'].get('back'):
                        go_to_main_menu()
                        return None
        if not input_active:
            restart_game()
            return None
    else:
        screen.fill(BLACK)
        game_over_text = tetris_font_large.render('GAME OVER', True, RED)
        score_text = tetris_font_medium.render(f'''Score: {score}''', True, WHITE)
        lines_text = tetris_font_small.render(f'''Lines: {lines_cleared}  Pieces: {pieces_dropped}  Lvl: {level}  Combo: {max_combo}''', True, WHITE)
        if t_spin_count:
            t_spin_display = tetris_font_small.render(f'''T-Spins: {t_spin_count}''', True, WHITE)
        restart_text = tetris_font_small.render('Press R to Restart', True, WHITE)
        menu_text = tetris_font_small.render('Press M for Menu', True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 50))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 140))
        screen.blit(lines_text, (SCREEN_WIDTH // 2 - lines_text.get_width() // 2, 180))
        if time_str:
            time_display = tetris_font_small.render(f'''Time: {time_str}''', True, WHITE)
            screen.blit(time_display, (SCREEN_WIDTH // 2 - time_display.get_width() // 2, 210))
        if t_spin_count:
            screen.blit(t_spin_display, (SCREEN_WIDTH // 2 - t_spin_display.get_width() // 2, 240))
        restart_text = tetris_font_small.render('Press R to Restart', True, WHITE)
        menu_text = tetris_font_small.render('Press M for Menu', True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT - 130))
        screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, SCREEN_HEIGHT - 100))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    restart_game()
                    return None
                if event.key == pygame.K_m:
                    go_to_main_menu()
                    return None
            if event.type == pygame.JOYBUTTONDOWN and settings.get('controller_menu_navigation'):
                if event.button == settings['controller_menu_navigation'].get('select'):
                    restart_game()
                    return None
                if event.button == settings['controller_menu_navigation'].get('back'):
                    go_to_main_menu()
                    return None
        return None


def display_victory(score, elapsed_ms, mode, lines_cleared=0, pieces_dropped=0, level=1):
    global high_scores
    mode_hs = high_scores.get(mode, {}).get('score', 0)

    def restart_game():
        if settings.get('music_enabled', True):
            if settings.get('use_custom_music', False):
                play_custom_music(settings)
            else:
                try:
                    pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                except Exception as e:
                    print(f'Error loading default background music: {e}')
        run_game(mode)
        return None

    def go_to_main_menu():
        main_menu()

    seconds = elapsed_ms // 1000
    minutes = seconds // 60
    secs = seconds % 60
    time_str = f'{minutes}:{secs:02d}'
    if score > mode_hs:
        initials = ''
        input_active = True
        while input_active:
            screen.fill(BLACK)
            if mode == 'sprint':
                title = f'Sprint Complete!'
            else:
                title = f'Time Up!'
            title_text = tetris_font_large.render(title, True, YELLOW)
            time_display = tetris_font_medium.render(f'Time: {time_str}', True, WHITE)
            score_text = tetris_font_medium.render(f'Score: {score}', True, WHITE)
            high_text = tetris_font_medium.render('NEW HIGH SCORE!', True, RED)
            initials_text = tetris_font_medium.render(f'Enter Initials: {initials}', True, WHITE)
            menu_text = tetris_font_small.render('Press M for Menu or ENTER to Save', True, WHITE)
            screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 30))
            screen.blit(time_display, (SCREEN_WIDTH // 2 - time_display.get_width() // 2, 90))
            screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 130))
            stats_v = tetris_font_small.render(f'''Lines: {lines_cleared}  Pieces: {pieces_dropped}  Lvl: {level}''', True, WHITE)
            screen.blit(stats_v, (SCREEN_WIDTH // 2 - stats_v.get_width() // 2, 165))
            screen.blit(high_text, (SCREEN_WIDTH // 2 - high_text.get_width() // 2, 205))
            screen.blit(initials_text, (SCREEN_WIDTH // 2 - initials_text.get_width() // 2, 240))
            screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, 340))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and initials:
                        save_high_score(mode, score, initials)
                        high_scores = load_high_score()
                        input_active = False
                    if event.key == pygame.K_BACKSPACE:
                        initials = initials[:-1]
                    if len(initials) < 3 and event.unicode.isalnum():
                        initials += event.unicode.upper()
                    if event.key == pygame.K_m:
                        go_to_main_menu()
                        return None
                if event.type == pygame.JOYBUTTONDOWN and settings.get('controller_menu_navigation'):
                    if event.button == settings['controller_menu_navigation'].get('select'):
                        if initials:
                            save_high_score(mode, score, initials)
                            high_scores = load_high_score()
                            input_active = False
                    if event.button == settings['controller_menu_navigation'].get('back'):
                        go_to_main_menu()
                        return None
        if not input_active:
            restart_game()
            return None
    else:
        screen.fill(BLACK)
        if mode == 'sprint':
            title = 'Sprint Complete!'
        else:
            title = 'Time Up!'
        title_text = tetris_font_large.render(title, True, YELLOW)
        time_display = tetris_font_medium.render(f'Time: {time_str}', True, WHITE)
        score_text = tetris_font_medium.render(f'Score: {score}', True, WHITE)
        stats_text = tetris_font_small.render(f'''Lines: {lines_cleared}  Pieces: {pieces_dropped}  Lvl: {level}''', True, WHITE)
        restart_text = tetris_font_small.render('Press R to Restart', True, WHITE)
        menu_text = tetris_font_small.render('Press M for Menu', True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        screen.blit(time_display, (SCREEN_WIDTH // 2 - time_display.get_width() // 2, 110))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 150))
        screen.blit(stats_text, (SCREEN_WIDTH // 2 - stats_text.get_width() // 2, 190))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT - 130))
        screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, SCREEN_HEIGHT - 100))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    restart_game()
                    return None
                if event.key == pygame.K_m:
                    go_to_main_menu()
                    return None
            if event.type == pygame.JOYBUTTONDOWN and settings.get('controller_menu_navigation'):
                if event.button == settings['controller_menu_navigation'].get('select'):
                    restart_game()
                    return None
                if event.button == settings['controller_menu_navigation'].get('back'):
                    go_to_main_menu()
                    return None
    return None


def place_tetromino(tetromino, offset, grid, color_index):
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = offset[0] + cx
                y = offset[1] + cy
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    grid[y][x] = color_index


def run_game(mode='marathon'):
    global _bg_cache, hold_piece, hold_used, game_command, heartbeat_playing
    _bg_cache.clear()
    joy = None
    if pygame.joystick.get_count() > 0:
        joy = pygame.joystick.Joystick(0)
        joy.init()
    hold_piece = None
    hold_used = False
    game_command = None
    controls = settings['controls']
    cc = settings.get('controller_controls', {})
    difficulty = settings['difficulty']
    flame_trails_enabled = settings['flame_trails']
    effect_name = settings.get('effect', 'flame')
    grid_color = apply_theme(settings.get('theme', 0))
    grid_opacity = settings.get('grid_opacity', 255)
    grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    draw_3d_grid(grid_surface, grid_color, grid_opacity)
    difficulty_speeds = {'easy': 1500, 'normal': 1000, 'hard': 600, 'very hard': 400, 'master': 200}
    base_fall_speed = int(difficulty_speeds.get(difficulty, 1000) / settings.get('gravity_multiplier', 1.0))
    fall_speed = base_fall_speed
    level = 15 if difficulty == 'master' else 1
    lines_cleared_total = 0
    pieces_dropped = 0
    trail_particles = []
    explosion_particles = []
    dust_particles = []
    screen_shake = 0
    combo_count = -1
    back_to_back_active = False
    max_combo = 0
    t_spin_count = 0
    lock_delay_active = False
    lock_delay_start = 0
    lock_delay_resets = 0
    clearing_lines = []
    clear_anim_start = 0
    game_over_anim_start = 0
    game_over_anim_active = False
    start_time = pygame.time.get_ticks()
    game_won = False
    grid = create_grid()
    tetromino_bag = TetrominoBag(SHAPES)
    tetromino = tetromino_bag.get_next_tetromino()
    next_pieces = [tetromino_bag.get_next_tetromino() for _ in range(5)]
    shape_index = get_shape_index(tetromino) or 0
    color_index = (shape_index + level - 1) % len(COLORS) + 1
    rotation_state = 0
    offset = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
    score = 0
    fast_fall = False
    last_fall_time = pygame.time.get_ticks()
    game_over = False
    left_pressed = False
    right_pressed = False
    down_pressed = False
    mouse_col = None
    mouse_on_board = False
    mouse_dx = 0
    mouse_dy = False
    last_horizontal_move = pygame.time.get_ticks()
    move_interval = settings.get('das', 150)
    fast_move_interval = settings.get('arr', 50)
    is_tetris = False
    tetris_flash_time = 2000
    tetris_last_flash = 0
    in_level_transition = False
    transition_start_time = 0
    TRANSITION_DURATION = 2000
    FLASH_INTERVAL = 100
    last_flash_time = pygame.time.get_ticks()
    flash_count = 0
    pygame.key.set_repeat(300, 100)

    def lock_and_update_tetromino(current_time=None):
        global hold_used
        nonlocal grid, score, lines_cleared_total, pieces_dropped, screen_shake, level, fall_speed, tetromino, next_pieces, offset, shape_index, color_index, rotation_state, game_over, is_tetris, tetris_last_flash, in_level_transition, transition_start_time, last_flash_time, flash_count, explosion_particles, dust_particles, lock_delay_active, lock_delay_resets, combo_count, back_to_back_active, game_won, max_combo, t_spin_count, clearing_lines, clear_anim_start
        hard_drop_rows = 0
        temp_offset = offset.copy()
        while valid_position(tetromino, [temp_offset[0], temp_offset[1] + 1], grid):
            temp_offset[1] += 1
            hard_drop_rows += 1
        offset[1] = temp_offset[1]
        score += hard_drop_rows * 2
        for _ in range(20 + hard_drop_rows * 5):
            dust_particles.append(DustParticle((offset[0] + random.uniform(-1, len(tetromino[0]) + 1)) * BLOCK_SIZE, (offset[1] + len(tetromino)) * BLOCK_SIZE))
        for _ in range(8 + hard_drop_rows * 2):
            dx = (offset[0] + random.uniform(-0.5, len(tetromino[0]) + 0.5)) * BLOCK_SIZE
            dy = (offset[1] + random.uniform(0, len(tetromino))) * BLOCK_SIZE
            dust_particles.append(DustParticle(dx, dy))
        if check_game_over(grid):
            game_over = True
            return None
        original_grid = [row[:] for row in grid]
        place_tetromino(tetromino, offset, grid, color_index)
        hold_used = False
        t_spin_bonus = is_t_spin(tetromino, offset, grid)
        if t_spin_bonus:
            score += 400 * level
            t_spin_count += 1
        full_ys = [y for y in range(GRID_HEIGHT) if all(grid[y])]
        cleared_colors = {}
        if full_ys:
            for y in full_ys:
                cleared_colors[y] = [grid[y][x] for x in range(GRID_WIDTH)]
        grid, lines_cleared = clear_lines(grid)
        if full_ys:
            clearing_lines = full_ys
            clear_anim_start = current_time if current_time is not None else pygame.time.get_ticks()
            for y in full_ys:
                for x in range(GRID_WIDTH):
                    ci = cleared_colors[y][x]
                    explosion_particles.append(Explosion(x * BLOCK_SIZE + BLOCK_SIZE // 2, y * BLOCK_SIZE + BLOCK_SIZE // 2, COLORS[ci - 1], particle_count=8, max_speed=8, duration=40))
        lines_cleared_total += lines_cleared
        if mode == 'sprint' and lines_cleared_total >= 40:
            game_won = True
        score = update_score(score, lines_cleared)
        if lines_cleared > 0:
            combo_count += 1
            if combo_count > max_combo:
                max_combo = combo_count
            if combo_count > 0:
                score += 50 * combo_count * level * lines_cleared
            if lines_cleared == 4:
                if back_to_back_active:
                    score += score // 2
                back_to_back_active = True
            elif lines_cleared == 1 or lines_cleared == 2 or lines_cleared == 3:
                back_to_back_active = False
            if all(cell == 0 for row in grid for cell in row):
                score += 1200 * level
        else:
            combo_count = -1
            back_to_back_active = False
        pieces_dropped += 1
        if lines_cleared > 0:
            screen_shake = 8 + lines_cleared * 3
        if lines_cleared == 4:
            is_tetris = True
            tetris_last_flash = current_time
        new_level = lines_cleared_total // 10 + 1
        if new_level > level:
            level = new_level
            fall_speed = max(50, int(base_fall_speed * (0.85 ** (level - 1))))
            in_level_transition = True
            transition_start_time = current_time
            last_flash_time = current_time
            flash_count = 0
        tetromino = next_pieces.pop(0)
        shape_index = get_shape_index(tetromino) or 0
        color_index = (shape_index + level - 1) % len(COLORS) + 1
        rotation_state = 0
        next_pieces.append(tetromino_bag.get_next_tetromino())
        offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
        lock_delay_active = False
        lock_delay_resets = 0

    def process_keyboard_events(events, current_time):
        global hold_piece, hold_used, game_command
        nonlocal left_pressed, right_pressed, down_pressed, fast_fall, offset, last_horizontal_move, tetromino, shape_index, color_index, rotation_state, lock_delay_active, lock_delay_start, lock_delay_resets, next_pieces, pieces_dropped
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls['left']:
                    left_pressed = True
                    new_x = offset[0] - 1
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                        if lock_delay_active and lock_delay_resets < MAX_LOCK_DELAY_RESETS:
                            lock_delay_start = current_time
                            lock_delay_resets += 1
                    last_horizontal_move = current_time
                elif event.key == controls['right']:
                    right_pressed = True
                    new_x = offset[0] + 1
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                        if lock_delay_active and lock_delay_resets < MAX_LOCK_DELAY_RESETS:
                            lock_delay_start = current_time
                            lock_delay_resets += 1
                    last_horizontal_move = current_time
                elif event.key == controls['down']:
                    fast_fall = True
                    down_pressed = True
                elif event.key == controls['rotate']:
                    rotated, new_offset, rotation_state = rotate_tetromino_with_kick(tetromino, offset, grid, rotation_state, shape_index)
                    if rotated is not tetromino:
                        tetromino, offset = rotated, new_offset
                        if lock_delay_active and lock_delay_resets < MAX_LOCK_DELAY_RESETS:
                            lock_delay_start = current_time
                            lock_delay_resets += 1
                elif event.key == controls.get('hold', pygame.K_c):
                    if not hold_used:
                        hold_used = True
                        if hold_piece is None:
                            hold_piece = copy.deepcopy(tetromino)
                            tetromino = next_pieces.pop(0)
                            next_pieces.append(tetromino_bag.get_next_tetromino())
                        else:
                            hold_piece, tetromino = copy.deepcopy(tetromino), copy.deepcopy(hold_piece)
                        shape_index = get_shape_index(tetromino) or 0
                        color_index = (shape_index + level - 1) % len(COLORS) + 1
                        rotation_state = 0
                        offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
                elif event.key == controls['hard_drop']:
                    lock_and_update_tetromino(current_time)
                elif event.key == controls['pause']:
                    pause_game(mode)
                    game_command = 'skip'
                elif mode == 'training' and event.key == pygame.K_h:
                    for x in range(GRID_WIDTH):
                        for y in range(GRID_HEIGHT - 1, -1, -1):
                            if grid[y][x]:
                                for dy in range(y, 0, -1):
                                    grid[dy][x] = grid[dy - 1][x]
                                grid[0][x] = 0
                                break
                    pieces_dropped += 1
            elif event.type == pygame.KEYUP:
                if event.key == controls['left']:
                    left_pressed = False
                elif event.key == controls['right']:
                    right_pressed = False
                elif event.key == controls['down']:
                    fast_fall = False
                    down_pressed = False

    def process_controller_events(events, current_time):
        global hold_piece, hold_used, game_command
        nonlocal left_pressed, right_pressed, down_pressed, fast_fall, tetromino, offset, shape_index, color_index, rotation_state, last_horizontal_move, lock_delay_active, lock_delay_start, lock_delay_resets, next_pieces
        analog_threshold = settings['controller_settings'].get('analog_threshold', 0.5)
        hat_threshold = settings['controller_settings'].get('hat_threshold', 0.5)
        analog_deadzone = settings['controller_settings'].get('analog_deadzone', 0.3)
        for event in events:
            if event.type == pygame.JOYBUTTONDOWN:
                if cc.get('left') is not None and event.button == cc.get('left'):
                    left_pressed = True
                    if lock_delay_active and lock_delay_resets < MAX_LOCK_DELAY_RESETS:
                        lock_delay_start = current_time
                        lock_delay_resets += 1
                elif cc.get('right') is not None and event.button == cc.get('right'):
                    right_pressed = True
                    if lock_delay_active and lock_delay_resets < MAX_LOCK_DELAY_RESETS:
                        lock_delay_start = current_time
                        lock_delay_resets += 1
                elif cc.get('down') is not None and event.button == cc.get('down'):
                    fast_fall = True
                    down_pressed = True
                elif cc.get('rotate') is not None and event.button == cc.get('rotate'):
                    rotated, new_offset, rotation_state = rotate_tetromino_with_kick(tetromino, offset, grid, rotation_state, shape_index)
                    if rotated is not tetromino:
                        tetromino, offset = rotated, new_offset
                        if lock_delay_active and lock_delay_resets < MAX_LOCK_DELAY_RESETS:
                            lock_delay_start = current_time
                            lock_delay_resets += 1
                elif cc.get('hard_drop') is not None and event.button == cc.get('hard_drop'):
                    lock_and_update_tetromino(current_time)
                elif cc.get('hold') is not None and event.button == cc.get('hold'):
                    if not hold_used:
                        hold_used = True
                        if hold_piece is None:
                            hold_piece = copy.deepcopy(tetromino)
                            tetromino = next_pieces.pop(0)
                            next_pieces.append(tetromino_bag.get_next_tetromino())
                        else:
                            hold_piece, tetromino = copy.deepcopy(tetromino), copy.deepcopy(hold_piece)
                        shape_index = get_shape_index(tetromino) or 0
                        color_index = (shape_index + level - 1) % len(COLORS) + 1
                        rotation_state = 0
                        offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
                elif cc.get('pause') is not None and event.button == cc.get('pause'):
                    pause_game(mode)
                elif cc.get('skip_track') is not None and event.button == cc.get('skip_track'):
                    game_command = 'skip'
            elif event.type == pygame.JOYBUTTONUP:
                if cc.get('left') is not None and event.button == cc.get('left'):
                    left_pressed = False
                elif cc.get('right') is not None and event.button == cc.get('right'):
                    right_pressed = False
                elif cc.get('down') is not None and event.button == cc.get('down'):
                    fast_fall = False
                    down_pressed = False
            elif event.type == pygame.JOYHATMOTION:
                if settings['controller_settings'].get('use_dpad', True):
                    hx, hy = event.value
                    if hx < -hat_threshold:
                        left_pressed = True
                        right_pressed = False
                    elif hx > hat_threshold:
                        right_pressed = True
                        left_pressed = False
                    else:
                        left_pressed = False
                        right_pressed = False
                    if hy < -hat_threshold:
                        fast_fall = True
                        down_pressed = True
                    else:
                        fast_fall = False
                        down_pressed = False
            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:
                    if abs(event.value) < analog_deadzone:
                        left_pressed = False
                        right_pressed = False
                    elif event.value < 0:
                        left_pressed = True
                        right_pressed = False
                    else:
                        right_pressed = True
                        left_pressed = False
                elif event.axis == 1:
                    if event.value >= analog_threshold:
                        fast_fall = True
                        down_pressed = True
                    else:
                        fast_fall = False
                        down_pressed = False

    def process_mouse_events(events):
        global hold_piece, hold_used, game_command
        nonlocal mouse_col, mouse_on_board, mouse_dx, mouse_dy, offset, tetromino, shape_index, color_index, rotation_state, next_pieces
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if 0 <= mx < GRID_WIDTH * BLOCK_SIZE and 0 <= my < GRID_HEIGHT * BLOCK_SIZE and not game_over and not game_won and not in_level_transition:
                    mouse_on_board = True
                    col = min(max(mx // BLOCK_SIZE - len(tetromino[0]) // 2, 0), GRID_WIDTH - len(tetromino[0]))
                    if col != mouse_col:
                        mouse_dx = 1 if col > (mouse_col or 0) else -1
                        mouse_col = col
                        if valid_position(tetromino, [col, offset[1]], grid) and valid_position(tetromino, [col, offset[1] + 1], grid):
                            offset[0] = col
                else:
                    mouse_on_board = False
                if event.buttons[0] and event.pos[0] >= SCREEN_WIDTH:
                    rel_x = event.pos[0] - SCREEN_WIDTH
                    if sound_bar_rect and sound_bar_rect.collidepoint(rel_x, event.pos[1]):
                        new_volume = (rel_x - sound_bar_rect.x) / sound_bar_rect.width
                        pygame.mixer.music.set_volume(new_volume)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0] >= SCREEN_WIDTH:
                    rel_x = event.pos[0] - SCREEN_WIDTH
                    rel_y = event.pos[1]
                    if sound_bar_rect and sound_bar_rect.collidepoint(rel_x, rel_y):
                        new_volume = (rel_x - sound_bar_rect.x) / sound_bar_rect.width
                        pygame.mixer.music.set_volume(new_volume)
                    if restart_button_rect and restart_button_rect.collidepoint(rel_x, rel_y):
                        game_command = 'restart'
                        return None
                    if settings.get('use_custom_music', False) and skip_button_rect and skip_button_rect.collidepoint(rel_x, rel_y):
                        game_command = 'skip'
                    if menu_button_rect and menu_button_rect.collidepoint(rel_x, rel_y):
                        game_command = 'menu'
                elif not game_over and not game_won and not in_level_transition:
                    mx, my = event.pos
                    if 0 <= mx < GRID_WIDTH * BLOCK_SIZE and 0 <= my < GRID_HEIGHT * BLOCK_SIZE:
                        if event.button == 1:
                            lock_and_update_tetromino(current_time)
                        elif event.button == 3:
                            rotated, new_offset, rotation_state = rotate_tetromino_with_kick(tetromino, offset, grid, rotation_state, shape_index)
                            if rotated is not tetromino:
                                tetromino, offset = rotated, new_offset
                        elif event.button == 2:
                            if not hold_used:
                                hold_used = True
                                if hold_piece is None:
                                    hold_piece = copy.deepcopy(tetromino)
                                    tetromino = next_pieces.pop(0)
                                    next_pieces.append(tetromino_bag.get_next_tetromino())
                                else:
                                    hold_piece, tetromino = copy.deepcopy(tetromino), copy.deepcopy(hold_piece)
                                shape_index = get_shape_index(tetromino) or 0
                                color_index = (shape_index + level - 1) % len(COLORS) + 1
                                rotation_state = 0
                                offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if event.y < 0 and 0 <= mx < GRID_WIDTH * BLOCK_SIZE and 0 <= my < GRID_HEIGHT * BLOCK_SIZE and not game_over and not game_won and not in_level_transition:
                    if valid_position(tetromino, [offset[0], offset[1] + 1], grid):
                        offset[1] += 1
                        mouse_dy = True

    while True:
        current_time = pygame.time.get_ticks()
        down_pressed = False
        mouse_dx = 0
        mouse_dy = False
        shake_intensity = (screen_shake * 2) if settings.get('screen_shake', True) else 0
        if screen_shake > 0:
            shake_x = random.randint(-shake_intensity, shake_intensity)
            shake_y = random.randint(-shake_intensity, shake_intensity)
        else:
            shake_x = 0
            shake_y = 0
        if mode == 'ultra' and not game_over and not game_won and current_time - start_time >= 180000:
            game_over = True
        if game_won:
            if heartbeat_playing and heartbeat_sound:
                heartbeat_sound.stop()
            if settings.get('use_custom_music', False):
                last_track_index = current_track_index
            pygame.mixer.music.stop()
            elapsed = current_time - start_time
            display_victory(score, elapsed, mode, lines_cleared_total, pieces_dropped, level)
            return None
        if game_over and not game_over_anim_active:
            if mode == 'training':
                game_over = False
                grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
            else:
                if heartbeat_playing and heartbeat_sound:
                    heartbeat_sound.stop()
                if game_over_sound:
                    game_over_sound.play()
                if settings.get('use_custom_music', False):
                    last_track_index = current_track_index
                pygame.mixer.music.stop()
                game_over_anim_active = True
                game_over_anim_start = current_time
        if game_over_anim_active:
            elapsed_anim = current_time - game_over_anim_start
            if elapsed_anim >= GAME_OVER_ANIM_DURATION:
                display_game_over(score, mode, lines_cleared_total, pieces_dropped, level, current_time - start_time, max_combo, t_spin_count)
                return None
        if in_level_transition:
            time_in_transition = current_time - transition_start_time
            if time_in_transition > TRANSITION_DURATION:
                in_level_transition = False
                grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                draw_3d_grid(grid_surface, grid_color, grid_opacity)
                for y in range(GRID_HEIGHT):
                    for x in range(GRID_WIDTH):
                        if grid[y][x] != 0:
                            grid[y][x] = random.randint(1, len(COLORS))
            elif current_time - last_flash_time > FLASH_INTERVAL:
                for y in range(GRID_HEIGHT):
                    for x in range(GRID_WIDTH):
                        if grid[y][x] != 0:
                            grid[y][x] = random.randint(1, len(COLORS))
                last_flash_time = current_time
                flash_count += 1
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                toggle_fullscreen()
            if event.type == MUSIC_END_EVENT:
                handle_music_end_event()
        process_keyboard_events(events, current_time)
        process_controller_events(events, current_time)
        process_mouse_events(events)
        if game_command in ('restart', 'menu'):
            return None
        if game_command == 'skip':
            skip_current_track()
            game_command = None
        if left_pressed or right_pressed:
            time_since_last_move = current_time - last_horizontal_move
            required_delay = fast_move_interval if time_since_last_move > move_interval else move_interval
            if time_since_last_move >= required_delay:
                direction = -1 if left_pressed else 1
                new_x = offset[0] + direction
                if valid_position(tetromino, [new_x, offset[1]], grid):
                    offset[0] = new_x
                    if lock_delay_active and lock_delay_resets < MAX_LOCK_DELAY_RESETS:
                        lock_delay_start = current_time
                        lock_delay_resets += 1
                last_horizontal_move = current_time
        current_fall_speed = 50 if fast_fall else fall_speed
        if current_time - last_fall_time > current_fall_speed:
            can_fall = valid_position(tetromino, [offset[0], offset[1] + 1], grid)
            if can_fall:
                if lock_delay_active:
                    lock_delay_active = False
                    lock_delay_resets = 0
                offset[1] += 1
            elif fast_fall:
                if check_game_over(grid):
                    game_over = True
                else:
                    original_grid = [row[:] for row in grid]
                    place_tetromino(tetromino, offset, grid, color_index)
                    hold_used = False
                    if is_t_spin(tetromino, offset, grid):
                        score += 400 * level
                        t_spin_count += 1
                    full_ys = [y for y in range(GRID_HEIGHT) if all(grid[y])]
                    cleared_colors = {}
                    if full_ys:
                        for y in full_ys:
                            cleared_colors[y] = [grid[y][x] for x in range(GRID_WIDTH)]
                    grid, lines_cleared = clear_lines(grid)
                    if full_ys:
                        clearing_lines = full_ys
                        clear_anim_start = current_time
                        for y in full_ys:
                            for x in range(GRID_WIDTH):
                                ci = cleared_colors[y][x]
                                explosion_particles.append(Explosion(x * BLOCK_SIZE + BLOCK_SIZE // 2, y * BLOCK_SIZE + BLOCK_SIZE // 2, COLORS[ci - 1], particle_count=8, max_speed=8, duration=40))
                    if lines_cleared == 4:
                        is_tetris = True
                        tetris_last_flash = current_time
                    new_level = lines_cleared_total // 10 + 1
                    if new_level > level:
                        level = new_level
                        fall_speed = max(50, int(base_fall_speed * (0.85 ** (level - 1))))
                        in_level_transition = True
                        transition_start_time = current_time
                        last_flash_time = current_time
                        flash_count = 0
                    tetromino = next_pieces.pop(0)
                    shape_index = get_shape_index(tetromino) or 0
                    color_index = (shape_index + level - 1) % len(COLORS) + 1
                    rotation_state = 0
                    next_pieces.append(tetromino_bag.get_next_tetromino())
                    offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
            elif not lock_delay_active:
                lock_delay_active = True
                lock_delay_start = current_time
            elif current_time - lock_delay_start >= LOCK_DELAY_TIME:
                if check_game_over(grid):
                    game_over = True
                else:
                    original_grid = [row[:] for row in grid]
                    place_tetromino(tetromino, offset, grid, color_index)
                    hold_used = False
                    if is_t_spin(tetromino, offset, grid):
                        score += 400 * level
                        t_spin_count += 1
                    full_ys = [y for y in range(GRID_HEIGHT) if all(grid[y])]
                    cleared_colors = {}
                    if full_ys:
                        for y in full_ys:
                            cleared_colors[y] = [grid[y][x] for x in range(GRID_WIDTH)]
                    grid, lines_cleared = clear_lines(grid)
                    if full_ys:
                        clearing_lines = full_ys
                        clear_anim_start = current_time
                        for y in full_ys:
                            for x in range(GRID_WIDTH):
                                ci = cleared_colors[y][x]
                                explosion_particles.append(Explosion(x * BLOCK_SIZE + BLOCK_SIZE // 2, y * BLOCK_SIZE + BLOCK_SIZE // 2, COLORS[ci - 1], particle_count=8, max_speed=8, duration=40))
                    if lines_cleared == 4:
                        is_tetris = True
                        tetris_last_flash = current_time
                    new_level = lines_cleared_total // 10 + 1
                    if new_level > level:
                        level = new_level
                        fall_speed = max(50, int(base_fall_speed * (0.85 ** (level - 1))))
                        in_level_transition = True
                        transition_start_time = current_time
                        last_flash_time = current_time
                        flash_count = 0
                    tetromino = next_pieces.pop(0)
                    shape_index = get_shape_index(tetromino) or 0
                    color_index = (shape_index + level - 1) % len(COLORS) + 1
                    rotation_state = 0
                    next_pieces.append(tetromino_bag.get_next_tetromino())
                    offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
                lock_delay_active = False
                lock_delay_resets = 0
            last_fall_time = current_time
        if effect_name != 'none' and (left_pressed or right_pressed or fast_fall or down_pressed or mouse_dx or mouse_dy):
            density_mult = {'low': 0.4, 'medium': 1.0, 'high': 2.0}
            num_particles = max(1, int(random.randint(5, 8) * density_mult.get(settings.get('particle_density', 'medium'), 1.0)))
            spawn_offset = 15
            for _ in range(num_particles):
                if left_pressed or mouse_dx == -1:
                    direction = 'left'
                    spawn_x = (offset[0] - 1) * BLOCK_SIZE + random.randint(-spawn_offset, 0)
                    spawn_y = (offset[1] + random.uniform(0.2, 0.8) * len(tetromino)) * BLOCK_SIZE
                elif right_pressed or mouse_dx == 1:
                    direction = 'right'
                    spawn_x = (offset[0] + len(tetromino[0])) * BLOCK_SIZE + random.randint(0, spawn_offset)
                    spawn_y = (offset[1] + random.uniform(0.2, 0.8) * len(tetromino)) * BLOCK_SIZE
                else:
                    direction = 'down'
                    spawn_x = (offset[0] + random.uniform(0.2, 0.8) * len(tetromino[0])) * BLOCK_SIZE
                    spawn_y = (offset[1] + len(tetromino)) * BLOCK_SIZE - spawn_offset
                if effect_name == 'wind':
                    trail_particles.append(WindParticle(spawn_x, spawn_y, direction))
                elif effect_name == 'water':
                    trail_particles.append(WaterParticle(spawn_x, spawn_y, direction))
                elif effect_name == 'ice':
                    trail_particles.append(IceParticle(spawn_x, spawn_y, direction))
                elif effect_name == 'flicker':
                    trail_particles.append(FlickerParticle(spawn_x, spawn_y, direction))
                elif effect_name == 'matrix':
                    trail_particles.append(MatrixParticle(spawn_x, spawn_y, direction))
                else:
                    trail_particles.append(TrailParticle(spawn_x, spawn_y, direction))
        wind_force = (-4 if left_pressed else (4 if right_pressed else 0), 5 if fast_fall else 0)
        for particle in trail_particles[:]:
            particle.update(wind_force, screen)
            if particle.age >= particle.max_age:
                trail_particles.remove(particle)
        for particle in dust_particles[:]:
            particle.update()
            if particle.age >= particle.max_age:
                dust_particles.remove(particle)
        for explosion in explosion_particles[:]:
            explosion.update()
            if explosion.lifetime <= 0:
                explosion_particles.remove(explosion)
        screen_shake = max(0, screen_shake - 1)
        if is_danger_zone_active(grid):
            if heartbeat_sound and not heartbeat_playing:
                heartbeat_sound.play(-1)
                heartbeat_playing = True
        elif heartbeat_playing:
            if heartbeat_sound:
                heartbeat_sound.stop()
            heartbeat_playing = False
        screen.fill(BLACK)
        draw_background(settings.get('background', 'auto'), level)
        if not in_level_transition:
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if grid[y][x]:
                        draw_3d_block(screen, COLORS[grid[y][x] - 1], x * BLOCK_SIZE + shake_x, y * BLOCK_SIZE + shake_y, BLOCK_SIZE, level)
            for cy, row in enumerate(tetromino):
                for cx, cell in enumerate(row):
                    if cell:
                        draw_3d_block(screen, COLORS[color_index - 1], (offset[0] + cx) * BLOCK_SIZE + shake_x, (offset[1] + cy) * BLOCK_SIZE + shake_y, BLOCK_SIZE, level)
            screen.blit(grid_surface, (shake_x, shake_y))
            if settings.get('ghost_piece', True):
                draw_ghost_piece(tetromino, offset, grid, COLORS[color_index - 1], level)
            for explosion in explosion_particles:
                explosion.draw(screen, (shake_x, shake_y))
            for trail in trail_particles:
                trail.draw(screen)
            for particle in dust_particles:
                particle.draw(screen)
        else:
            time_in_transition = current_time - transition_start_time
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if grid[y][x]:
                        draw_3d_block(screen, COLORS[grid[y][x] - 1], x * BLOCK_SIZE + shake_x, y * BLOCK_SIZE + shake_y, BLOCK_SIZE, level)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            if level % 4 == 0 and time_in_transition < 800:
                face_pulse = max(0.3, 1.0 - time_in_transition / 800)
                draw_evil_face(screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30, face_pulse)
            if time_in_transition > 400:
                level_text = tetris_font_large.render(f'LEVEL {level}!', True, random.choice(COLORS))
                level_shake_x = random.randint(-10, 10)
                level_shake_y = random.randint(-10, 10)
                screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2 + level_shake_x, SCREEN_HEIGHT // 2 - level_text.get_height() // 2 + level_shake_y))
        if clearing_lines:
            if pygame.time.get_ticks() - clear_anim_start > CLEAR_ANIM_DURATION:
                clearing_lines = []
        if game_over_anim_active:
            elapsed_anim = current_time - game_over_anim_start
            progress = elapsed_anim / GAME_OVER_ANIM_DURATION
            pulse = int(80 + 80 * math.sin(progress * math.pi * 6))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((pulse, 0, 0, min(160, int(progress * 200))))
            screen.blit(overlay, (0, 0))
            if elapsed_anim > GAME_OVER_ANIM_DURATION * 0.5:
                go_text = tetris_font_large.render('GAME OVER', True, (pulse, pulse, 0))
                screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2 + random.randint(-5, 5), SCREEN_HEIGHT // 3 - go_text.get_height() // 2 + random.randint(-5, 5)))
        elapsed_ms = current_time - start_time
        if mode in ('sprint', 'ultra') and not game_over_anim_active and not in_level_transition:
            seconds = elapsed_ms // 1000
            minutes = seconds // 60
            secs = seconds % 60
            time_str = f'{minutes}:{secs:02d}'
            timer_big = tetris_font_large.render(time_str, True, YELLOW)
            screen.blit(timer_big, (SCREEN_WIDTH // 2 - timer_big.get_width() // 2 + shake_x, 10 + shake_y))
        draw_subwindow(score, next_pieces, level, pieces_dropped, lines_cleared_total, is_tetris, tetris_last_flash, combo_count=combo_count, back_to_back_active=back_to_back_active, mode=mode, elapsed_ms=elapsed_ms, tetris_flash_time=tetris_flash_time)
        pygame.display.flip()
        clock.tick(60)


def help_menu():
    scroll = 0
    line_h = 18
    left_margin = 15
    text_width = SCREEN_WIDTH - left_margin - 20
    basic_mode = False
    col_sub = (100, 200, 255)
    col_body = WHITE
    col_head = (255, 220, 80)

    def add_section(head, body_lines):
        out = [('head', head)]
        for b in body_lines:
            out.append(('body', b))
        out.append(('spacer', ''))
        return out

    sections = []
    sections += add_section('CONTROLS  (current keybinds)', [
        f'Left: {pygame.key.name(settings["controls"]["left"]).upper()}    Right: {pygame.key.name(settings["controls"]["right"]).upper()}',
        f'Soft Drop: {pygame.key.name(settings["controls"]["down"]).upper()}    Hard Drop: {pygame.key.name(settings["controls"]["hard_drop"]).upper()}',
        f'Rotate: {pygame.key.name(settings["controls"]["rotate"]).upper()}    Hold: {pygame.key.name(settings["controls"]["hold"]).upper()}',
        f'Pause: {pygame.key.name(settings["controls"]["pause"]).upper()}',
        'Place piece instantly at lock position.',
        'Hold saves current piece (once per drop).',
        '',
        'Controller: left, right, down, rotate,',
        'hard_drop, hold, pause, skip_track.',
        'Menu nav: up, down, select, back (D-pad).',
        '',
        'Mouse: Hover piece left/right over board,',
        'Left-click: Hard Drop,  Right-click: Rotate,',
        'Middle-click: Hold,  Scroll Wheel: Soft Drop.',
    ])
    sections += add_section('GAME MODES', [
        'Marathon: Start level 1, level up every 10',
        'lines. Game over when blocks reach the top.',
        'Endless - score as high as possible!',
        '',
        'Sprint: Clear exactly 40 lines as fast as',
        'possible. Timer stops on completion.',
        '',
        'Ultra: Score as many points as possible in',
        '3 minutes. Timer counts down.',
        '',
        'Training: No game over. Topping out clears',
        'the board. Press H to delete bottom row.',
    ])
    sections += add_section('GAMEPLAY MECHANICS', [
        '7-Bag: All 7 pieces appear once before any',
        'piece repeats. Fair random distribution.',
        '',
        'Next Queue: 5 forthcoming pieces shown on',
        'the right side panel.',
        '',
        'Hold: Store current piece for later (once',
        'per drop). Press hold key to swap.',
        '',
        'SRS Wall Kicks: Rotating near walls/floor',
        'kicks piece into valid positions using',
        'standard SRS kick tables (JLSTZ + I).',
        '',
        'Lock Delay: 500ms before piece locks.',
        'Each move/rotate resets timer (max 15).',
        '',
        'DAS: Delay before held direction repeats.',
        'ARR: Speed of auto-repeat once started.',
        '',
        'Ghost Piece: Semi-transparent preview of',
        'where the active piece will land.',
        '',
        'T-Spin: 3-corner rule - T piece must have',
        '3 of 4 diagonals occupied on lock.',
        'Awards +400 x level bonus.',
        '',
        'Gravity Multiplier: Scales fall speed',
        'from 0.5x to 5.0x (in Options).',
    ])
    sections += add_section('SCORING', [
        'Single (1 line):  100 x level',
        'Double (2 lines):  300 x level',
        'Triple (3 lines):  500 x level',
        'Tetris (4 lines):  800 x level',
        '',
        'Combo: Consecutive clears add',
        '+50 x combo x level x lines_cleared.',
        '',
        'Back-to-Back: Two Tetrises in a row =',
        '1.5x bonus on the second one.',
        '',
        'All Clear: Emptying every cell awards',
        '+1200 x level.',
        '',
        'T-Spin Bonus: +400 x level on lock.',
        '',
        'Soft Drop: +1 per row.',
        'Hard Drop: +2 per row.',
    ])
    sections += add_section('DIFFICULTY & SPEED', [
        'Easy: 1500ms    Normal: 1000ms',
        'Hard: 600ms    Very Hard: 400ms',
        'Master: lvl 15 start, 200ms base',
        '',
        'Speed formula: base x 0.85^(level-1)',
        'Minimum: 50ms (~level 22+).',
        'Gravity multiplier scales base speed.',
    ])
    sections += add_section('VISUAL EFFECTS', [
        'Flame: Orange/red particles trail.',
        'Wind: Light blue directional streaks.',
        'Water: Blue droplets on movement.',
        'Ice: Cyan-white crystals, sparkle.',
        'Flicker: Ghostly white flickering.',
        'Matrix: Green digital rain style.',
        'None: No trail particles.',
        '',
        'Density: Low (0.4x), Medium (1x),',
        'High (2x) particle count.',
    ])
    sections += add_section('THEMES', [
        'Default / Retro / Dark / Pastel',
        'Protanopia / Deuteranopia / Tritanopia',
        'Colorblind palettes adjust RGB for',
        'protanopia, deuteranopia, tritanopia.',
    ])
    sections += add_section('BOARD BACKGROUNDS', [
        'Auto: Unique procedural background per',
        'level (10+ patterns, endless colors).',
        'None / Stars / Gradient / Checker',
        'Waves / Aurora',
    ])
    sections += add_section('HIGH SCORES', [
        'Each mode tracks its own high score.',
        'Saved to high_score.json as JSON dict.',
        'Enter 3-letter initials on new record.',
        'Displayed in the right side panel.',
    ])
    sections += add_section('OTHER FEATURES', [
        'Screen Shake: Rumble on line clears.',
        'Grid Lines: Toggle overlay on/off.',
        'Grid Opacity: Adjust line visibility.',
        'Line Clear: White flash + pulse fade.',
        'Game Over: 1.2s red pulse + text.',
        'Pause: Dimmed background overlay.',
        'Level Up: Random-color flash transition.',
        'Danger Zone: Top 4 rows = heartbeat SFX.',
        'Music: Toggle on/off or custom folder.',
        'Fullscreen: F4 (safe SCALED mode).',
        'Fade transitions between all menus.',
    ])
    sections += add_section('TIPS', [
        'Hold bad pieces to bail out.',
        'Watch the 5-piece queue to plan ahead.',
        'Tuck T pieces into gaps for T-spin.',
        'Back-to-Back Tetris = massive score.',
        'Lower DAS = snappier movement.',
        'Master mode starts fast - be ready!',
        'Use Training mode to practice setups.',
    ])
    sections += add_section('CREDITS', [
        'TetraFusion 2.1',
        'Created by drDOOM69GAMING',
        'Built with Python 3 + Pygame',
        '',
        'Thank you for playing!',
    ])

    flat = []
    for sec in sections:
        flat.append(sec)
    total_h = sum(line_h if t != 'spacer' else 8 for t, _ in flat) + 20
    visible_h = SCREEN_HEIGHT - 80
    max_scroll = max(0, total_h - visible_h)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll = max(0, scroll - line_h * 4)
                elif event.button == 5:
                    scroll = min(max_scroll, scroll + line_h * 4)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4:
                    toggle_fullscreen()
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    return None
                if event.key == pygame.K_UP:
                    scroll = max(0, scroll - line_h * 4)
                if event.key == pygame.K_DOWN:
                    scroll = min(max_scroll, scroll + line_h * 4)
                if event.key == pygame.K_TAB:
                    basic_mode = not basic_mode

        screen.fill(BLACK)
        if basic_mode:
            title_surf = tetris_font_large.render('HELP MANUAL  [TAB=TEXT]', True, col_sub)
        else:
            title_surf = tetris_font_large.render('HELP MANUAL  [TAB=GRAPHIC]', True, col_sub)
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 5))

        clip_rect = pygame.Rect(0, 40, SCREEN_WIDTH, visible_h)
        screen.set_clip(clip_rect)
        y = 40
        for typ, text in flat:
            if typ == 'spacer':
                y += 8
                continue
            if typ == 'head':
                if basic_mode:
                    head_surf = pygame.font.Font(None, 22).render('== ' + text + ' ==', True, col_sub)
                    y += 4
                    screen.blit(head_surf, (left_margin, y - scroll))
                    y += 22
                else:
                    head_surf = tetris_font_small.render(text, True, col_sub)
                    y += 4
                    screen.blit(head_surf, (left_margin, y - scroll))
                    y += line_h
                    underline = pygame.Surface((text_width, 2))
                    underline.fill((col_sub[0] // 2, col_sub[1] // 2, col_sub[2] // 2))
                    screen.blit(underline, (left_margin, y - scroll - 2))
                continue
            if typ == 'body':
                if basic_mode:
                    body_surf = pygame.font.Font(None, 20).render(text, True, col_body if text else (40, 40, 40))
                    screen.blit(body_surf, (left_margin + 4, y - scroll))
                    y += 20
                else:
                    surf = tetris_font_smaller.render(text, True, col_body if text else (40, 40, 40))
                    screen.blit(surf, (left_margin + 4, y - scroll))
                    y += line_h
        screen.set_clip(None)

        bar_left = SCREEN_WIDTH - 10
        bar_w = 6
        if max_scroll > 0:
            bar_h = max(20, int(visible_h * visible_h / total_h))
            bar_y = 40 + int(scroll / max_scroll * (visible_h - bar_h))
            pygame.draw.rect(screen, (60, 60, 60), (bar_left, 40, bar_w, visible_h))
            pygame.draw.rect(screen, (180, 180, 180), (bar_left, bar_y, bar_w, bar_h))

        mode_label = 'TEXT' if basic_mode else 'GRAPHIC'
        hint = tetris_font_tiny.render(f'ESC/ENTER to close  |  TAB switches to {mode_label} mode  |  Arrows/mouse to scroll', True, (120, 120, 120))
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 20))
        pygame.display.flip()
        clock.tick(60)


def main():
    global settings
    settings = load_settings()
    if settings.get('music_enabled', True):
        if settings.get('use_custom_music', False):
            play_custom_music(settings)
        else:
            try:
                pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f'Error loading default background music: {e}')
    while True:
        mode = main_menu()
        hold_piece = None
        hold_used = False
        while True:
            run_game(mode)
            if game_command == 'menu':
                break


if __name__ == '__main__':
    main()
