import pygame


class Player:
    def __init__(self, x, y, speed=60):
        self.size = 12
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.pos = pygame.Vector2(x, y)  # exact position (decimals allowed)
        self.speed = speed               # pixels per second
        self.color = (255, 200, 60)

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

        # Stops diagonal movement from being faster.
        if direction.length_squared() > 0:
            direction = direction.normalize()
        return direction

    def update(self, dt, walls):
        direction = self.get_direction()

        # Move on the X axis, then fix collisions.
        self.pos.x += direction.x * self.speed * dt
        self.rect.x = round(self.pos.x)
        for wall in walls:
            if self.rect.colliderect(wall):
                if direction.x > 0:
                    self.rect.right = wall.left
                elif direction.x < 0:
                    self.rect.left = wall.right
                self.pos.x = self.rect.x

        # Move on the Y axis, then fix collisions.
        self.pos.y += direction.y * self.speed * dt
        self.rect.y = round(self.pos.y)
        for wall in walls:
            if self.rect.colliderect(wall):
                if direction.y > 0:
                    self.rect.bottom = wall.top
                elif direction.y < 0:
                    self.rect.top = wall.bottom
                self.pos.y = self.rect.y

    def draw(self, surface, camera=None):
        rect = camera.apply(self.rect) if camera else self.rect
        pygame.draw.rect(surface, self.color, rect)