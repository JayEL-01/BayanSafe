"""Author scene-specific cast names and conversations for the story campaign."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "data" / "stages"

LEGACY_NAMES = {
    "aling_nena": "Aling Nena", "nanay_luz": "Nanay Luz",
    "kapitan_jo": "Kapitan Jo", "lolo_berto": "Lolo Berto",
    "ate_mila": "Ate Mila", "rosa": "Aling Rosa",
    "tarsi_lead": "Response Leader Tarsi", "lola_pilar": "Lola Pilar",
    "mang_tomas": "Mang Tomas", "ate_salma": "Ate Salma",
    "researcher_ana": "Researcher Ana",
}

# Names follow the supplied NPC roster. Existing IDs are deliberately retained:
# quests, rescues, and saved campaign data refer to those stable IDs.
CAST_BY_STAGE = {
    "home_island_tutorial": {"aling_nena": "Aling Rosa"},
    "earthquake": {"kapitan_jo": "Berto"},
    "landslide": {"kapitan_jo": "Berto", "lolo_berto": "Liza"},
    "calm_before_wave": {"nanay_luz": "Lola Teresa"},
    "tsunami": {"nanay_luz": "Mang Lito"},
    "flash_fire": {"ate_mila": "Rico Dela Cruz", "rosa": "Aling Rosa"},
    "central_landslide": {"kapitan_jo": "Mayor Cruz"},
    "central_typhoon": {"aling_nena": "Mayor Cruz"},
    "central_earthquake": {"kapitan_jo": "Mayor Cruz"},
    "central_flash_flood": {"nanay_luz": "Nurse Joy"},
    "harbor_flash_flood": {"nanay_luz": "Mang Lito", "ate_salma": "Sari"},
    "harbor_typhoon": {"aling_nena": "Captain Reyes"},
    "harbor_severe_flood": {"nanay_luz": "Mang Lito"},
    "harbor_fire_tsunami": {"tarsi_lead": "Rico Dela Cruz", "lola_pilar": "Dr. Mira Santos"},
    "approach_quake_landslide": {
        "tarsi_lead": "Rico Dela Cruz", "lola_pilar": "Dr. Mira Santos",
        "mang_tomas": "Mang Lito",
    },
    "plains_typhoon": {"aling_nena": "Kuya Ben"},
    "plains_severe_flood": {"nanay_luz": "Mila"},
    "plains_landslide": {"kapitan_jo": "Kuya Ben", "researcher_ana": "Dr. Elena Reyes"},
    "plains_quake_volcano": {"tarsi_lead": "Rico Dela Cruz", "lola_pilar": "Dr. Mira Santos"},
    "silence_volcano": {"mang_tomas": "Mang Lito"},
    "facility_fire": {"ate_mila": "Tito Ramon", "rosa": "Rhea"},
    "volcano_flash_flood": {"ate_mila": "Tatay Pio", "rosa": "Rhea"},
    "final_typhoon_flood": {
        "tarsi_lead": "Rico Dela Cruz", "lola_pilar": "Dr. Mira Santos",
        "aling_rosa": "Aling Rosa",
    },
    "final_shutdown": {
        "dr_voss": "Dr. Elias Voss", "tarsi_lead": "Engr. Paolo Santos",
        "lola_pilar": "Dr. Mira Santos",
    },
    # Non-campaign legacy scene files are kept playable and use the same cast.
    "typhoon": {"aling_nena": "Aling Rosa"},
    "flood": {"nanay_luz": "Lola Teresa"},
    "severe_flood": {"nanay_luz": "Lola Teresa"},
}

# Every key names an existing NPC ID. Lines are short enough for the in-game
# speech bubbles and written for the location, current hazard, and story beat.
SCENE_LINES = {
    "approach_quake_landslide": {
        "tarsi_lead": (
            ["The earthquake, landslide, and coastal warnings are all active.",
             "Use sturdy cover during shaking, then follow the checked route inland."],
            ["The route is holding. Keep the group together and follow updates from responders."],
        ),
        "lola_pilar": (
            ["The slope blocked the road and I hurt my leg trying to get clear.",
             "Please bring the radio so I can call the team, then carry me to high ground."],
            ["The response team heard my call. Please carry me along the marked safe route."],
        ),
        "mang_tomas": (
            ["The ground is cracking near the coast, and the sea is pulling back.",
             "Help me pass the tsunami warning to the shelter. We must move uphill."],
            ["The warning reached the shelter. Stay inland and away from the river valleys."],
        ),
    },
    "home_island_tutorial": {
        "aling_nena": (
            ["The warning says a typhoon is turning toward our village.",
             "Please help me secure the windows, then bring our go-bag to the shelter."],
            ["You helped our neighbors get ready. Stay with the group and follow the shelter signs."],
        ),
    },
    "typhoon": {
        "aling_nena": (
            ["The typhoon warning has reached the village. Please help secure the windows.",
             "Then bring the go-bag and guide everyone to the community shelter."],
            ["The family is together at the shelter. Keep away from the windows until the all-clear."],
        ),
    },
    "flood": {
        "nanay_luz": (
            ["Rain has turned the creek into fast-moving floodwater.",
             "Take the raised path to high ground. Do not try to cross the current."],
            ["We are above the water now. Wait for local officials to say the route is safe."],
        ),
    },
    "severe_flood": {
        "nanay_luz": (
            ["Floodwater is spreading through the settlement and the low road is gone.",
             "Move people and medicine uphill. Leave belongings behind and stay out of the water."],
            ["Everyone is on high ground. We will wait here for the response team."],
        ),
    },
    "earthquake": {
        "kapitan_jo": (
            ["That aftershock shook the plateau again. Drop, cover, and hold on under a sturdy table.",
             "When the shaking stops, keep clear of cracked cliffs and buildings."],
            ["You checked the route before moving. We will wait for responders before entering damaged places."],
        ),
    },
    "landslide": {
        "kapitan_jo": (
            ["Aftershocks and heavy rain have loosened the plateau slope. A fresh slide can move again without warning.",
             "Keep everyone off the hillside and use the marked stable path."],
            ["The slope is still shifting after the quake. We will report the blocked path and stay uphill."],
        ),
        "lolo_berto": (
            ["I was checking the trail when the hillside gave way. My leg hurts, and rocks are still falling.",
             "Please bring the first-aid kit. Then help me follow the safe route."],
            ["Thank you for the first aid. I can follow you, but let's stay well away from the slope."],
        ),
    },
    "calm_before_wave": {
        "nanay_luz": (
            ["Aftershocks have eased, but the coast has gone strangely quiet and the water is drawing away.",
             "That can mean a tsunami is coming. Leave the beach and go to high ground now."],
            ["We are safely uphill. Keep listening for the all-clear from local officials."],
        ),
    },
    "tsunami": {
        "nanay_luz": (
            ["The tsunami warning is active after the quake. Do not wait to watch the wave or collect things.",
             "Move inland and uphill on foot, away from the shoreline and landslide slopes."],
            ["We made it to high ground. Stay here until officials say it is safe to return."],
        ),
    },
    "flash_fire": {
        "ate_mila": (
            ["A cooking fire has spread to the market stalls, and thick smoke is crossing the street.",
             "Warn the vendors and take the clear exit away from the smoke."],
            ["Everyone is out of the market. Do not go back inside for bags or belongings."],
        ),
        "rosa": (
            ["I am near the clinic, but smoke is making it hard to breathe.",
             "Please bring the spare respirator. I will leave by the clear route with you."],
            ["I have the respirator. I can follow you to the safe area now."],
        ),
    },
    "central_landslide": {
        "kapitan_jo": (
            ["The market fire is out, but the town road is blocked by a fresh slope failure. Do not climb across debris.",
             "Use the checked detour and tell the shelter which streets are closed."],
            ["The detour is holding. We can guide families around the slide without entering it."],
        ),
    },
    "central_typhoon": {
        "aling_nena": (
            ["The market fire and earthquake damaged two streets. Now the typhoon is reaching town.",
             "I have opened the town shelter. Let's guide families there before the winds grow stronger."],
            ["The families are inside the shelter. I will keep the town updated as the storm passes."],
        ),
    },
    "central_earthquake": {
        "kapitan_jo": (
            ["An aftershock has damaged the hospital wing. Keep patients and visitors outside that building.",
             "Move them to the checked assembly area and let responders inspect the structure."],
            ["The patients are in the safe area. Nobody should re-enter until inspectors approve it."],
        ),
    },
    "central_flash_flood": {
        "nanay_luz": (
            ["After the fire, earthquake, and typhoon, runoff is rushing through town and covering the low street.",
             "Take the raised road to the school shelter. Never enter the floodwater, on foot or by car."],
            ["We reached the school by the high road. The water can hide open drains and debris."],
        ),
    },
    "harbor_flash_flood": {
        "nanay_luz": (
            ["A sudden surge is sweeping across the harbor road. The dock is not a safe place to wait.",
             "Take the marked uphill route and leave the boats and cargo behind."],
            ["We are above the flood line now. Stay clear of the harbor until the warning is lifted."],
        ),
        "ate_salma": (
            ["Water is coming over the dock, and I cannot carry the warning radio alone.",
             "Bring the drinking water, then help me reach the uphill shelter."],
            ["Thank you. I can follow you away from the dock and rising water."],
        ),
    },
    "harbor_typhoon": {
        "aling_nena": (
            ["The flash flood has covered the dock road, and now strong winds are pushing boats against the harbor wall.",
             "The harbor master has opened the inland shelter. Let's get everyone off the waterfront."],
            ["Everyone is away from the water. Keep clear of the seawall while the storm passes."],
        ),
    },
    "harbor_severe_flood": {
        "nanay_luz": (
            ["The flash flood and typhoon have left the harbor water rising. The lower road is underwater.",
             "Use the marked high route and do not enter the current to reach the warehouse."],
            ["We are on high ground. Keep away from damaged docks and any water near power lines."],
        ),
    },
    "harbor_fire_tsunami": {
        "tarsi_lead": (
            ["Floodwater and typhoon damage already block the harbor road. Now fire and a tsunami warning add danger.",
             "Use the inland evacuation path. Do not go to the beach, cross floodwater, or enter smoke."],
            ["The harbor group is moving inland. Keep everyone together and follow official alerts."],
        ),
        "lola_pilar": (
            ["I hurt my ankle when the harbor road cracked. The smoke is getting closer.",
             "Please bring the emergency radio so I can call for help, then carry me inland."],
            ["I can hear the response team. Please carry me away from the shore and smoke."],
        ),
    },
    "plains_typhoon": {
        "aling_nena": (
            ["The typhoon is crossing the open plains. The farms and power lines are exposed to the wind.",
             "Leave tools and crops behind; bring the go-bag and guide everyone to the inland shelter."],
            ["We are in the shelter. Stay inside and keep away from windows until officials give the all-clear."],
        ),
    },
    "plains_severe_flood": {
        "nanay_luz": (
            ["The typhoon has pushed water from the overflowing channel across the low fields.",
             "Move people and medicine uphill. Do not enter the channel to clear debris."],
            ["The families and medicines are above the flood line. We will wait for responders."],
        ),
    },
    "plains_landslide": {
        "kapitan_jo": (
            ["Typhoon rain and floodwater have weakened the hillside above the monitoring station. It is slipping.",
             "Use the stable detour and report the blocked farm road to the response team."],
            ["The route is clear enough for the team. No one should cross the fresh slide."],
        ),
        "researcher_ana": (
            ["My station recorded a pulse just before the slope failed. These notes bear Dr. Elias Voss's name.",
             "I hurt my leg. Please bring the first-aid kit; the facility records may explain the pulse."],
            ["Thank you. The readings show the machine sent a pulse before the landslide."],
        ),
    },
    "plains_quake_volcano": {
        "tarsi_lead": (
            ["Typhoon winds, floodwater, and unstable slopes are already dangerous. Now tremors and ashfall begin.",
             "Take cover during shaking, then follow the official inland route. Avoid valleys and slopes."],
            ["The group is clear of the valley. Keep masks on and listen for the next official update."],
        ),
        "lola_pilar": (
            ["I helped the harbor families escape. Now a tremor has blocked our path, and ash hides the road.",
             "Bring the radio so I can call the team. Then carry me along the marked route."],
            ["The team heard us. Please keep me away from the valley and falling rocks."],
        ),
    },
    "silence_volcano": {
        "mang_tomas": (
            ["I heard from the coast that the volcano has gone quiet, but ash is still falling and the alert remains.",
             "Cover your nose and mouth, avoid river valleys, and prepare to evacuate."],
            ["Quiet does not mean safe. We will wait for the official all-clear at the evacuation center."],
        ),
    },
    "facility_fire": {
        "ate_mila": (
            ["The volcano and landslide alerts are still active. An electrical fault has now started a facility fire.",
             "I repair this equipment, but it is not safe to save it. Use the clear exit, stay low, and leave it behind."],
            ["The staff are outside. Nobody should return to the facility while it is burning."],
        ),
        "rosa": (
            ["I am a ranger, not a responder, but I know the service path around the smoke and unstable slopes.",
             "Please bring the spare respirator. I can guide the group once my breathing is protected."],
            ["I can breathe clearly now. Follow me along the service path, away from the smoke."],
        ),
    },
    "volcano_flash_flood": {
        "ate_mila": (
            ["The fire damaged the valley, and rain is mixing ash into fast lahar flows from the volcano slopes.",
             "Stay out of river channels and away from unstable slopes. Move to high ground now."],
            ["We are clear of the channel. Keep watching the slopes for new flows."],
        ),
        "rosa": (
            ["I am guiding people around the valley, but ash and floodwater have cut off my path.",
             "Bring the spare respirator, then help me follow the high route."],
            ["Thank you. I can follow you uphill, away from the ash and lahar channel."],
        ),
    },
    "final_typhoon_flood": {
        "tarsi_lead": (
            ["All eight hazard warnings are active around Mount Talon. This route is our last chance.",
             "Take cover during shaking; avoid floodwater, smoke, ash, and unstable slopes."],
            ["The team is together. We will follow the safest route and keep listening for updates."],
        ),
        "lola_pilar": (
            ["I helped the harbor and plains teams, but floodwater, smoke, ash, and debris now block this road.",
             "I hurt my leg. Bring the radio so I can call for help, then carry me to the control shelter."],
            ["The response team is on the radio. Please carry me away from the flood channel."],
        ),
        "aling_rosa": (
            ["I have seen neighbors help one another at every shelter on this island.",
             "Please bring first aid. We still have families to guide away from the hazards."],
            ["Thank you. I can follow you. Let's keep the families together and move uphill."],
        ),
    },
    "final_shutdown": {
        "dr_voss": (
            ["I am Dr. Elias Voss, the World Engine's creator. I wanted to control disasters.",
             "Instead, I pushed the machine past its limits and made every warning worse.",
             "The research log, control key, and backup cell can help your team shut it down."],
            ["I will answer for what I did. Please stabilize the core and protect the people first."],
        ),
        "tarsi_lead": (
            ["I am Engr. Paolo Santos. The key and backup cell are ready, but the core is unstable.",
             "We need to evacuate the staff, isolate the power, and follow the shutdown checklist."],
            ["The personnel route is open. Choose the shutdown plan that protects people and emergency systems."],
        ),
        "lola_pilar": (
            ["I am Dr. Mira Santos. I hurt my leg during the evacuation, but I can still help the team.",
             "Please bring the first-aid kit, then help me reach the personnel exit."],
            ["Thank you. I can walk with you to the evacuation point now."],
        ),
    },
}


def main():
    for stage_id, cast in CAST_BY_STAGE.items():
        path = STAGES / f"{stage_id}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        scene_lines = SCENE_LINES.get(stage_id, {})
        for npc in data.get("npcs", []):
            npc_id = npc["id"]
            if npc_id in cast:
                old_name, new_name = LEGACY_NAMES.get(npc_id, npc["name"]), cast[npc_id]
                npc["name"] = new_name
                if old_name != new_name:
                    def rename_text(value):
                        if isinstance(value, str):
                            return value.replace(old_name, new_name)
                        if isinstance(value, list):
                            return [rename_text(entry) for entry in value]
                        if isinstance(value, dict):
                            return {key: rename_text(entry) for key, entry in value.items()}
                        return value
                    data = rename_text(data)
                    npc = next(entry for entry in data["npcs"] if entry["id"] == npc_id)
            if npc_id in scene_lines:
                before, after = scene_lines[npc_id]
                npc["dialogue"] = before
                npc["after_dialogue"] = after
            # Keep rescue mechanics and items unchanged, but fix stale names in
            # prompts and make the requested action specific and grammatical.
            name = npc["name"]
            item = npc.get("rescue_item")
            if item:
                item_name = next((entry.get("name", item) for entry in data.get("items", [])
                                  if entry.get("id") == item), item.replace("_", " "))
                hazard_names = data.get("hazards", {}).get("disasters", [])
                if "tsunami" in hazard_names:
                    refuge = "inland high ground"
                elif "flash_fire" in hazard_names or "volcano" in hazard_names:
                    refuge = "the safe route, away from smoke and ash"
                elif "landslide" in hazard_names:
                    refuge = "the marked route, away from the unstable slope"
                elif any(h in hazard_names for h in ("flash_flood", "severe_flood")):
                    refuge = "the marked high ground, away from floodwater"
                else:
                    refuge = "the marked shelter"
                if npc_id == "lola_pilar":
                    npc["rescue_dialogue"] = [f"I cannot walk safely with my injured leg. Bring the {item_name.lower()}, then carry me to {refuge}."]
                    npc["rescue_success_dialogue"] = [f"Thank you. Please carry me to {refuge}."]
                    npc["rescue_hint"] = f"Collect the {item_name.lower()}, then speak with {name} again."
                elif name == "Dr. Mira Santos":
                    npc["rescue_dialogue"] = [f"I am hurt and need the {item_name.lower()} before I can help anyone else. Please bring it, then help me reach {refuge}."]
                    npc["rescue_success_dialogue"] = [f"Thank you. I can continue to {refuge} with you now."]
                    npc["rescue_hint"] = f"Find the {item_name.lower()}, then speak with Dr. Mira Santos again."
                elif name in ("Berto", "Liza", "Mila", "Rhea", "Sari", "Aling Rosa", "Lola Teresa", "Mang Lito"):
                    npc["rescue_dialogue"] = [f"I am stranded and need the {item_name.lower()}. Please bring it, then help me get to {refuge}."]
                    npc["rescue_success_dialogue"] = [f"Thank you. I can follow you to {refuge} now."]
                    npc["rescue_hint"] = f"Find the {item_name.lower()}, then speak with {name} again."

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")

    # Jun is the second named Home Village resident in the supplied roster.
    home_path = STAGES / "home_island_tutorial.json"
    home = json.loads(home_path.read_text(encoding="utf-8"))
    jun = next((npc for npc in home.get("npcs", []) if npc["id"] == "jun"), None)
    if jun is None:
        jun = {"id": "jun", "name": "Jun", "pos": [148, 102],
               "color": [87, 155, 222]}
        home["npcs"].append(jun)
    jun.update({
        "name": "Jun",
        "dialogue": [
            "I heard the typhoon alert at school. I packed water and a flashlight.",
            "I am ready to walk with the other families to the shelter.",
        ],
        "after_dialogue": [
            "Our class is together now. We will stay inside until the all-clear.",
        ],
    })
    home_path.write_text(json.dumps(home, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
