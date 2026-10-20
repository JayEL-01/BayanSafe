import random

import pygame

from src.core.session import GameSession
from src.states.base_state import BaseState
from src.states.loading import LoadingScreen
from src.ui import theme
from src.ui.button import Button
from src.utils.data_loader import load_json
from src.utils.helpers import wrap_text


class StageComplete(BaseState):
    ENDINGS = {
        "good": (
            "A WORLD RESTORED",
            "The World Engine is disabled. Communities begin rebuilding.",
        ),
        "neutral": (
            "A COSTLY SURVIVAL",
            "The machine stops, but losses remain. Recovery takes time.",
        ),
        "bad": (
            "THE WORLD OVERWHELMED",
            "The machine releases another surge. Disasters grow stronger.",
        ),
    }

    AUTO_CONTINUE_SECONDS = 13.0

    def __init__(self, game, stats, on_replay=None):
        super().__init__(game)
        self.stats = stats
        self.campaign_final = stats.get("stage_id") == GameSession.STAGE_ORDER[-1]
        self.ending_key = stats.get("ending", "fresh_start")
        self.quiz = stats.get("quiz") or {}
        self.ui_font = theme.get_font("tiny")
        self.button_font = pygame.font.Font(None, 16)
        lessons = stats["lessons"]
        self.lesson = random.choice(lessons) if lessons else "Review the safety guide before the next mission."
        self.view = "results"
        self.elapsed = 0.0
        self.continuing = False
        self.answer_selected = 0
        self.answer_submitted = False
        self.answer_correct = False
        self.quiz_button = Button("SAFETY CHECK", (4, 158, 78, 18), self.open_quiz, self.button_font)
        self.answers = [
            Button(text, (24, 0, 272, 19), lambda i=i: self.submit(i), self.button_font)
            for i, text in enumerate(self.quiz.get("options", []))
        ]
        self.quiz_font = theme.get_font("tiny")
        self.quiz_answer_lines = []
        self.quiz_feedback_y = 0
        self.layout_quiz()
        self.selected = 0

    def open_quiz(self):
        if self.quiz:
            self.view = "quiz"
            self.selected = self.answer_selected
            self.update_selection()

    def submit(self, index):
        if not self.quiz or self.answer_submitted:
            return
        self.answer_selected = index
        self.answer_submitted = True
        self.answer_correct = index == self.quiz.get("answer")
        if not self.answer_correct:
            penalty = 150
            self.stats["score"] = max(0, self.stats.get("score", 0) - penalty)
            self.stats["quiz_penalty"] = self.stats.get("quiz_penalty", 0) + penalty
            self.stats["perfect"] = False
            self.game.session.record_run(self.stats["stage_id"], self.stats, count_attempt=False)
            if self.campaign_final:
                self.ending_key = self.game.session.campaign_ending()
                self.stats["ending"] = self.ending_key

    def continue_story(self):
        if self.continuing:
            return
        self.continuing = True
        manager = self.game.state_manager
        # Remove both this recap and the finished playfield before entering the
        # next scene; otherwise an old mission would remain underneath it.
        manager.pop()
        manager.pop()
        if self.campaign_final:
            from src.states.main_menu import MainMenu
            if not isinstance(manager.current(), MainMenu):
                manager.push(MainMenu(self.game))
            return

        from src.states.big_map import BigMap
        next_stage = self.game.session.current_stage
        try:
            from src.utils.data_loader import load_json
            next_data = load_json(f"data/stages/{next_stage}.json")
            location = next_data.get("campaign_region", next_data.get("chapter", "the next community"))
        except (OSError, ValueError, KeyError):
            location = "the next community"
        message = f"STORY CONTINUES · {location.upper()}"
        from src.states.chapter_intro import ChapterIntro
        build_next = (lambda: ChapterIntro(self.game, next_stage)
                      if next_stage in load_json("data/chapter_openers.json")
                      else BigMap(self.game, next_stage))
        manager.push(LoadingScreen(self.game, build_next, message, duration=0.9))

    def update(self, dt):
        if self.view != "quiz" and not self.continuing:
            self.elapsed += dt
            limit = 22.0 if self.campaign_final else self.AUTO_CONTINUE_SECONDS
            if self.elapsed >= limit:
                self.continue_story()

    def update_selection(self):
        if self.view == "quiz":
            for i, b in enumerate(self.answers):
                b.selected = (i == self.selected)

    def handle_event(self, event):
        if self.view == "quiz":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.view = "results"
                    self.elapsed = 0.0
                elif self.answer_submitted and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.view = "results"
                    self.elapsed = 0.0
                elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
                    self.selected = (self.selected - 1) % max(1, len(self.answers))
                    self.update_selection()
                elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                    self.selected = (self.selected + 1) % max(1, len(self.answers))
                    self.update_selection()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.answers:
                    self.answers[self.selected].activate()
            elif event.type == pygame.MOUSEMOTION:
                pos = self.game.to_canvas_pos(event.pos)
                for i, b in enumerate(self.answers):
                    if b.contains(pos):
                        self.selected = i
                        self.update_selection()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.game.to_canvas_pos(event.pos)
                for i, b in enumerate(self.answers):
                    if b.contains(pos):
                        self.selected = i
                        self.update_selection()
                        b.activate()
                        break
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_t):
                self.open_quiz()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.continue_story()
        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            self.quiz_button.selected = self.quiz_button.contains(pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            if self.quiz_button.contains(pos):
                self.quiz_button.activate()

    def panel(self, surface, rect, label):
        theme.draw_panel(surface, rect, title=label, accent=theme.HONEY)

    def draw_results(self, surface):
        s = self.stats
        heading = "CAMPAIGN COMPLETE!" if self.campaign_final else "MISSION COMPLETE!"
        theme.draw_text(surface, heading, (160, 10), "heading", theme.SAGE,
                        shadow=False, anchor="center")
        mission_number = s.get("mission_number", 0)
        mission_label = (f"STORY {mission_number:02d}/{len(GameSession.STAGE_ORDER)} · "
                         f"{s.get('chapter', 'CAMPAIGN').upper()}")
        theme.draw_text(surface, mission_label, (160, 19), "tiny", theme.CREAM_DIM,
                        shadow=False, anchor="midtop")
        left = pygame.Rect(10, 30, 146, 82)
        self.panel(surface, left, "RESULTS")
        minutes, seconds = divmod(int(s["time"]), 60)
        rows = [
            ("TIME", f"{minutes}:{seconds:02d}"),
            ("DAMAGE TAKEN", str(s["damage"])),
            ("HOME DAMAGE", str(s.get("property_damage", 0))),
            ("ITEMS", f"{s['items_found']}/{s['items_total']}"),
            ("OBJECTIVES", f"{s['quests_done']}/{s['quests_total']}"),
            ("SCORE", str(s["score"])),
        ]
        for i, (name, value) in enumerate(rows):
            y = left.y + 19 + i * 10
            theme.draw_text(surface, name, (left.x + 6, y), self.ui_font,
                            theme.CREAM_DIM, shadow=False)
            theme.draw_text(surface, value, (left.right - 6, y), self.ui_font,
                            theme.CREAM, shadow=False, anchor="topright")
        right = pygame.Rect(164, 30, 146, 82)
        self.panel(surface, right, "CHOICES & CONSEQUENCES")
        text = " ".join(s["consequences"]) or "You completed the mission by following the evacuation plan."
        for i, line in enumerate(wrap_text(text, self.ui_font, right.w - 12)[:7]):
            theme.draw_text(surface, line, (right.x + 6, right.y + 19 + i * 8),
                            self.ui_font, theme.CREAM, shadow=False)
        lesson = pygame.Rect(10, 112, 300, 48)
        if self.campaign_final:
            title, ending_text = self.ENDINGS[self.ending_key]
            summary = self.game.session.campaign_summary()
            self.panel(surface, lesson,
                       f"FINAL OUTCOME · {summary['points']:,} POINTS · TASKS {summary['objective_rate']:.0%}")
            self.draw_recovery_vignette(surface, lesson, self.ending_key)
            theme.draw_text(surface, title, (lesson.x + 42, lesson.y + 18), self.ui_font,
                            (255, 220, 140), shadow=False)
            details = (ending_text, f"SUPPLIES COLLECTED: {summary['item_rate']:.0%}")
            for i, line in enumerate(details):
                theme.draw_text(surface, line, (lesson.x + 42, lesson.y + 27 + i * 10),
                                self.ui_font, (220, 230, 225), shadow=False)
        else:
            self.panel(surface, lesson, "SAFETY TIP")
            for i, line in enumerate(wrap_text(self.lesson, self.ui_font, 286)[:2]):
                theme.draw_text(surface, line, (lesson.x + 7, lesson.y + 19 + i * 9),
                                self.ui_font, (255, 220, 140), shadow=False)

    @staticmethod
    def draw_recovery_vignette(surface, panel, ending):
        """Small, hopeful recovery illustration that changes with the ending."""
        x, y = panel.x + 9, panel.y + 19
        sky = (168, 207, 219) if ending != "bad" else (117, 133, 148)
        roof = (76, 130, 87) if ending == "good" else (131, 105, 91)
        pygame.draw.rect(surface, sky, (x, y, 25, 16))
        pygame.draw.circle(surface, (255, 221, 118), (x + 19, y + 4), 3)
        pygame.draw.rect(surface, (91, 139, 83), (x, y + 13, 25, 3))
        pygame.draw.rect(surface, (225, 203, 160), (x + 7, y + 7, 12, 8))
        pygame.draw.polygon(surface, roof, [(x + 5, y + 8), (x + 13, y + 2), (x + 21, y + 8)])
        pygame.draw.rect(surface, (93, 67, 52), (x + 12, y + 10, 3, 5))
        if ending == "good":
            for flower_x in (x + 2, x + 23):
                pygame.draw.line(surface, (47, 115, 66), (flower_x, y + 14), (flower_x, y + 10), 1)
                pygame.draw.circle(surface, (238, 137, 105), (flower_x, y + 9), 2)
        elif ending == "neutral":
            pygame.draw.rect(surface, (73, 130, 194), (x + 1, y + 10, 4, 4))
            pygame.draw.rect(surface, (73, 130, 194), (x + 20, y + 10, 4, 4))
        else:
            pygame.draw.line(surface, (208, 187, 127), (x + 1, y + 15), (x + 5, y + 12), 1)
            pygame.draw.rect(surface, (178, 126, 70), (x + 21, y + 12, 3, 3))

    def draw_quiz(self, surface):
        theme.draw_text(surface, "SAFETY CHECK", (160, 14), "heading", theme.HONEY,
                        shadow=False, anchor="center")
        question = self.quiz.get("question", "Which action best protects people during this disaster?")
        for i, line in enumerate(wrap_text(question, self.quiz_font, 286)[:3]):
            theme.draw_text(surface, line, (160, 34 + i * 9), self.quiz_font, theme.CREAM, anchor="center")
        for answer, lines in zip(self.answers, self.quiz_answer_lines):
            # Use a stable, solid selected row here. The animated hazard stripes
            # in the shared button treatment can visually cut through wrapped quiz text.
            theme.draw_button(surface, answer.rect, "", False, font="tiny")
            if answer.selected:
                highlight = answer.rect.inflate(-4, -4)
                pygame.draw.rect(surface, theme.HONEY, highlight)
                pygame.draw.rect(surface, theme.CREAM, answer.rect, 1)
            line_height = self.quiz_font.get_height() + 1
            first_y = answer.rect.centery - ((len(lines) - 1) * line_height) // 2
            for i, line in enumerate(lines):
                theme.draw_text(surface, line, (answer.rect.centerx, first_y + i * line_height),
                                self.quiz_font, theme.NIGHT if answer.selected else theme.CREAM,
                                shadow=False, anchor="center")
        if self.answer_submitted:
            color = theme.SAGE if self.answer_correct else theme.CORAL
            label = "Correct!" if self.answer_correct else "Incorrect: -150 points"
            theme.draw_text(surface, label, (160, self.quiz_feedback_y), "tiny", color, anchor="center")
            explanation = self.quiz.get("explanation", "Follow official emergency guidance.")
            lines = wrap_text(explanation, self.quiz_font, 284)[:3]
            for i, line in enumerate(lines):
                theme.draw_text(surface, line, (160, self.quiz_feedback_y + 10 + i * 8),
                                self.quiz_font, theme.CREAM, anchor="center")
        else:
            theme.draw_text(surface, "Choose an answer. ESC returns to results.",
                            (160, self.quiz_feedback_y), "tiny", theme.CREAM_DIM, anchor="center")

    def layout_quiz(self):
        """Wrap mission answers into readable, evenly spaced, clickable rows."""
        question = self.quiz.get("question", "Which action best protects people during this disaster?")
        question_lines = wrap_text(question, self.quiz_font, 286)[:3]
        answer_y = max(61, 34 + len(question_lines) * 9 + 3)
        gap = 2
        self.quiz_answer_lines = []
        for answer in self.answers:
            lines = wrap_text(answer.text, self.quiz_font, 250) or [""]
            self.quiz_answer_lines.append(lines)
            row_height = max(17, len(lines) * (self.quiz_font.get_height() + 1) + 4)
            answer.rect = pygame.Rect(24, answer_y, 272, row_height)
            answer_y += row_height + gap
        self.quiz_feedback_y = min(170, answer_y + 1)

    def draw(self, surface):
        surface.fill((15, 25, 55))
        if self.view == "quiz":
            self.draw_quiz(surface)
        else:
            self.draw_results(surface)
            self.quiz_button.draw(surface)
            if self.campaign_final:
                prompt = "CAMPAIGN ENDING · ENTER TO RETURN HOME"
            else:
                remaining = max(0, int(self.AUTO_CONTINUE_SECONDS - self.elapsed + 0.99))
                prompt = f"AUTO {remaining}s · ENTER TO CONTINUE"
            theme.draw_text(surface, prompt, (210, 164), "tiny", theme.CREAM_DIM,
                            shadow=False, anchor="center")
