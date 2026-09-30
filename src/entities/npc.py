import pygame


class NPC:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.rect = pygame.Rect(data["pos"][0], data["pos"][1], 12, 12)
        self.color = tuple(data["color"])
        self.dialogue = data["dialogue"]
        self.after_dialogue = data.get("after_dialogue", data["dialogue"])
        self.talked = False
        self.choice = data.get("choice")  

    def get_lines(self):
        return self.after_dialogue if self.talked else self.dialogue

    def is_near(self, player_rect, distance=10):
        return player_rect.inflate(distance * 2, distance * 2).colliderect(self.rect)

    def draw(self, surface, camera):
        r = camera.apply(self.rect)
        pygame.draw.rect(surface, self.color, r)
        pygame.draw.rect(surface, (255, 255, 255), r, 1)