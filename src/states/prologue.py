"""Prologue State for BayanSafe.

Clean placeholder ready for the new story script.
"""
from src.states.chapter import ChapterState


class PrologueState(ChapterState):
    """Prologue state loading data/story/prologue.json onto a clean, plain-colored map."""

    def __init__(self, game):
        super().__init__(game, chapter_id="prologue")
