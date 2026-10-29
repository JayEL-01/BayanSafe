"""Regression test that queued input is delivered to the new active scene."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import unittest
from unittest.mock import patch

import pygame

from src.core.game import Game
from src.states.base_state import BaseState


class SceneTransitionTests(unittest.TestCase):
    def test_second_queued_key_reaches_the_scene_after_transition(self):
        game = Game()
        received = []

        class Destination(BaseState):
            def handle_event(self, event):
                received.append(event.key)
                self.game.quit()

        class Source(BaseState):
            def handle_event(self, event):
                if event.key == pygame.K_1:
                    self.game.state_manager.change(Destination(self.game))

        game.state_manager.push(Source(game))
        keys = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)]
        with patch.object(game.controller, "poll_events", return_value=[]), \
                patch("pygame.event.get", return_value=keys):
            game.run()
        self.assertEqual(received, [pygame.K_2])


if __name__ == "__main__":
    unittest.main()
