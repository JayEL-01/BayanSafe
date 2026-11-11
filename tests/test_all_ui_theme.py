import os
import sys
sys.path.insert(0, ".")

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame
from src.core.game import Game
from src.states.main_menu import MainMenu
from src.states.character_select import CharacterSelect
from src.states.world_map import WorldMap
from src.states.chapter import ChapterState
from src.states.guide_state import GuideState
from src.states.options_state import OptionsState
from src.states.high_scores import HighScores
from src.states.new_game_confirm import NewGameConfirm
from src.states.stage_complete import StageComplete
from src.states.game_over import GameOver
from src.ui import theme


class ThemePreviewsTest(unittest.TestCase):
    def test_generate_snapshots(self):
        game = Game()
        canvas = game.canvas
        out_dir = "tests/theme_previews"
        os.makedirs(out_dir, exist_ok=True)

        # 1. Main Menu
        main_menu = MainMenu(game)
        for _ in range(15):
            main_menu.update(0.05)
        main_menu.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/1_main_menu.png")

        # 2. Character Select
        char_select = CharacterSelect(game)
        char_select.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/2_character_select.png")

        # 3. World Map
        world_map = WorldMap(game)
        world_map.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/3_world_map.png")

        # 4. Chapter (Prologue)
        prologue = ChapterState(game, "prologue")
        prologue.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/4_prologue.png")

        # 5. High Scores
        high_scores = HighScores(game)
        high_scores.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/5_high_scores.png")

        # 6. New Game Confirm
        new_game = NewGameConfirm(game)
        new_game.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/6_new_game_confirm.png")

        # 7. Stage Complete
        complete = StageComplete(game)
        complete.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/7_stage_complete.png")

        # 8. Game Over
        game_over = GameOver(game, lambda: None)
        game_over.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/8_game_over.png")

        # 9. Options
        options = OptionsState(game)
        options.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/9_options.png")

        # 10. Guide
        guide = GuideState(game)
        guide.draw(canvas)
        theme.flush_text(canvas)
        pygame.image.save(canvas, f"{out_dir}/10_guide.png")


if __name__ == "__main__":
    unittest.main()
