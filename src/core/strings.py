"""All menu text in English and Filipino. Add a language by adding a key to each dict."""
from src.core import prefs

STRINGS = {
    "en": {
        "new_game": "NEW GAME", "continue": "CONTINUE", "guide": "DISASTER GUIDE",
        "options": "OPTIONS", "exit": "EXIT", "back": "BACK",
        "language": "LANGUAGE", "lang_name": "ENGLISH",
        "sfx": "SOUND FX", "on": "ON", "off": "OFF",
        "guide_title": "DISASTER GUIDE", "options_title": "OPTIONS",
        "hint_guide": "LEFT / RIGHT: PAGE     ESC: BACK",
        "hint_options": "UP / DOWN: MOVE     ENTER: CHANGE     ESC: BACK",
        "NORMAL": "NORMAL", "WATCH": "WATCH", "WARNING": "WARNING", "CRITICAL": "CRITICAL",
        "h_typhoon": "TYPHOON", "h_flood": "FLOOD", "h_earthquake": "EARTHQUAKE",
        "h_volcano": "ERUPTION", "h_wildfire": "WILDFIRE",
    },
    "fil": {
        "new_game": "BAGONG LARO", "continue": "ITULOY", "guide": "GABAY",
        "options": "OPSYON", "exit": "LUMABAS", "back": "BUMALIK",
        "language": "WIKA", "lang_name": "FILIPINO",
        "sfx": "TUNOG", "on": "BUKAS", "off": "SARADO",
        "guide_title": "GABAY SA SAKUNA", "options_title": "OPSYON",
        "hint_guide": "KALIWA / KANAN: PAHINA     ESC: BUMALIK",
        "hint_options": "PATAAS / PABABA: LIPAT     ENTER: PALITAN     ESC: BUMALIK",
        "NORMAL": "NORMAL", "WATCH": "BANTAY", "WARNING": "BABALA", "CRITICAL": "KRITIKAL",
        "h_typhoon": "BAGYO", "h_flood": "BAHA", "h_earthquake": "LINDOL",
        "h_volcano": "PAGSABOG", "h_wildfire": "SUNOG",
    },
}

TIPS = {
    "en": [
        "TIP: Pack your go-bag before the typhoon, not during it.",
        "TIP: Drop, Cover, and Hold On when the ground shakes.",
        "TIP: Never cross flooded roads. Turn around, don't drown.",
        "TIP: Know your barangay evacuation center.",
        "TIP: Keep a battery radio. Signals go down first.",
        "TIP: Wear a mask or damp cloth during volcanic ashfall.",
        "TIP: Never burn trash in dry grass. One spark can start a wildfire.",
        "TIP: Stay out of the volcano's Permanent Danger Zone.",
        "TIP: Check for cracks and gas leaks after an earthquake.",
        "BAYANSAFE v0.1 - Made for disaster awareness",
    ],
    "fil": [
        "TIP: Ihanda ang go-bag bago ang bagyo, hindi habang may bagyo.",
        "TIP: Yumuko, Magtakip, at Kumapit kapag lumindol.",
        "TIP: Huwag tumawid sa baha. Mas ligtas ang umiwas.",
        "TIP: Alamin ang evacuation center ng inyong barangay.",
        "TIP: Magtabi ng radyong de-baterya. Unang nawawala ang signal.",
        "TIP: Magsuot ng maskara o basang tela kapag may ashfall.",
        "TIP: Huwag magsunog ng basura sa tuyong damo. Isang siklab, sunog na.",
        "TIP: Lumayo sa Permanent Danger Zone ng bulkan.",
        "TIP: Suriin ang bitak at gas leak pagkatapos ng lindol.",
        "BAYANSAFE v0.1 - Para sa kamalayan sa sakuna",
    ],
}

# Page order must match ACCENTS in guide_state.py
GUIDE = {
    "en": [
        {"title": "TYPHOON", "lines": [
            "Watch the PAGASA wind signals (1 to 5).",
            "Secure windows, roof and loose objects early.",
            "Charge phones, store water, and pack your go-bag.",
            "If told to evacuate, go before the storm hits.",
        ]},
        {"title": "EARTHQUAKE", "lines": [
            "DROP to your hands and knees.",
            "COVER your head and neck under a sturdy table.",
            "HOLD ON until the shaking stops.",
            "Then move to an open area. Watch for aftershocks.",
        ]},
        {"title": "FLOOD", "lines": [
            "Move to higher ground at the first warning.",
            "Never walk or drive through floodwater.",
            "Turn off the electricity if water enters your home.",
            "Boil or treat water before drinking it.",
        ]},
        {"title": "VOLCANIC ERUPTION", "lines": [
            "Stay out of the Permanent Danger Zone.",
            "Wear a mask and goggles to protect from ashfall.",
            "Cover water and food. Close all windows.",
            "Evacuate early when the alert level rises.",
        ]},
        {"title": "WILDFIRE", "lines": [
            "Never burn trash in dry grass or forests.",
            "If you see smoke, call the fire station fast.",
            "Cover your nose with a wet cloth and stay low.",
            "Leave early and follow the evacuation route.",
        ]},
    ],
    "fil": [
        {"title": "BAGYO", "lines": [
            "Subaybayan ang Wind Signal ng PAGASA (1 hanggang 5).",
            "Ayusin agad ang bintana, bubong, at mga bagay na liliparin.",
            "I-charge ang cellphone, mag-imbak ng tubig, ihanda ang go-bag.",
            "Kapag may utos na lumikas, umalis bago dumating ang bagyo.",
        ]},
        {"title": "LINDOL", "lines": [
            "YUMUKO at lumuhod sa lapag.",
            "TAKPAN ang ulo at leeg sa ilalim ng matibay na mesa.",
            "KUMAPIT hanggang tumigil ang pagyanig.",
            "Pagkatapos, pumunta sa bukas na lugar. Mag-ingat sa aftershock.",
        ]},
        {"title": "BAHA", "lines": [
            "Lumipat sa mataas na lugar sa unang babala.",
            "Huwag lumusong o magmaneho sa baha.",
            "Patayin ang kuryente kung pumasok ang tubig sa bahay.",
            "Pakuluan o gamutin ang tubig bago inumin.",
        ]},
        {"title": "PAGSABOG NG BULKAN", "lines": [
            "Lumayo sa Permanent Danger Zone.",
            "Magsuot ng maskara at goggles laban sa abo.",
            "Takpan ang tubig at pagkain. Isara ang bintana.",
            "Lumikas agad kapag tumaas ang alert level.",
        ]},
        {"title": "SUNOG SA GUBAT", "lines": [
            "Huwag magsunog ng basura sa tuyong damo.",
            "Kapag may usok, tumawag agad sa bumbero.",
            "Takpan ang ilong ng basang tela at dumapa.",
            "Lumikas nang maaga at sundin ang evacuation route.",
        ]},
    ],
}


def _lang():
    lang = prefs.get("language")
    return lang if lang in STRINGS else "en"


def tr(key):
    return STRINGS[_lang()].get(key, STRINGS["en"].get(key, key))


def tips():
    return TIPS[_lang()]


def guide():
    return GUIDE[_lang()]