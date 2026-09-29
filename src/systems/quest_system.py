class QuestSystem:
    """Tracks objectives. Listens to events, so items/NPCs don't know about quests."""

    def __init__(self, quest_defs, events):
        self.events = events
        self.quests = []
        for q in quest_defs:
            self.quests.append({
                "id": q["id"],
                "title": q["title"],
                "type": q["type"],          # collect / talk / reach
                "target": q["target"],
                "required": q.get("count", 1),
                "progress": 0,
                "done": False,
            })
        events.subscribe("item_collected", self.on_item)
        events.subscribe("npc_talked", self.on_talk)
        events.subscribe("area_reached", self.on_reach)

    def _advance(self, quest_type, target):
        for q in self.quests:
            if q["done"] or q["type"] != quest_type or q["target"] != target:
                continue
            q["progress"] += 1
            if q["progress"] >= q["required"]:
                q["done"] = True
                self.events.emit("quest_completed", quest_id=q["id"], title=q["title"])

    def on_item(self, item_id, **_):
        self._advance("collect", item_id)

    def on_talk(self, npc_id, **_):
        self._advance("talk", npc_id)

    def on_reach(self, area_id, **_):
        self._advance("reach", area_id)

    def all_done(self):
        return all(q["done"] for q in self.quests)

    def done_count(self):
        return sum(1 for q in self.quests if q["done"])