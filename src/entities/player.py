import pygame


class Player:
    def __init__(self, x, y, speed=60, max_health=100):
        self.size = 12
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.pos = pygame.Vector2(x, y)
        self.speed = speed
        self.color = (255, 200, 60)

        self.max_health = max_health
        self.health = max_health
        self.invuln = 0.0        # seconds of protection after a hit
        self.damage_taken = 0    # used later for achievements

    def get_direction(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y += 1
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

    def update(self, dt, walls, push=(0, 0)):
        if self.invuln > 0:
            self.invuln -= dt

        # Walking plus wind push.
        velocity = self.get_direction() * self.speed + pygame.Vector2(push)

        self.pos.x += velocity.x * dt
        self.rect.x = round(self.pos.x)
        for wall in walls:
            if self.rect.colliderect(wall):
                if velocity.x > 0:
                    self.rect.right = wall.left
                elif velocity.x < 0:
                    self.rect.left = wall.right
                self.pos.x = self.rect.x

        self.pos.y += velocity.y * dt
        self.rect.y = round(self.pos.y)
        for wall in walls:
            if self.rect.colliderect(wall):
                if velocity.y > 0:
                    self.rect.bottom = wall.top
                elif velocity.y < 0:
                    self.rect.top = wall.bottom
                self.pos.y = self.rect.y

    def draw(self, surface, camera=None):
        # Blink while protected.
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            return
        rect = camera.apply(self.rect) if camera else self.rect
        pygame.draw.rect(surface, self.color, rect)