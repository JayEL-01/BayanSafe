"""Cast mapping and character metadata for BayanSafe.

Matches the story script roles to the preserved character sprite assets in
assets/images/characters/ and assets/images/game_art/characters/.
"""

CAST_ROLES = {
    # Player options
    "juan": {
        "name": "Juan",
        "title": "Community Youth Leader",
        "category": "player",
        "sprite_path": "assets/images/characters/juan_walk.png",
        "portrait_path": "assets/images/characters/juan_portrait.png",
        "frame_folder": "assets/images/game_art/player_frames/juan",
    },
    "maria": {
        "name": "Maria",
        "title": "Community Youth Leader",
        "category": "player",
        "sprite_path": "assets/images/characters/maria_walk.png",
        "portrait_path": "assets/images/characters/maria_portrait.png",
        "frame_folder": "assets/images/game_art/player_frames/maria",
    },
    # Companion / Guide
    "tarsi": {
        "name": "Tarsi",
        "title": "Disaster Preparedness Companion",
        "category": "companion",
        "sprite_path": None,  # Procedural pixel sprite
        "portrait_path": None,
    },
    # Antagonist
    "dr_elias_voss": {
        "name": "Dr. Elias Voss",
        "title": "Director of Project Aegis-Terra",
        "category": "antagonist",
        "sprite_path": "assets/images/game_art/characters/dr_elias_voss.png",
        "portrait_path": None,
    },
    # Barangay Officials & Responders
    "captain_reyes": {
        "name": "Captain Reyes",
        "title": "Barangay Captain / Incident Commander",
        "category": "official",
        "sprite_path": "assets/images/game_art/characters/captain_reyes.png",
        "portrait_path": None,
    },
    "mayor_cruz": {
        "name": "Mayor Cruz",
        "title": "Municipal Mayor / MDRRMC Chair",
        "category": "official",
        "sprite_path": "assets/images/game_art/characters/mayor_cruz.png",
        "portrait_path": None,
    },
    # Medical Staff
    "nurse_joy": {
        "name": "Nurse Joy",
        "title": "Rural Health Unit Triage Nurse",
        "category": "medical",
        "sprite_path": "assets/images/game_art/characters/nurse_joy.png",
        "portrait_path": None,
    },
    # Researchers & Technical Staff
    "dr_elena_reyes": {
        "name": "Dr. Elena Reyes",
        "title": "Senior Seismologist",
        "category": "researcher",
        "sprite_path": "assets/images/game_art/characters/dr_elena_reyes.png",
        "portrait_path": None,
    },
    "dr_mira_santos": {
        "name": "Dr. Mira Santos",
        "title": "Hydrologist & Sensor Specialist",
        "category": "researcher",
        "sprite_path": "assets/images/game_art/characters/dr_mira_santos.png",
        "portrait_path": None,
    },
    "engr_paolo_santos": {
        "name": "Engr. Paolo Santos",
        "title": "Civil Infrastructure Engineer",
        "category": "researcher",
        "sprite_path": "assets/images/game_art/characters/engr_paolo_santos.png",
        "portrait_path": None,
    },
    # Community Residents, Farmers, Fishers, Workers
    "aling_rosa": {
        "name": "Aling Rosa",
        "title": "Sari-Sari Store Owner",
        "category": "resident",
        "sprite_path": "assets/images/game_art/characters/aling_rosa.png",
        "portrait_path": None,
    },
    "mang_lito": {
        "name": "Mang Lito",
        "title": "Plateau Rice Farmer",
        "category": "resident",
        "sprite_path": "assets/images/game_art/characters/mang_lito.png",
        "portrait_path": None,
    },
    "tatay_pio": {
        "name": "Tatay Pio",
        "title": "Senior Fisherman",
        "category": "resident",
        "sprite_path": "assets/images/game_art/characters/tatay_pio.png",
        "portrait_path": None,
    },
    "tito_ramon": {
        "name": "Tito Ramon",
        "title": "Harbor Cargo Handler",
        "category": "resident",
        "sprite_path": "assets/images/game_art/characters/tito_ramon.png",
        "portrait_path": None,
    },
    "kuya_ben": {
        "name": "Kuya Ben",
        "title": "Jeepney Driver & Logistics Volunteer",
        "category": "resident",
        "sprite_path": "assets/images/game_art/characters/kuya_ben.png",
        "portrait_path": None,
    },
    "berto": {
        "name": "Berto",
        "title": "Barangay Tanod (Peacekeeper)",
        "category": "resident",
        "sprite_path": "assets/images/game_art/characters/berto.png",
        "portrait_path": None,
    },
    "rico_dela_cruz": {
        "name": "Rico dela Cruz",
        "title": "Community Radio Operator",
        "category": "resident",
        "sprite_path": "assets/images/game_art/characters/rico_dela_cruz.png",
        "portrait_path": None,
    },
    "jun": {
        "name": "Jun",
        "title": "Youth Volunteer & Runner",
        "category": "resident",
        "sprite_path": "assets/images/game_art/characters/jun.png",
        "portrait_path": None,
    },
    # Vulnerable Residents (Elders, Children, Persons with Disabilities)
    "lola_teresa": {
        "name": "Lola Teresa",
        "title": "Elderly Resident",
        "category": "vulnerable",
        "sprite_path": "assets/images/game_art/characters/lola_teresa.png",
        "portrait_path": None,
    },
    "mila": {
        "name": "Mila",
        "title": "Young Mother",
        "category": "vulnerable",
        "sprite_path": "assets/images/game_art/characters/mila.png",
        "portrait_path": None,
    },
    "sari": {
        "name": "Sari",
        "title": "Schoolchild",
        "category": "vulnerable",
        "sprite_path": "assets/images/game_art/characters/sari.png",
        "portrait_path": None,
    },
    "liza": {
        "name": "Liza",
        "title": "Resident with Mobility Impairment",
        "category": "vulnerable",
        "sprite_path": "assets/images/game_art/characters/liza.png",
        "portrait_path": None,
    },
    "rhea": {
        "name": "Rhea",
        "title": "Daycare Student",
        "category": "vulnerable",
        "sprite_path": "assets/images/game_art/characters/rhea.png",
        "portrait_path": None,
    },
}


def get_character_meta(char_key: str) -> dict:
    """Retrieve metadata dictionary for any character key, falling back safely."""
    return CAST_ROLES.get(char_key, {
        "name": char_key.replace("_", " ").title(),
        "title": "Community Member",
        "category": "resident",
        "sprite_path": None,
        "portrait_path": None,
    })
