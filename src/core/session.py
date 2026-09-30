class GameSession:
    """Holds the current run's progress. Saved to the database in Phase 10."""

    STAGE_ORDER = ["typhoon", "flood", "earthquake", "volcano", "wildfire"]

    def __init__(self):
        self.reset()

    def reset(self):
        self.character = None          # dict from characters.json
        self.unlocked = {"typhoon"}
        self.completed = set()

    def is_unlocked(self, stage_id):
        return stage_id in self.unlocked

    def complete_stage(self, stage_id):
        self.completed.add(stage_id)
        index = self.STAGE_ORDER.index(stage_id)
        if index + 1 < len(self.STAGE_ORDER):
            self.unlocked.add(self.STAGE_ORDER[index + 1])
            self.records = {}
    
    def record_run(self, stage_id, stats):
        best = self.records.setdefault(
            stage_id, {"best_time": None, "best_score": 0, "perfect": False}
        )
        if best["best_time"] is None or stats["time"] < best["best_time"]:
            best["best_time"] = stats["time"]
        best["best_score"] = max(best["best_score"], stats["score"])
        best["perfect"] = best["perfect"] or stats["perfect"]