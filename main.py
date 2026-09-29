from src.core.game import Game
from src.states.main_menu import MainMenu


def main():
    game = Game()
    game.state_manager.push(MainMenu(game))
    game.run()


if __name__ == "__main__":
    main()