import pygame

from src.entities.walk_sheet import ReferencePlayerSheet, WalkSheet
from src.ui.pixel_art import character_sprite


class Player:
    def __init__(self, x, y, speed=78, max_health=100, walk_path=None, color=(255, 200, 60)):
        self.size = 12
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.pos = pygame.Vector2(x, y)
        self.speed = speed
        self.color = tuple(color)

        # Use the supplied walking sheet when available, with drawn pixel art
        # as a fallback so a missing asset never turns the character into a box.
        self.sheet = None
        self.fallback_sprite = None
        character_id = "maria" if "maria" in str(walk_path).lower() else "juan"
        try:
            self.sheet = ReferencePlayerSheet(character_id, height=20)
        except (OSError, pygame.error, ValueError):
            self.sheet = None
        if self.sheet is None and walk_path:
            try:
                self.sheet = WalkSheet(walk_path, height=20)
            except (OSError, pygame.error, ValueError):
                pass
        if self.sheet is None:
            self.fallback_sprite = pygame.transform.scale(character_sprite(self.color), (16, 20))

        self.max_health = max_health
        self.health = max_health
        self.invuln = 0.0        # seconds of protection after a hit
        self.damage_taken = 0    # used later for achievements
        self.ability = None
        self.ability_cooldown = 0.0
        self.sprint_time = 0.0
        self.ability_notice = ""
        self.ability_notice_time = 0.0

    def activate_ability(self):
        if self.ability_cooldown > 0:
            self.ability_notice = f"Ability ready in {self.ability_cooldown:.0f}s"
            self.ability_notice_time = 1.5
            return False
        if self.ability == "sprint":
            self.sprint_time = 2.0
            self.ability_cooldown = 8.0
            self.ability_notice = "SPRINT!"
        elif self.ability == "first_aid":
            restored = min(35, self.max_health - self.health)
            if restored <= 0:
                self.ability_notice = "Health is already full"
                self.ability_notice_time = 1.5
                return False
            self.health += restored
            self.ability_cooldown = 20.0
            self.ability_notice = f"FIRST AID +{restored} HP"
        else:
            return False
        self.ability_notice_time = 1.5
        return True

    def get_direction(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: direction.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: direction.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: direction.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: direction.y += 1
        # Pygame-compatible USB HID gamepads can drive the same single-player
        # movement. Custom controller firmware should emit these same axes.
        if pygame.joystick.get_init() and pygame.joystick.get_count():
            try:
                joystick = pygame.joystick.Joystick(0)
                if joystick.get_init() and joystick.get_numaxes() >= 2:
                    x, y = joystick.get_axis(0), joystick.get_axis(1)
                    deadzone = 0.28
                    if abs(x) > deadzone:
                        direction.x += x
                    if abs(y) > deadzone:
                        direction.y += y
            except pygame.error:
                pass  # a disconnected controller falls back to keyboard control
        if direction.length_squared() > 0:
            direction = direction.normalize()
        return direction

    def take_damage(self, amount):
        """Returns True if the hit counted."""
        if self.invuln > 0:
            return False
        self.health = max(0, self.health - amount)
        self.damage_taken += amount
        self.invuln = 1.0
        return True

    def update(self, dt, walls, push=(0, 0), speed_scale=1.0, collision=None):
        self.ability_cooldown = max(0.0, self.ability_cooldown - dt)
        self.sprint_time = max(0.0, self.sprint_time - dt)
        self.ability_notice_time = max(0.0, self.ability_notice_time - dt)
        if self.invuln > 0:
            self.invuln -= dt

        start = self.pos.copy()
        direction = self.get_direction()

        # Walking plus wind push.
        move_speed = self.speed * (2.0 if self.sprint_time > 0 else 1.0) * speed_scale
        velocity = direction * move_speed + pygame.Vector2(push)

        previous_x = self.rect.x
        self.pos.x += velocity.x * dt
        self.rect.x = round(self.pos.x)
        for wall in walls:
            if self.rect.colliderect(wall):
                if velocity.x > 0:
                    self.rect.right = wall.left
                elif velocity.x < 0:
                    self.rect.left = wall.right
                self.pos.x = self.rect.x
        if collision and collision.is_blocked(self.rect):
            self.rect.x = previous_x
            self.pos.x = self.rect.x

        previous_y = self.rect.y
        self.pos.y += velocity.y * dt
        self.rect.y = round(self.pos.y)
        for wall in walls:
            if self.rect.colliderect(wall):
                if velocity.y > 0:
                    self.rect.bottom = wall.top
                elif velocity.y < 0:
                    self.rect.top = wall.bottom
                self.pos.y = self.rect.y
        if collision and collision.is_blocked(self.rect):
            self.rect.y = previous_y
            self.pos.y = self.rect.y

        # Face the requested direction even if blocked; idle preserves facing.
        if self.sheet:
            if direction.length_squared() > 0:
                self.sheet.update(dt, direction.x, direction.y)
            else:
                self.sheet.update(dt, 0, 0)

    def draw(self, surface, camera=None):
        # Blink while protected.
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            return
        rect = camera.apply(self.rect) if camera else self.rect
        zoom = camera.zoom if camera else 1.0
        if self.sheet:
            img = self.sheet.image()
            if zoom != 1.0:
                img = pygame.transform.scale(img, (round(img.get_width() * zoom),
                                                   round(img.get_height() * zoom)))
            surface.blit(img, img.get_rect(midbottom=(rect.centerx, rect.bottom + 2)))
        elif self.fallback_sprite:
            sprite = self.fallback_sprite
            if zoom != 1.0:
                sprite = pygame.transform.scale(sprite, (round(sprite.get_width() * zoom),
                                                          round(sprite.get_height() * zoom)))
            surface.blit(sprite, sprite.get_rect(midbottom=(rect.centerx, rect.bottom + 2)))
        else:
            pygame.draw.rect(surface, self.color, rect)
