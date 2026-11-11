"""Hazard systems for BayanSafe."""

from src.hazards.base_hazard import BaseHazard
from src.hazards.typhoon import TyphoonHazard
from src.hazards.flash_flood import FlashFloodHazard, SevereFloodingHazard
from src.hazards.earthquake import EarthquakeHazard
from src.hazards.landslide import LandslideHazard, TsunamiHazard, FlashFireHazard, VolcanicEruptionHazard

__all__ = [
    "BaseHazard",
    "TyphoonHazard",
    "FlashFloodHazard",
    "SevereFloodingHazard",
    "EarthquakeHazard",
    "LandslideHazard",
    "TsunamiHazard",
    "FlashFireHazard",
    "VolcanicEruptionHazard",
]
