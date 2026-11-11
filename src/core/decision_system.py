"""Decision and Choice Consequence System for BayanSafe.

Handles branching disaster response decisions, prompt presentation,
safety evaluation, educational explanations, and score integration.
"""

from typing import List, Dict, Any, Callable, Optional


class Decision:
    def __init__(
        self,
        decision_id: str,
        prompt: str,
        options: List[Dict[str, Any]],  # [{"text": ..., "safe": bool, "feedback": ..., "lesson": ...}]
        on_resolved: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.decision_id = decision_id
        self.prompt = prompt
        self.options = options
        self.on_resolved = on_resolved
        self.selected_index = 0
        self.resolved = False
        self.chosen_option: Optional[Dict[str, Any]] = None

    def select(self, index: int):
        if 0 <= index < len(self.options):
            self.selected_index = index

    def next_option(self):
        self.selected_index = (self.selected_index + 1) % len(self.options)

    def prev_option(self):
        self.selected_index = (self.selected_index - 1) % len(self.options)

    def confirm(self, score_system=None) -> Dict[str, Any]:
        """Confirm current selection and record consequence."""
        self.resolved = True
        self.chosen_option = self.options[self.selected_index]
        if score_system:
            score_system.record_choice(
                prompt=self.prompt,
                choice_text=self.chosen_option["text"],
                is_safe=self.chosen_option["safe"],
                lesson=self.chosen_option.get("lesson", ""),
            )
        if self.on_resolved:
            self.on_resolved(self.chosen_option)
        return self.chosen_option


class DecisionSystem:
    def __init__(self, score_system=None):
        self.score_system = score_system
        self.current_decision: Optional[Decision] = None
        self.recent_feedback: Optional[Dict[str, Any]] = None
        self.feedback_timer: float = 0.0

    def trigger_decision(self, decision: Decision):
        self.current_decision = decision
        self.recent_feedback = None

    def is_active(self) -> bool:
        return self.current_decision is not None and not self.current_decision.resolved

    def handle_input(self, action: str) -> bool:
        """Handle navigation (up/down) and confirm (confirm/space/enter)."""
        if not self.is_active():
            return False

        if action in ("up", "prev"):
            self.current_decision.prev_option()
            return True
        elif action in ("down", "next"):
            self.current_decision.next_option()
            return True
        elif action in ("confirm", "interact", "select"):
            outcome = self.current_decision.confirm(self.score_system)
            self.recent_feedback = outcome
            self.feedback_timer = 4.0
            return True
        return False

    def update(self, dt: float):
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.recent_feedback = None
                self.current_decision = None
