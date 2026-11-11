"""Score and Preparedness Tracking System for BayanSafe.

Tracks user preparedness decisions, warnings followed, residents assisted,
evacuations executed, and unsafe actions across all chapters. Determines
which of the 3 canonical story endings is triggered at the conclusion.
"""

from typing import Dict, Any, List


class ScoreSystem:
    def __init__(self):
        self.warnings_followed: int = 0
        self.evacuations_completed: int = 0
        self.residents_assisted: int = 0
        self.unsafe_actions: int = 0
        self.supplies_secured: int = 0
        self.choices_log: List[Dict[str, Any]] = []

    def record_choice(self, prompt: str, choice_text: str, is_safe: bool, lesson: str = ""):
        """Record a player decision in a scenario."""
        entry = {
            "prompt": prompt,
            "choice": choice_text,
            "safe": is_safe,
            "lesson": lesson,
        }
        self.choices_log.append(entry)
        if is_safe:
            self.warnings_followed += 1
        else:
            self.unsafe_actions += 1

    def assist_resident(self, resident_name: str):
        """Record a successful rescue/evacuation assistance for a resident."""
        self.residents_assisted += 1

    def complete_evacuation(self, chapter_id: str):
        """Record successful evacuation to safe high ground or shelter."""
        self.evacuations_completed += 1

    def collect_supply(self, item_name: str):
        """Record an essential supply item gathered."""
        self.supplies_secured += 1

    def get_summary(self) -> Dict[str, Any]:
        """Calculate score metrics and determine ending."""
        total_actions = self.warnings_followed + self.unsafe_actions
        preparedness_ratio = (
            (self.warnings_followed / total_actions) if total_actions > 0 else 1.0
        )
        
        # Ending evaluation:
        # Ending 1 (Complete Victory): High preparedness ratio (>= 0.75), low unsafe actions (<= 2), residents saved
        # Ending 2 (Partial Victory): Moderate preparedness (>= 0.45)
        # Ending 3 (Total Failure): Low preparedness (< 0.45) or high unsafe actions (> 5)
        if preparedness_ratio >= 0.75 and self.unsafe_actions <= 2:
            ending_id = "ending_1_complete_victory"
            ending_title = "Complete Victory: A Community Restored"
            status = "safe"
        elif preparedness_ratio >= 0.45 and self.unsafe_actions <= 5:
            ending_id = "ending_2_partial_victory"
            ending_title = "Partial Victory: A Costly Recovery"
            status = "caution"
        else:
            ending_id = "ending_3_total_failure"
            ending_title = "Total Failure: Warnings Ignored"
            status = "critical"

        return {
            "warnings_followed": self.warnings_followed,
            "evacuations_completed": self.evacuations_completed,
            "residents_assisted": self.residents_assisted,
            "unsafe_actions": self.unsafe_actions,
            "supplies_secured": self.supplies_secured,
            "preparedness_ratio": round(preparedness_ratio * 100, 1),
            "ending_id": ending_id,
            "ending_title": ending_title,
            "status": status,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for save state."""
        return {
            "warnings_followed": self.warnings_followed,
            "evacuations_completed": self.evacuations_completed,
            "residents_assisted": self.residents_assisted,
            "unsafe_actions": self.unsafe_actions,
            "supplies_secured": self.supplies_secured,
            "choices_log": self.choices_log,
        }

    def from_dict(self, data: Dict[str, Any]):
        """Restore from save state."""
        if not data:
            return
        self.warnings_followed = data.get("warnings_followed", 0)
        self.evacuations_completed = data.get("evacuations_completed", 0)
        self.residents_assisted = data.get("residents_assisted", 0)
        self.unsafe_actions = data.get("unsafe_actions", 0)
        self.supplies_secured = data.get("supplies_secured", 0)
        self.choices_log = data.get("choices_log", [])
