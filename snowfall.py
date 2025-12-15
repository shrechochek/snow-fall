#!/usr/bin/env python3
# pip install pyobjc
"""
Расширенная погодная система (Python / PyObjC).
Включает: снег, дождь, молнии (сегменты сверху->вниз), tornado, microburst, dust devil,
ash fall, aurora, ball lightning (плавное движение), meteors, sandstorm, leaves, insects swarm.
Управление эффектами через флаги в конфиге.
"""
import time
import random
import math

from AppKit import (
    NSApplication, NSWindow, NSBackingStoreBuffered,
    NSWindowStyleMaskBorderless, NSColor, NSView,
    NSScreenSaverWindowLevel, NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSScreen
)
from Quartz import (
    CALayer, CATransform3DMakeRotation,
    CGRectMake, CGPointMake, CATransaction, CABasicAnimation
)
from Foundation import NSNull
from PyObjCTools import AppHelper

# ==========================
# ========== CONFIG ========
# ==========================

# === GENERAL VISUAL SETTINGS ===
SCREEN_MARGIN = 200           # extra space around screen for effects
PARTICLE_FADE_DISTANCE = 0   # distance from screen edge where particles fade
GLOBAL_OPACITY_MULTIPLIER = 1.0  # global opacity adjustment
ENABLE_PARTICLE_BLENDING = True   # enable particle transparency effects
MAX_FPS = 60                  # target frame rate

# === PERFORMANCE SETTINGS ===
MAX_PARTICLES_TOTAL = 2000    # maximum total particles across all effects
ENABLE_CULLING = True         # remove off-screen particles
UPDATE_BATCH_SIZE = 50        # particles updated per frame batch
LOW_PERFORMANCE_MODE = False  # reduce particle counts automatically
# Base enables
ENABLE_SNOW = False
ENABLE_RAIN = True
ENABLE_LIGHTNING = False

ENABLE_FOG = False
ENABLE_GUSTS = False
ENABLE_LEAVES = False

ENABLE_HAIL = False
ENABLE_FLASH = False

ENABLE_AURORA = False
ENABLE_BALL_LIGHTNING = False
ENABLE_METEORS = False
ENABLE_SANDSTORM = False

# New requested effects:
ENABLE_MICROBURST = False    # (7) microburst event
ENABLE_DUST_DEVIL = False    # (8) dust devil / small vortex
ENABLE_ASH = False           # (11) ash fall
ENABLE_INSECTS = False       # (15) insects swarm
ENABLE_TORNADO = False       # tornado: strong lateral wind + debris

# WIND general
WIND_BASE = 600.0            # px/sec (positive => right)
WIND_WAVE_AMPLITUDE = 40.0
WIND_WAVE_FREQ = 0.08

# Gusts
GUST_MIN_INTERVAL = 4.0
GUST_MAX_INTERVAL = 12.0
GUST_MIN_DURATION = 0.8
GUST_MAX_DURATION = 2.5
GUST_MIN_STRENGTH = 40.0
GUST_MAX_STRENGTH = 220.0

# Snow - Fine tuning
SNOW_COUNT = 60
SNOW_SPEED = (30, 120)
SNOW_SIZE = (2, 6)          # particle size range
SNOW_OPACITY = (0.8, 1.0)   # opacity range
SNOW_ROTATION_SPEED = (10, 40)  # degrees per second
SNOW_JITTER_STRENGTH = 15   # horizontal wind variation

# Rain - Fine tuning
RAIN_COUNT = 220
RAIN_SPEED = (500, 1300)
RAIN_WIDTH = (0.8, 2.2)     # raindrop width range
RAIN_LENGTH = (12, 35)      # raindrop length range
RAIN_OPACITY = (0.6, 0.9)   # opacity range
RAIN_WIND_INFLUENCE = 0.8   # how much wind affects rain direction (0-1)
RAIN_TRAIL_LENGTH = 3       # visual trail effect

# Hail - Fine tuning
HAIL_COUNT = 60
HAIL_SPEED = (800, 1800)
HAIL_SIZE = (3, 8)          # hailstone radius range
HAIL_OPACITY = (0.85, 1.0)  # opacity range
HAIL_BOUNCE_COEFF = 0.45
HAIL_MIN_BOUNCE_V = 180.0
HAIL_MAX_BOUNCES = 5        # maximum bounce count before disappearing
HAIL_GROUND_FADE_TIME = 2.0 # seconds to fade after hitting ground

# Leaves - Fine tuning
LEAF_COUNT = 40
LEAF_SPEED = (60, 220)
LEAF_WIDTH = (4, 14)        # leaf width range
LEAF_LENGTH_RATIO = (0.7, 1.4)  # length to width ratio
LEAF_SWAY = 80.0
LEAF_ROT_SPEED = 120.0
LEAF_COLOR_VARIATION = True  # enable autumn color variations
LEAF_FALL_PATTERN = 'sway'   # 'sway', 'twirl', 'drift'
LEAF_WIND_SENSITIVITY = 0.6  # how responsive to wind

# Fog - Fine tuning
FOG_PATCHES = 6
FOG_WIDTH_RATIO = (0.8, 1.4)    # width relative to screen
FOG_HEIGHT_RATIO = (0.15, 0.5)  # height relative to screen
FOG_OPACITY_MIN = 0.035
FOG_OPACITY_MAX = 0.14
FOG_DRIFT_SPEED_MIN = 5.0
FOG_DRIFT_SPEED_MAX = 30.0
FOG_COLOR_GRAY = (0.75, 0.9)    # gray tone range
FOG_EDGE_SOFTNESS = 0.02        # corner radius factor
FOG_OPACITY_PULSE = True        # enable breathing effect

# Lightning - Fine tuning
LIGHTNING_MIN_DELAY = 2.0
LIGHTNING_MAX_DELAY = 4.0
LIGHTNING_LIFETIME = 0.18
LIGHTNING_APPEAR_DURATION = 0.12
LIGHTNING_SEGMENT_LENGTH = (8, 50)  # segment length range
LIGHTNING_BRANCH_CHANCE = 0.28      # probability of branching
LIGHTNING_MAX_DEPTH = 3              # maximum branch depth
LIGHTNING_CORE_THICKNESS = (1.5, 3.0)  # core thickness range
LIGHTNING_GLOW_FACTOR = 2.8          # glow to core ratio
LIGHTNING_COLOR = 'white'            # 'white', 'blue', 'purple'

# Aurora - Fine tuning
AURORA_BANDS = 3
AURORA_BAND_HEIGHT = (0.04, 0.15)  # band height range (relative to screen)
AURORA_SPEED = 10.0
AURORA_COLOR_FREQ = 0.12
AURORA_OPACITY_RANGE = (0.0, 0.35)  # opacity animation range
AURORA_COLOR_SCHEME = 'green_blue'  # 'green', 'green_blue', 'purple', 'rainbow'
AURORA_WAVE_AMPLITUDE = 0.3         # wave motion intensity
AURORA_HORIZONTAL_DRIFT = True      # enable slow horizontal movement

# Ball lightning - Fine tuning
BALL_CHANCE_ON_LIGHTNING = 1
BALL_LIFE = 1.6
BALL_COUNT_MAX = 6
BALL_SIZE_RANGE = (6, 22)       # ball radius range
BALL_SPEED_RANGE = (30, 90)     # movement speed range
BALL_COLOR = 'golden'           # 'golden', 'blue', 'purple', 'white'
BALL_GLOW_INTENSITY = 1.2       # glow effect multiplier
BALL_TRAIL_LENGTH = 8           # visual trail segments
BALL_WIND_INFLUENCE = 0.3       # how much wind affects movement

# Meteors - Fine tuning
# METEOR_CHANCE_PER_SEC = 0.4
METEOR_CHANCE_PER_SEC = 1
METEOR_SPEED = (1400, 3000)
METEOR_LENGTH = (60, 180)
METEOR_WIDTH = (1.5, 3.5)       # meteor trail width
METEOR_COLOR = 'fire'           # 'fire', 'white', 'blue', 'green'
METEOR_SPARK_COUNT = 3          # trailing sparks
METEOR_FADE_TIME = 0.8          # seconds to fade after disappearing
METEOR_TRAIL_OPACITY = 0.7      # trail opacity
METEOR_ANGLE_RANGE = (15, 55)   # entry angle range

# Sandstorm - Fine tuning
SAND_PARTICLES = 300
SAND_SPEED = (200, 600)
SAND_SIZE = (1.0, 2.5)         # particle size range
SAND_LENGTH = (2.0, 7.0)       # particle length range
SAND_OPACITY = 0.15
SAND_COLOR_VARIATION = True    # enable color variations
SAND_WIND_STRENGTH = 0.1       # wind influence multiplier
SAND_VERTICAL_DRIFT = True     # enable slight vertical movement
SAND_TRAIL_EFFECT = False      # enable motion blur trail

# Dust devil - Fine tuning
DUST_DEVILS_MAX = 3
DUST_DEVIL_LIFE = 18.0
DUST_DEVIL_RADIUS = 80.0
DUST_DEVIL_PARTICLES = 150
DUST_DEVIL_HEIGHT_FACTOR = 1.2    # how much above screen height particles go
DUST_DEVIL_ROTATION_SPEED = (0.8, 2.8)  # particle rotation speed range
DUST_DEVIL_VERTICAL_SPEED = (20, 60)    # upward movement speed
DUST_DEVIL_COLOR_SATURATION = 0.7       # color intensity
DUST_DEVIL_PARTICLE_LIFETIME = True     # particles have individual lifetimes

# Microburst - Fine tuning
MICROBURST_CHANCE = 0.02    # per second
MICROBURST_STRENGTH = 900.0 # strong downward + radial push
MICROBURST_DURATION = 1.2   # seconds
MICROBURST_RADIUS = 250     # influence radius
MICROBURST_VISUAL_SIZE = (400, 200)  # visual oval dimensions
MICROBURST_VISUAL_OPACITY = 0.4      # visual effect opacity
MICROBURST_VERTICAL_PUSH = 0.03      # radial horizontal push factor
MICROBURST_GROUND_DARKNESS = True    # darken ground effect

# Ash - Fine tuning
ASH_COUNT = 120
ASH_SPEED = (20, 80)        # slow small flakes
ASH_SIZE = (1.0, 4.0)       # particle size range
ASH_OPACITY_RANGE = (0.3, 0.7)  # opacity variation
ASH_COLOR = 'dark_gray'     # 'dark_gray', 'black', 'brown'
ASH_WIND_INFLUENCE = 0.2    # how much wind affects ash
ASH_SETTLE_TIME = 0.0       # time before particles start falling (0 = immediate)
ASH_GROUND_ACCUMULATION = False  # enable ground accumulation effect

# Insects - Fine tuning
INSECT_COUNT = 120
INSECT_SPEED = (20, 140)
INSECT_SIZE = (1.0, 2.4)     # insect size range
INSECT_SWARM_RADIUS = 120.0
INSECT_SWARM_COUNT = 6       # number of swarm centers
INSECT_COLOR = 'yellow'      # 'yellow', 'black', 'green', 'brown'
INSECT_MOVEMENT_STYLE = 'swarm'  # 'swarm', 'random', 'pattern'
INSECT_SWARM_COHESION = 0.06     # how strongly insects stick to swarm
INSECT_LIGHT_REACTION = False     # react to lightning flashes

# Tornado - Fine tuning
TORNADO_CHANCE = 0.005    # per second
TORNADO_LIFE = 18.0
TORNADO_RADIUS = 160.0
TORNADO_PARTICLES = 2000    # total particles (dust + debris)
TORNADO_DEBRIS_RATIO = 0.3 # percentage of debris vs dust particles
TORNADO_DESCENT_SPEED = 1.0 # how fast it descends (relative to life)
TORNADO_DRIFT_AMPLITUDE = 80.0  # side-to-side drift intensity
TORNADO_VORTEX_STRENGTH = 250.0  # force applied to other particles
TORNADO_DEBRIS_SIZE = (8, 28)    # debris size range
TORNADO_DUST_SIZE = (1.5, 5.0)   # dust particle size range
TORNADO_ROTATION_SPEED = (10.0, 10.0)  # particle rotation speed range
DEBRIS_TYPES = ['branch', 'rock']     # available debris object types

MAX_DT = 0.2

# ==========================
# ========== HELPERS =======
# ==========================
def no_implicit(layer):
    layer.setActions_({
        'position': NSNull.null(),
        'transform': NSNull.null(),
        'bounds': NSNull.null(),
        'opacity': NSNull.null()
    })

def rotate(layer, degrees):
    rad = math.radians(degrees)
    layer.setTransform_(CATransform3DMakeRotation(rad, 0, 0, 1))

def lerp(a, b, t):
    return a + (b - a) * t

# ============================
# Particle types
# ============================
class Particle:
    def __init__(self, layer, speed, jitter, radius=None, width=None, length=None):
        self.layer = layer
        self.speed = float(speed)
        self.jitter = float(jitter)
        self.radius = radius
        self.width = width
        self.length = length if length is not None else 0
        self.x = float(layer.position().x)
        self.y = float(layer.position().y)
        self.prev_x = self.x
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-60, 60)

    def respawn_top(self, screen_w, screen_h, radius_override=None, width_override=None, length_override=None):
        CATransaction.begin()
        CATransaction.setDisableActions_(True)
        self.x = random.uniform(0, screen_w)
        self.y = screen_h + random.uniform(20, 200)
        self.layer.setPosition_(CGPointMake(self.x, self.y))
        self.prev_x = self.x
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-60, 60)
        if radius_override is not None and self.radius is not None:
            self.radius = radius_override
            self.layer.setBounds_(CGRectMake(0, 0, self.radius*2, self.radius*2))
            self.layer.setCornerRadius_(self.radius)
        if width_override is not None and self.width is not None:
            self.width = width_override
            self.layer.setBounds_(CGRectMake(0, 0, self.width, getattr(self, 'length', 30)))
        if length_override is not None:
            self.length = length_override
        CATransaction.commit()

class HailParticle:
    def __init__(self, layer, v_y):
        self.layer = layer
        self.v_y = v_y
        self.x = float(layer.position().x)
        self.y = float(layer.position().y)
        self.radius = (layer.bounds().size.width / 2.0) if layer.bounds() is not None else 3.0

    def respawn(self, screen_w, screen_h):
        CATransaction.begin()
        CATransaction.setDisableActions_(True)
        self.x = random.uniform(0, screen_w)
        self.y = screen_h + random.uniform(10, 200)
        self.v_y = random.uniform(*HAIL_SPEED)
        self.layer.setPosition_(CGPointMake(self.x, self.y))
        CATransaction.commit()

# Tornado object with enhanced visualization and physics
class Tornado:
    def __init__(self, root, x, y, radius, life, screen_w, screen_h):
        self.root = root
        self.x = x
        self.y = y  # start from top of screen
        self.radius = radius
        self.life = life
        self.born = time.time()
        self.center_layer = CALayer.layer()
        self.center_layer.setBounds_(CGRectMake(0, 0, radius*2, radius*2))
        self.center_layer.setPosition_(CGPointMake(x, y))
        self.center_layer.setOpacity_(0.0)  # invisible center
        no_implicit(self.center_layer)
        self.particles = []  # all particles including debris and dust
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.drift_direction = random.choice([-1, 1])  # left or right drift

        # spawn mixed particles: some debris (branches/rocks), some dust
        total_particles = 200
        for i in range(total_particles):
            # decide if this is debris or dust
            is_debris = random.random() < 0.3  # 30% chance for debris

            if is_debris:
                # create debris (branches/rocks)
                typ = random.choice(DEBRIS_TYPES)
                size = random.uniform(8.0, 28.0)
                layer = CALayer.layer()
                layer.setBounds_(CGRectMake(0,0, size, size if typ=='rock' else size*0.6))
                layer.setCornerRadius_(3.0 if typ=='branch' else size/2.0)
                if typ == 'branch':
                    layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.55,0.38,0.18,1.0).CGColor())
                else:
                    layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.4,0.4,0.42,1.0).CGColor())
            else:
                # create dust particles like in dust devil
                size = random.uniform(1.5, 5.0)
                layer = CALayer.layer()
                layer.setBounds_(CGRectMake(0,0,size,size))
                layer.setCornerRadius_(size/2.0)
                # varied earth tones for dust
                r_color = random.uniform(0.65, 0.85)
                g_color = random.uniform(0.55, 0.75)
                b_color = random.uniform(0.35, 0.55)
                alpha = random.uniform(0.5, 0.9)
                layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(r_color, g_color, b_color, alpha).CGColor())

            # distribute around the tornado top (starts at top, descends downward)
            angle = random.uniform(0, 2*math.pi)
            r = random.uniform(10.0, radius * 1.5)
            # start particles at the top and let them fall down
            height_from_top = random.uniform(0, screen_h * 0.3)  # start within top 30% of screen
            sx = x + math.cos(angle) * r * random.uniform(0.3, 1.0)
            sy = height_from_top  # start from top, will fall down
            layer.setPosition_(CGPointMake(sx, sy))
            no_implicit(layer)
            root.addSublayer_(layer)

            self.particles.append({
                'layer': layer,
                'x': sx, 'y': sy,
                'theta': angle,
                'r': r,
                'cx': x, 'cy': y,
                'speed': random.uniform(1.5, 4.0),
                'fall_offset': height_from_top,  # how far it has fallen from top
                'vertical_speed': random.uniform(60.0, 180.0),  # downward movement speed
                'size': size,
                'is_debris': is_debris,
                'type': typ if is_debris else 'dust'
            })

    def apply_forces(self, dt, particles, sand_particles, rain_particles, hail_particles, leaf_particles, ash_particles, insect_particles):
        # Tornado starts at top and descends downward with side-to-side drift
        t = (time.time() - self.born) / self.life

        # tornado descends from top to bottom over its lifetime
        target_y = self.screen_h * t  # gradually move down from 0 to screen_h
        self.y = min(target_y, self.screen_h + self.radius)

        # side-to-side drift
        drift_speed = 80.0 * self.drift_direction * (0.5 + 0.5 * math.sin(t * 2.0))  # oscillating drift
        self.x += drift_speed * dt

        # wrap around screen edges
        if self.x > self.screen_w + self.radius:
            self.x = -self.radius
        elif self.x < -self.radius:
            self.x = self.screen_w + self.radius

        # animate all tornado particles like dust devil but with debris mixed in
        for p in self.particles:
            # increase theta for rotation (faster near center, varies by particle type)
            if p['is_debris']:
                rotation_speed = 3.0 + p['speed'] * 0.5  # debris rotates slower
            else:
                rotation_speed = 2.8 + p['speed'] * 0.9 + (1.0 - p['r']/self.radius) * 2.5

            p['theta'] += dt * rotation_speed

            # slowly reduce radius to create inward spiral, but with some variation
            spiral_in = dt * (12.0 * (1.0 + p['speed']*0.4))
            p['r'] = max(8.0, p['r'] - spiral_in)

            # add downward movement - particles fall as they spiral inward
            fall_boost = (1.0 - p['r']/self.radius) * 0.8  # slight variation in fall speed
            p['fall_offset'] += p['vertical_speed'] * dt * (0.9 + fall_boost)

            # calculate new position relative to current tornado center
            x = self.x + math.cos(p['theta']) * p['r']
            y = self.y + p['fall_offset']  # fall downward from tornado center

            # respawn particles that fall too far or go too far inward
            if p['fall_offset'] > self.screen_h * 1.2 or p['r'] < 12.0 or y > self.screen_h + 300:
                # respawn at top with new parameters
                p['theta'] = random.uniform(0, 2*math.pi)
                p['r'] = random.uniform(self.radius * 0.9, self.radius * 1.3)
                p['fall_offset'] = random.uniform(-self.screen_h * 0.1, self.screen_h * 0.05)
                p['vertical_speed'] = random.uniform(60.0, 160.0)
                x = self.x + math.cos(p['theta']) * p['r']
                y = self.y + p['fall_offset']

            p['x'] = x
            p['y'] = y
            p['layer'].setPosition_(CGPointMake(x, y))

        # apply tornado forces to other particle types with varying intensity
        all_particles = [
            (particles, 0.8, 'snow'),  # snow particles - stronger effect
            (sand_particles, 0.9, 'sand'),  # sand particles
            (rain_particles, 0.6, 'rain'),  # rain particles
            (hail_particles, 0.7, 'hail'),  # hail particles
            (leaf_particles, 0.5, 'leaf'),  # leaves
            (ash_particles, 1.0, 'ash'),  # ash - strongest effect
            (insect_particles, 0.4, 'insect')  # insects
        ]

        for particle_list, intensity, ptype in all_particles:
            for p in particle_list:
                if ptype == 'snow':
                    px, py = p.x, p.y
                elif ptype == 'sand':
                    px, py = p['x'], p['y']
                elif ptype == 'rain':
                    px, py = p.x, p.y
                elif ptype == 'hail':
                    px, py = p.x, p.y
                elif ptype == 'leaf':
                    px, py = p.x, p.y
                elif ptype == 'ash':
                    px, py = p['x'], p['y']
                elif ptype == 'insect':
                    px, py = p['x'], p['y']
                else:
                    continue

                dx = px - self.x
                dy = py - self.y
                dist = math.hypot(dx, dy)

                if dist < self.radius * 1.8 and dist > 5.0:
                    # apply rotational force
                    tx = -dy / dist
                    ty = dx / dist
                    force_strength = intensity * 250.0 * (1.0 - dist/(self.radius*1.8))

                    # apply forces based on particle type
                    if ptype == 'snow':
                        p.x += tx * force_strength * dt
                        p.y += ty * force_strength * dt * 0.4 - 80.0 * dt * intensity  # stronger upward lift
                    elif ptype == 'sand':
                        p['x'] += tx * force_strength * dt
                        p['y'] += ty * force_strength * dt * 0.4 - 60.0 * dt * intensity
                        p['layer'].setPosition_(CGPointMake(p['x'], p['y']))
                    elif ptype == 'rain':
                        p.x += tx * force_strength * dt
                        p.y += ty * force_strength * dt * 0.4 - 70.0 * dt * intensity
                        p.layer.setPosition_(CGPointMake(p.x, p.y))
                    elif ptype == 'hail':
                        p.x += tx * force_strength * dt
                        p.y += ty * force_strength * dt * 0.4 - 90.0 * dt * intensity
                        p.layer.setPosition_(CGPointMake(p.x, p.y))
                    elif ptype == 'leaf':
                        p.x += tx * force_strength * dt
                        p.y += ty * force_strength * dt * 0.4 - 65.0 * dt * intensity
                        p.layer.setPosition_(CGPointMake(p.x, p.y))
                    elif ptype == 'ash':
                        p['x'] += tx * force_strength * dt
                        p['y'] += ty * force_strength * dt * 0.4 - 50.0 * dt * intensity
                        p['layer'].setPosition_(CGPointMake(p['x'], p['y']))
                    elif ptype == 'insect':
                        p['x'] += tx * force_strength * dt
                        p['y'] += ty * force_strength * dt * 0.4 - 35.0 * dt * intensity
                        p['layer'].setPosition_(CGPointMake(p['x'], p['y']))

# ============================
# Lightning builder
# ============================
def create_lightning_segments(root_layer, start_x, start_y, total_height,
                              main_thickness=2.5, color=None,
                              angle_spread=25, length_min=10, length_max=60,
                              branch_chance=0.28, depth_limit=3,
                              base_distance=0.0):
    if color is None:
        color = NSColor.whiteColor()
    segments = []
    cx, cy = start_x, start_y
    angle = -90.0
    remaining = total_height
    traveled = 0.0
    attempts = 0
    while remaining > 0 and attempts < 1000:
        attempts += 1
        seg_len = random.uniform(length_min, length_max)
        if seg_len > remaining:
            seg_len = remaining
        angle += random.uniform(-angle_spread, angle_spread)
        rad = math.radians(angle)
        nx = cx + math.cos(rad) * seg_len
        ny = cy + math.sin(rad) * seg_len
        core_thickness = max(1.0, main_thickness * random.uniform(0.6, 1.2))
        glow_thickness = max(core_thickness * 2.5, core_thickness + 1.5)
        glow = CALayer.layer()
        glow.setBounds_(CGRectMake(0,0,glow_thickness, seg_len))
        glow.setAnchorPoint_(CGPointMake(0.5, 0.0))
        glow.setPosition_(CGPointMake(cx, cy))
        glow.setBackgroundColor_(color.CGColor())
        glow.setOpacity_(0.14 * random.uniform(0.7, 1.0))
        glow.setCornerRadius_(glow_thickness/2.0)
        glow.setTransform_(CATransform3DMakeRotation(rad + math.pi/2.0, 0,0,1))
        no_implicit(glow)
        segments.append({'layer': glow, 'distance': base_distance + traveled + seg_len * 0.5})
        core = CALayer.layer()
        core.setBounds_(CGRectMake(0,0, core_thickness, seg_len))
        core.setAnchorPoint_(CGPointMake(0.5, 0.0))
        core.setPosition_(CGPointMake(cx, cy))
        core.setBackgroundColor_(color.CGColor())
        core.setOpacity_(0.95 * random.uniform(0.8, 1.0))
        core.setCornerRadius_(core_thickness/2.0)
        core.setTransform_(CATransform3DMakeRotation(rad + math.pi/2.0, 0,0,1))
        no_implicit(core)
        segments.append({'layer': core, 'distance': base_distance + traveled + seg_len * 0.5})
        if random.random() < 0.12:
            flash = CALayer.layer()
            flash_t = max(0.5, core_thickness * 0.6)
            flash.setBounds_(CGRectMake(0,0, flash_t, seg_len))
            flash.setAnchorPoint_(CGPointMake(0.5, 0.0))
            flash.setPosition_(CGPointMake(cx, cy))
            flash.setBackgroundColor_(NSColor.whiteColor().CGColor())
            flash.setOpacity_(0.6 * random.uniform(0.5, 0.9))
            flash.setCornerRadius_(flash_t/2.0)
            flash.setTransform_(CATransform3DMakeRotation(rad + math.pi/2.0, 0,0,1))
            no_implicit(flash)
            segments.append({'layer': flash, 'distance': base_distance + traveled + seg_len * 0.5})
        if depth_limit > 0 and random.random() < branch_chance:
            tpos = random.uniform(0.25, 0.85)
            bx = cx + math.cos(rad) * seg_len * tpos
            by = cy + math.sin(rad) * seg_len * tpos
            branch_base_distance = base_distance + traveled + seg_len * tpos
            branch_height = remaining * random.uniform(0.25, 0.6)
            branch_segments = create_lightning_segments(
                root_layer, bx, by, branch_height,
                main_thickness=max(0.8, main_thickness * 0.6),
                color=color,
                angle_spread=angle_spread * 1.1,
                length_min=length_min * 0.6,
                length_max=length_max * 0.7,
                branch_chance=branch_chance * 0.6,
                depth_limit=depth_limit - 1,
                base_distance=branch_base_distance
            )
            if branch_segments:
                segments.extend(branch_segments)
        cx, cy = nx, ny
        remaining -= seg_len
        traveled += seg_len
    return segments

# ==========================
# ========== MAIN =========
# ==========================
def main():
    app = NSApplication.sharedApplication()
    screen = NSScreen.mainScreen().frame()
    W, H = screen.size.width, screen.size.height

    # window + root layer
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        screen, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
    )
    window.setOpaque_(False)
    window.setBackgroundColor_(NSColor.clearColor())
    window.setLevel_(NSScreenSaverWindowLevel)
    window.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces)
    window.setIgnoresMouseEvents_(True)

    view = NSView.alloc().initWithFrame_(screen)
    view.setWantsLayer_(True)
    view.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)
    root = view.layer()

    # flash overlay
    flash_layer = None
    if ENABLE_FLASH:
        flash_layer = CALayer.layer()
        flash_layer.setBounds_(CGRectMake(0,0, W, H))
        flash_layer.setPosition_(CGPointMake(W/2.0, H/2.0))
        flash_layer.setBackgroundColor_(NSColor.whiteColor().CGColor())
        flash_layer.setOpacity_(0.0)
        no_implicit(flash_layer)
        root.addSublayer_(flash_layer)


    snow_particles = []
    rain_particles = []
    hail_particles = []
    leaf_particles = []
    fog_patches = []
    active_lightnings = []
    aurora_bands = []
    ball_lightnings = []
    meteors = []
    sand_particles = []
    dust_devils = []
    ash_particles = []
    insect_particles = []
    tornadoes = []

    # init snow
    if ENABLE_SNOW:
        for _ in range(SNOW_COUNT):
            r = random.randint(3, 8)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0, 0, r*2, r*2))
            layer.setCornerRadius_(r)
            layer.setBackgroundColor_(NSColor.whiteColor().CGColor())
            sx = random.uniform(0, W)
            sy = random.uniform(0, H)
            layer.setPosition_(CGPointMake(sx, sy))
            no_implicit(layer)
            root.addSublayer_(layer)
            snow_particles.append(Particle(layer, random.uniform(*SNOW_SPEED), random.uniform(-20,20), radius=r))

    # init rain
    if ENABLE_RAIN:
        for _ in range(RAIN_COUNT):
            w = random.uniform(1.0, 2.5)
            l = random.uniform(15.0, 40.0)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0, 0, w, l))
            layer.setCornerRadius_(min(1.5, w/2.0))
            layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.7,0.8,1.0,1.0).CGColor())
            sx = random.uniform(0, W)
            sy = random.uniform(0, H)
            layer.setPosition_(CGPointMake(sx, sy))
            no_implicit(layer)
            root.addSublayer_(layer)
            p = Particle(layer, random.uniform(*RAIN_SPEED), random.uniform(-40,40), width=w)
            p.length = l
            rain_particles.append(p)

    # init hail
    if ENABLE_HAIL:
        for _ in range(HAIL_COUNT):
            sz = random.uniform(3.0, 7.0)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0, 0, sz*2, sz*2))
            layer.setCornerRadius_(sz)
            layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95,0.95,1.0,1.0).CGColor())
            sx = random.uniform(0, W)
            sy = random.uniform(0, H)
            layer.setPosition_(CGPointMake(sx, sy))
            no_implicit(layer)
            root.addSublayer_(layer)
            hp = HailParticle(layer, random.uniform(*HAIL_SPEED))
            hail_particles.append(hp)

    # init leaves
    if ENABLE_LEAVES:
        for _ in range(LEAF_COUNT):
            w = random.uniform(6.0, 16.0)
            l = w * random.uniform(0.8, 1.6)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0, 0, w, l))
            layer.setCornerRadius_(w/3.0)
            rcol = random.uniform(0.6, 1.0)
            gcol = random.uniform(0.2, 0.6)
            bcol = random.uniform(0.0, 0.2)
            layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(rcol,gcol,bcol,1.0).CGColor())
            sx = random.uniform(0, W)
            sy = random.uniform(0, H)
            layer.setPosition_(CGPointMake(sx, sy))
            no_implicit(layer)
            root.addSublayer_(layer)
            p = Particle(layer, random.uniform(*LEAF_SPEED), random.uniform(-LEAF_SWAY, LEAF_SWAY), width=w)
            p.length = l
            p.rot_speed = random.uniform(-LEAF_ROT_SPEED, LEAF_ROT_SPEED)
            leaf_particles.append(p)

    # fog
    if ENABLE_FOG:
        for i in range(FOG_PATCHES):
            fw = W * random.uniform(1.1, 1.6)
            fh = H * random.uniform(0.2, 0.6)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0,0,fw, fh))
            layer.setCornerRadius_(fw * 0.02)
            gray = random.uniform(0.8, 0.95)
            alpha = random.uniform(FOG_OPACITY_MIN, FOG_OPACITY_MAX)
            color = NSColor.colorWithCalibratedRed_green_blue_alpha_(gray, gray, gray, 1.0)
            layer.setBackgroundColor_(color.CGColor())
            sx = random.uniform(-fw*0.4, W + fw*0.4)
            sy = random.uniform(H*0.3, H * 0.9)
            layer.setPosition_(CGPointMake(sx, sy))
            layer.setOpacity_(alpha)
            no_implicit(layer)
            root.addSublayer_(layer)
            fog_patches.append({
                'layer': layer,
                'speed': random.uniform(FOG_DRIFT_SPEED_MIN, FOG_DRIFT_SPEED_MAX),
                'dir': random.choice([-1.0, 1.0]),
                'alpha_base': alpha,
                'alpha_phase': random.uniform(0, math.pi*2),
                'width': fw
            })

    # ash fall
    if ENABLE_ASH:
        for _ in range(ASH_COUNT):
            sz = random.uniform(1.0, 4.5)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0,0, sz, sz))
            layer.setCornerRadius_(sz/2.0)
            layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.12,0.12,0.12,1.0).CGColor())
            sx = random.uniform(0, W)
            sy = random.uniform(0, H)
            layer.setPosition_(CGPointMake(sx, sy))
            layer.setOpacity_(random.uniform(0.35, 0.75))
            no_implicit(layer)
            root.addSublayer_(layer)
            ash_particles.append({'layer': layer, 'x': sx, 'y': sy, 'speed': random.uniform(*ASH_SPEED)})

    # insects swarm (no reaction to light)
    if ENABLE_INSECTS:
        # create several swarm centers
        swarm_centers = []
        for i in range(6):
            cx = random.uniform(0, W)
            cy = random.uniform(H * 0.2, H * 0.85)
            swarm_centers.append({'x': cx, 'y': cy, 'phase': random.random() * 10.0})
        for i in range(INSECT_COUNT):
            size = random.uniform(1.0, 2.6)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0,0,size,size))
            layer.setCornerRadius_(size/2.0)
            layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95,0.8,0.4,1.0).CGColor())
            sx = random.uniform(0, W)
            sy = random.uniform(0, H)
            layer.setPosition_(CGPointMake(sx, sy))
            no_implicit(layer)
            root.addSublayer_(layer)
            insect_particles.append({'layer': layer, 'x': sx, 'y': sy, 'vx': random.uniform(-30,30), 'vy': random.uniform(-30,30), 'size': size, 'center_idx': random.randrange(len(swarm_centers))})
        # store swarm centers for use inside animate
    else:
        swarm_centers = []

    # sandstorm
    if ENABLE_SANDSTORM:
        for _ in range(SAND_PARTICLES):
            sw = random.uniform(1.0, 2.2)
            sl = random.uniform(2.0, 6.0)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0,0,sw, sl))
            layer.setCornerRadius_(min(1.2, sw/2.0))
            rcol = random.uniform(0.8, 0.95)
            gcol = random.uniform(0.65, 0.82)
            bcol = random.uniform(0.45, 0.6)
            layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(rcol,gcol,bcol,1.0).CGColor())
            sx = random.uniform(0, W)
            sy = random.uniform(0, H)
            layer.setPosition_(CGPointMake(sx, sy))
            layer.setOpacity_(random.uniform(0.25, 0.65))
            no_implicit(layer)
            root.addSublayer_(layer)
            vx = random.uniform(*SAND_SPEED) * random.choice([1, -1])
            sand_particles.append({'layer': layer, 'x': sx, 'y': sy, 'vx': vx})

    # aurora
    if ENABLE_AURORA:
        for i in range(AURORA_BANDS):
            band = CALayer.layer()
            bw = W * 1.6
            bh = random.uniform(H * 0.06, H * 0.18)
            band.setBounds_(CGRectMake(0, 0, bw, bh))
            band.setPosition_(CGPointMake(random.uniform(0, W), random.uniform(H*0.6, H*0.95)))
            band.setCornerRadius_(bh * 0.5)
            band.setOpacity_(0.0)
            no_implicit(band)
            root.addSublayer_(band)
            aurora_bands.append({
                'layer': band,
                'base_y': band.position().y,
                'speed': AURORA_SPEED * random.uniform(0.6, 1.4) * random.choice([-1,1]),
                'phase': random.uniform(0, math.pi*2),
                'width': bw,
                'height': bh,
                'hue_offset': random.uniform(0,1.0)
            })

    # gust state
    gust_state = {
        'active': False,
        'start': 0.0,
        'end': 0.0,
        'strength': 0.0,
        'next_start': time.time() + random.uniform(GUST_MIN_INTERVAL, GUST_MAX_INTERVAL),
    }

    def maybe_start_gust(now):
        if not ENABLE_GUSTS:
            return
        if gust_state['active']:
            if now >= gust_state['end']:
                gust_state['active'] = False
                gust_state['strength'] = 0.0
                gust_state['next_start'] = now + random.uniform(GUST_MIN_INTERVAL, GUST_MAX_INTERVAL)
        else:
            if now >= gust_state['next_start']:
                gust_state['active'] = True
                gust_state['start'] = now
                dur = random.uniform(GUST_MIN_DURATION, GUST_MAX_DURATION)
                gust_state['end'] = now + dur
                sign = 1.0 if random.random() < 0.85 else -1.0
                gust_state['strength'] = sign * random.uniform(GUST_MIN_STRENGTH, GUST_MAX_STRENGTH)

    def get_current_wind(now):
        wave = WIND_WAVE_AMPLITUDE * math.sin(2 * math.pi * WIND_WAVE_FREQ * now)
        gust = gust_state['strength'] if gust_state['active'] else 0.0
        # tornado adds to wind via tornado objects (applied elsewhere)
        return WIND_BASE + wave + gust

    # lightning spawning + ball lightning improved movement
    def spawn_lightning():
        if not ENABLE_LIGHTNING:
            return
        x = random.uniform(0, W)
        total_height = random.uniform(H * 0.35, H * 0.9)
        segments = create_lightning_segments(root, x, H, total_height, main_thickness=random.uniform(1.6, 3.2))
        record = {'segments': segments, 'born': time.time(), 'alive': True, 'total_height': max(total_height, 1.0)}
        active_lightnings.append(record)

        # flash
        if ENABLE_FLASH and flash_layer is not None:
            try:
                CATransaction.begin()
                CATransaction.setDisableActions_(True)
                flash_layer.setOpacity_(0.95)
                CATransaction.commit()
                anim = CABasicAnimation.animationWithKeyPath_("opacity")
                anim.setFromValue_(0.95)
                anim.setToValue_(0.0)
                anim.setDuration_(0.12)
                anim.setFillMode_("forwards")
                anim.setRemovedOnCompletion_(True)
                flash_layer.addAnimation_forKey_(anim, "flash_fade")
            except Exception:
                pass

        # spawn ball lightning cluster smoothly
        if ENABLE_BALL_LIGHTNING and random.random() < BALL_CHANCE_ON_LIGHTNING:
            count = random.randint(1, BALL_COUNT_MAX)
            for _ in range(count):
                bx = x + random.uniform(-160, 160)
                by = H - random.uniform(80, 260)
                bl = CALayer.layer()
                size = random.uniform(8.0, 26.0)
                bl.setBounds_(CGRectMake(0,0,size,size))
                bl.setCornerRadius_(size/2.0)
                bl.setPosition_(CGPointMake(bx, by))
                bl.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0,0.9,0.6,1.0).CGColor())
                bl.setOpacity_(1.0)
                no_implicit(bl)
                root.addSublayer_(bl)
                # smoother movement: store target vx/vy and use velocity smoothing (lerp)
                ball_lightnings.append({
                    'layer': bl,
                    'x': bx, 'y': by,
                    'vx': random.uniform(-40,40), 'vy': random.uniform(-30,30),
                    'target_vx': random.uniform(-100,100),
                    'target_vy': random.uniform(-60,60),
                    'born': time.time(), 'life': BALL_LIFE,
                    'smoothing': random.uniform(0.02, 0.12)
                })

        # schedule segment appearance top->down
        appear_duration = min(LIGHTNING_APPEAR_DURATION, LIGHTNING_LIFETIME * 0.9)
        for seg_info in segments:
            seg_layer = seg_info['layer']
            dist = seg_info['distance']
            if dist < 0: dist = 0.0
            if dist > record['total_height']: dist = record['total_height']
            delay = (dist / record['total_height']) * appear_duration
            def make_add_func(rec, layer_to_add, birth_time):
                def add_segment():
                    now2 = time.time()
                    if not rec['alive']: return
                    if now2 - birth_time > LIGHTNING_LIFETIME: return
                    try:
                        CATransaction.begin()
                        CATransaction.setDisableActions_(True)
                        root.addSublayer_(layer_to_add)
                        CATransaction.commit()
                    except Exception:
                        pass
                return add_segment
            AppHelper.callLater(delay, make_add_func(record, seg_layer, record['born']))

        AppHelper.callLater(random.uniform(LIGHTNING_MIN_DELAY, LIGHTNING_MAX_DELAY), spawn_lightning)

    if ENABLE_LIGHTNING:
        AppHelper.callLater(random.uniform(LIGHTNING_MIN_DELAY, LIGHTNING_MAX_DELAY), spawn_lightning)

    # dust devils spawn
    def spawn_dust_devil():
        if not ENABLE_DUST_DEVIL: return
        # choose center
        cx = random.uniform(0, W)
        cy = random.uniform(H * 0.15, H * 0.75)
        # create particles for devil (small sand/ash-like sprites with varied colors and sizes)
        particles = []
        for i in range(DUST_DEVIL_PARTICLES):
            size = random.uniform(1.0, 6.0)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0,0,size,size))
            layer.setCornerRadius_(size/2.0)

            # varied earth tones for dust
            r_color = random.uniform(0.65, 0.85)
            g_color = random.uniform(0.55, 0.75)
            b_color = random.uniform(0.35, 0.55)
            alpha = random.uniform(0.6, 0.9)
            layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(r_color, g_color, b_color, alpha).CGColor())

            angle = random.uniform(0, 2*math.pi)
            r = random.uniform(8.0, DUST_DEVIL_RADIUS * 1.2)
            height_variation = random.uniform(-DUST_DEVIL_RADIUS * 0.4, H * 0.1)  # can start up to 10% of screen height
            sx = cx + math.cos(angle) * r * random.uniform(0.3, 1.0)
            sy = cy - height_variation
            layer.setPosition_(CGPointMake(sx, sy))
            no_implicit(layer)
            root.addSublayer_(layer)
            particles.append({
                'layer': layer,
                'theta': angle,
                'r': r,
                'cx': cx,
                'cy': cy,
                'speed': random.uniform(1.2, 3.5),
                'height_offset': height_variation,
                'vertical_speed': random.uniform(20.0, 60.0),
                'size': size
            })
        dust_devils.append({'particles': particles, 'born': time.time(), 'life': DUST_DEVIL_LIFE, 'cx': cx, 'cy': cy})
        # schedule next devil occasionally
        AppHelper.callLater(random.uniform(6.0, 18.0), spawn_dust_devil)

    if ENABLE_DUST_DEVIL:
        AppHelper.callLater(random.uniform(2.0, 8.0), spawn_dust_devil)

    # tornado spawn
    def spawn_tornado():
        if not ENABLE_TORNADO: return
        # spawn at top of screen with some horizontal variation
        tx = random.uniform(-TORNADO_RADIUS, W + TORNADO_RADIUS)  # can start off-screen horizontally
        ty = -TORNADO_RADIUS  # start above the screen
        t = Tornado(root, tx, ty, TORNADO_RADIUS, TORNADO_LIFE, W, H)
        tornadoes.append(t)
        # schedule removal by life (cleanup in animate)
        AppHelper.callLater(random.uniform(30.0, 90.0), spawn_tornado)

    if ENABLE_TORNADO:
        AppHelper.callLater(random.uniform(15.0, 60.0), spawn_tornado)

    # meteors accumulator
    meteor_accum = 0.0

    def maybe_spawn_meteor(dt):
        nonlocal meteor_accum
        meteor_accum += METEOR_CHANCE_PER_SEC * dt
        while meteor_accum > 1.0:
            meteor_accum -= 1.0
            if not ENABLE_METEORS:
                continue
            length = random.uniform(*METEOR_LENGTH)
            w = random.uniform(2.0, 4.0)
            layer = CALayer.layer()
            layer.setBounds_(CGRectMake(0,0, w, length))
            layer.setCornerRadius_(w/2.0)
            layer.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0,0.9,0.7,1.0).CGColor())
            from_left = random.random() < 0.5
            sx = -50 if from_left else W + 50
            sy = random.uniform(H*0.5, H + 80)
            layer.setPosition_(CGPointMake(sx, sy))
            no_implicit(layer)
            root.addSublayer_(layer)
            speed = random.uniform(*METEOR_SPEED)
            angle = random.uniform(20, 50)
            if not from_left:
                angle = 180 - angle
            vx = math.cos(math.radians(angle)) * speed
            vy = math.sin(math.radians(angle)) * speed
            meteors.append({'layer': layer, 'x': sx, 'y': sy, 'vx': vx, 'vy': -vy, 'life': 2.5, 'born': time.time()})
            rotate(layer, -math.degrees(math.atan2(-vy, vx)))

    # microburst chance and visual effect
    microburst_active = {'active': False, 'start': 0.0, 'end': 0.0, 'x': 0.0, 'y': 0.0, 'visual_layer': None}

    # create microburst visual layer (dark spot on ground)
    microburst_visual = CALayer.layer()
    microburst_visual.setBounds_(CGRectMake(0, 0, 400, 200))  # smaller, more visible oval
    microburst_visual.setCornerRadius_(200.0)  # make it oval
    microburst_visual.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.15, 0.25, 0.0).CGColor())  # darker, more visible
    microburst_visual.setPosition_(CGPointMake(-200, H + 100))  # off-screen initially
    no_implicit(microburst_visual)
    root.addSublayer_(microburst_visual)
    microburst_active['visual_layer'] = microburst_visual

    def maybe_microburst(dt):
        # probabilistic trigger
        if not ENABLE_MICROBURST:
            return
        if microburst_active['active']:
            if time.time() >= microburst_active['end']:
                microburst_active['active'] = False
                # fade out visual effect
                CATransaction.begin()
                CATransaction.setDisableActions_(True)
                microburst_active['visual_layer'].setOpacity_(0.0)
                CATransaction.commit()
        else:
            if random.random() < MICROBURST_CHANCE * dt:
                microburst_active['active'] = True
                microburst_active['start'] = time.time()
                microburst_active['end'] = time.time() + MICROBURST_DURATION
                microburst_active['x'] = random.uniform(0, W)
                microburst_active['y'] = random.uniform(H*0.5, H*0.95)
                # position and show visual effect
                CATransaction.begin()
                CATransaction.setDisableActions_(True)
                microburst_active['visual_layer'].setPosition_(CGPointMake(microburst_active['x'], microburst_active['y'] + 50))
                microburst_active['visual_layer'].setOpacity_(0.4)
                CATransaction.commit()

    last = time.time()

    # animation loop
    def animate():
        nonlocal last, meteor_accum
        now = time.time()
        dt = now - last
        if dt > MAX_DT:
            dt = MAX_DT
        last = now

        maybe_start_gust(now)
        maybe_microburst(dt)
        current_wind = get_current_wind(now)

        # apply tornado forces first (they modify local wind for objects)
        tornado_wind_offsets = []  # list of functions to modify particle velocities
        for t in tornadoes[:]:
            # expire tornado if life ended
            if time.time() - t.born > t.life:
                # cleanup all tornado particle layers
                for p in t.particles:
                    try:
                        p['layer'].removeFromSuperlayer()
                    except Exception:
                        pass
                try:
                    tornadoes.remove(t)
                except ValueError:
                    pass
                continue
            # apply tornado forces to debris and other particles via method
            t.apply_forces(dt, snow_particles, sand_particles, rain_particles, hail_particles, leaf_particles, ash_particles, insect_particles)

        # snow update
        for p in snow_particles:
            p.prev_x = p.x
            p.y -= p.speed * dt
            # base horizontal move
            p.x += (current_wind + p.jitter) * dt
            # microburst: if active near particle, push down strongly + radial
            if microburst_active['active']:
                dx = p.x - microburst_active['x']
                dy = p.y - microburst_active['y']
                dist = math.hypot(dx, dy)
                if dist < 250.0:  # balanced radius
                    # downward burst
                    p.y -= (MICROBURST_STRENGTH * dt) * (1.0 - dist/250.0)
                    # radial horizontal
                    p.x += (dx / max(1.0, dist)) * (MICROBURST_STRENGTH * 0.03) * dt
            # wrap & respawn
            if p.y < 0:
                p.respawn_top(W, H)
            if p.x + p.radius < -120:
                p.x = W + p.radius
            elif p.x - p.radius > W + 120:
                p.x = -p.radius
            p.angle += 60.0 * dt
            p.layer.setPosition_(CGPointMake(p.x, p.y))
            rotate(p.layer, p.angle)

        # rain update
        for p in rain_particles:
            p.prev_x = p.x
            p.y -= p.speed * dt
            p.x += (current_wind + p.jitter) * dt
            if microburst_active['active']:
                dx = p.x - microburst_active['x']
                dy = p.y - microburst_active['y']
                dist = math.hypot(dx, dy)
                if dist < 250.0:  # balanced radius
                    p.y -= (MICROBURST_STRENGTH * dt) * (1.0 - dist/250.0)
                    p.x += (dx / max(1.0, dist)) * (MICROBURST_STRENGTH * 0.03) * dt
            if p.y < 0:
                p.respawn_top(W, H, width_override=p.width)
            half_w = (p.width or 0) / 2.0
            if p.x + half_w < -120:
                p.x = W + half_w
            elif p.x - half_w > W + 120:
                p.x = -half_w
            p.layer.setPosition_(CGPointMake(p.x, p.y))
            wind_angle = max(-70.0, min(70.0, current_wind / 8.0))
            rotate(p.layer, wind_angle/3)

        # hail update (bounce)
        if ENABLE_HAIL:
            for h in hail_particles:
                h.y -= h.v_y * dt
                h.x += current_wind * dt * 0.18
                if h.y < 0:
                    # bounce
                    h.v_y = h.v_y * HAIL_BOUNCE_COEFF
                    if h.v_y < HAIL_MIN_BOUNCE_V:
                        h.respawn(W, H)
                    else:
                        h.y = 6.0 + random.uniform(0.0, 8.0)
                if h.x < -120:
                    h.x = W + 120
                elif h.x > W + 120:
                    h.x = -120
                h.layer.setPosition_(CGPointMake(h.x, h.y))

        # leaves
        if ENABLE_LEAVES:
            for p in leaf_particles:
                p.prev_x = p.x
                p.y -= p.speed * dt
                sway = (math.sin((p.y + p.x) * 0.02) * 0.5 + 0.5)
                horizontal = (current_wind * 0.6 + p.jitter) * dt * (0.6 + 0.8 * sway)
                p.x += horizontal
                p.angle += getattr(p,'rot_speed', p.rot_speed) * dt
                if p.y < -200 or p.x < -400 or p.x > W + 400:
                    p.respawn_top(W, H)
                p.layer.setPosition_(CGPointMake(p.x, p.y))
                rotate(p.layer, p.angle)

        # ash fall (slow dark flakes)
        if ENABLE_ASH:
            for a in ash_particles:
                a['y'] -= a['speed'] * dt
                a['x'] += (current_wind * 0.2) * dt
                if a['y'] < -50:
                    a['y'] = H + random.uniform(10, 200)
                    a['x'] = random.uniform(0, W)
                a['layer'].setPosition_(CGPointMake(a['x'], a['y']))

        # insects swarm (cohesion to centers + noise movement)
        if ENABLE_INSECTS:
            # update swarm centers slowly
            for c in swarm_centers:
                # drift centers a bit
                c['x'] += math.sin(time.time()*0.1 + c['phase']) * 4.0 * dt
                c['y'] += math.cos(time.time()*0.07 + c['phase']) * 3.0 * dt
                # clamp
                c['x'] = max(0, min(W, c['x']))
                c['y'] = max(H*0.1, min(H, c['y']))
            for idx, insect in enumerate(insect_particles):
                ci = swarm_centers[insect['center_idx']]
                # vector to center
                dx = ci['x'] - insect['x']
                dy = ci['y'] - insect['y']
                dist = math.hypot(dx, dy)
                # steering towards center with some noise
                steer_x = (dx / (dist+1.0)) * 40.0
                steer_y = (dy / (dist+1.0)) * 20.0
                # random jitter
                jitter_x = random.uniform(-30, 30)
                jitter_y = random.uniform(-30, 30)
                insect['vx'] = lerp(insect['vx'], steer_x + jitter_x, 0.06)
                insect['vy'] = lerp(insect['vy'], steer_y + jitter_y, 0.06)
                insect['x'] += insect['vx'] * dt
                insect['y'] += insect['vy'] * dt
                # wrap / bounds
                if insect['x'] < -50: insect['x'] = W + 50
                if insect['x'] > W + 50: insect['x'] = -50
                if insect['y'] < H*0.05: insect['y'] = H*0.05 + random.uniform(0, 10)
                if insect['y'] > H: insect['y'] = H - random.uniform(0, 10)
                insect['layer'].setPosition_(CGPointMake(insect['x'], insect['y']))

        # dust devils update
        for dd in dust_devils[:]:
            age = time.time() - dd['born']
            if age > dd['life']:
                # remove particles
                for p in dd['particles']:
                    try:
                        p['layer'].removeFromSuperlayer()
                    except Exception:
                        pass
                try:
                    dust_devils.remove(dd)
                except ValueError:
                    pass
                continue
            # animate each particle with enhanced swirling and vertical movement
            for p in dd['particles']:
                # increase theta for rotation (faster near center)
                rotation_speed = 2.5 + p['speed'] * 0.8 + (1.0 - p['r']/DUST_DEVIL_RADIUS) * 2.0
                p['theta'] += dt * rotation_speed

                # slowly reduce radius to create inward spiral, but with some variation
                spiral_in = dt * (10.0 * (1.0 + p['speed']*0.3))
                p['r'] = max(5.0, p['r'] - spiral_in)

                # add vertical movement - particles rise as they spiral inward (full screen height)
                height_boost = (1.0 - p['r']/DUST_DEVIL_RADIUS) * 1.2  # stronger lift when closer to center
                p['height_offset'] += p['vertical_speed'] * dt * (0.9 + height_boost)

                # calculate new position with conical shape
                x = p['cx'] + math.cos(p['theta']) * p['r']
                y = p['cy'] - p['height_offset'] - p['r'] * 0.4  # conical shape

                # respawn particles that go too high or too far inward
                if p['height_offset'] > H * 1.1 or p['r'] < 8.0 or y < -200:
                    # respawn at bottom with new parameters
                    p['theta'] = random.uniform(0, 2*math.pi)
                    p['r'] = random.uniform(DUST_DEVIL_RADIUS * 0.9, DUST_DEVIL_RADIUS * 1.2)
                    p['height_offset'] = random.uniform(-DUST_DEVIL_RADIUS * 0.3, H * 0.05)
                    p['vertical_speed'] = random.uniform(35.0, 100.0)
                    x = p['cx'] + math.cos(p['theta']) * p['r']
                    y = p['cy'] - p['height_offset'] - p['r'] * 0.4

                p['x'] = x
                p['y'] = y
                p['layer'].setPosition_(CGPointMake(x, y))

        # meteors and meteors spawn
        for m in meteors[:]:
            m['x'] += m['vx'] * dt
            m['y'] += m['vy'] * dt
            if time.time() - m['born'] > m['life']:
                try: m['layer'].removeFromSuperlayer()
                except Exception: pass
                try: meteors.remove(m)
                except ValueError: pass
                continue
            m['layer'].setPosition_(CGPointMake(m['x'], m['y']))
        maybe_spawn_meteor(dt)

        # sandstorm movement
        if ENABLE_SANDSTORM:
            for sp in sand_particles:
                sp['x'] += sp['vx'] * dt + current_wind * dt * 0.08
                if sp['x'] < -150: sp['x'] = W + 150
                elif sp['x'] > W + 150: sp['x'] = -150
                sp['y'] += math.sin(time.time()*3.0 + sp['x'] * 0.01) * 2.0 * dt
                sp['layer'].setPosition_(CGPointMake(sp['x'], sp['y']))

        # ball lightning (smooth velocities via target + smoothing)
        for bl in ball_lightnings[:]:
            age = time.time() - bl['born']
            if age > bl['life']:
                try:
                    bl['layer'].removeFromSuperlayer()
                except Exception:
                    pass
                try:
                    ball_lightnings.remove(bl)
                except ValueError:
                    pass
                continue
            # occasionally change target velocities
            if random.random() < 0.02:
                bl['target_vx'] = random.uniform(-120,120)
                bl['target_vy'] = random.uniform(-80,80)
            # lerp velocity toward target
            bl['vx'] = lerp(bl['vx'], bl['target_vx'], bl['smoothing'])
            bl['vy'] = lerp(bl['vy'], bl['target_vy'], bl['smoothing'])
            bl['x'] += bl['vx'] * dt
            bl['y'] += bl['vy'] * dt + math.sin(age * 6.0) * 6.0 * dt
            # slight slow fade at end
            if age > bl['life'] * 0.6:
                remaining = (bl['life'] - age) / (bl['life'] * 0.4)
                CATransaction.begin()
                CATransaction.setDisableActions_(True)
                bl['layer'].setOpacity_(max(0.0, remaining))
                CATransaction.commit()
            bl['layer'].setPosition_(CGPointMake(bl['x'], bl['y']))

        # lightning cleanup
        for rec in active_lightnings[:]:
            if time.time() - rec['born'] > LIGHTNING_LIFETIME:
                rec['alive'] = False
                for seg_info in rec['segments']:
                    try:
                        seg_info['layer'].removeFromSuperlayer()
                    except Exception:
                        pass
                try:
                    active_lightnings.remove(rec)
                except ValueError:
                    pass


        # dust devil spawn chance handled by scheduled call earlier

        AppHelper.callAfter(animate)

    AppHelper.callAfter(animate)
    AppHelper.runEventLoop()

if __name__ == "__main__":
    main()
