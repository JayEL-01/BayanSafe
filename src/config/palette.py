"""Central color palette for all code-rendered environment blocks and hazard zones.

According to the Visual Style Rule, all environment elements (ground, roads,
buildings, hazards, water, items) are rendered as plain-colored pixel blocks.
All environment colors are configured here.
"""

# Ground & Location Colors
COLOR_GROUND_SAN_ISIDRO   = (48, 88, 64)    # Coastal green grass
COLOR_GROUND_PLATEAU      = (56, 76, 52)    # Mountain highland plateau
COLOR_GROUND_CENTRAL_TOWN = (54, 58, 62)    # Urban pavement / street gray
COLOR_GROUND_HARBOR       = (42, 68, 76)    # Coastal dockside teal-gray
COLOR_GROUND_PLAINS       = (68, 86, 44)    # Agricultural plains green
COLOR_GROUND_VALLEY       = (52, 42, 40)    # Volcanic dark caldera rock
COLOR_GROUND_FACILITY     = (38, 40, 46)    # High-tech complex interior floor
COLOR_GROUND_DEFAULT      = (45, 60, 50)    # General fallback terrain

# Structural Blocks
COLOR_BUILDING_HOUSE      = (110, 80, 56)   # Solid wood/concrete house block
COLOR_BUILDING_DAMAGED    = (74, 52, 42)    # Dark cracked damaged building block
COLOR_BUILDING_SHELTER    = (45, 115, 75)   # Designated Evacuation Center
COLOR_BUILDING_HOSPITAL   = (145, 140, 160) # Health Clinic / Medical Facility
COLOR_BUILDING_RESEARCH   = (60, 85, 120)   # Scientific monitoring station / terminal
COLOR_BUILDING_COMMERCIAL = (130, 95, 65)   # Central town shop / commercial building
COLOR_BUILDING_WAREHOUSE  = (90, 85, 95)    # Harbor warehouse block
COLOR_ROAD                = (75, 78, 82)    # Flat road/pavement block
COLOR_PATH                = (135, 120, 85)  # Dirt trail / path
COLOR_BRIDGE              = (125, 90, 60)   # Sturdy wooden bridge crossing water
COLOR_WATER               = (38, 92, 142)   # Natural stream / river / sea
COLOR_TREE_FOLIAGE        = (32, 70, 40)    # Solid tree canopy block
COLOR_TREE_TRUNK          = (80, 52, 30)    # Solid tree trunk block
COLOR_WALL_COLLISION      = (28, 28, 32)    # Map boundary & impassable walls

# Hazard Danger Zones
COLOR_HAZARD_FLOOD        = (25, 75, 165)   # Rushing floodwater / submerged street
COLOR_HAZARD_FIRE         = (210, 65, 35)   # Flash fire / burning debris zone
COLOR_HAZARD_LANDSLIDE    = (95, 65, 38)    # Landslide debris / collapsed slope
COLOR_HAZARD_UNSTABLE     = (70, 45, 25)    # Unstable hillside slope (do not enter)
COLOR_HAZARD_ASH          = (110, 110, 115) # Heavy ashfall danger zone
COLOR_HAZARD_TSUNAMI      = (30, 160, 180)  # Coastal tsunami inundation zone
COLOR_SAFE_ZONE           = (40, 140, 60)   # Designated safe area / high ground

# Items and Interactive Elements
COLOR_ITEM_GOBAG          = (220, 160, 50)  # Emergency Go-Bag
COLOR_ITEM_WATER          = (70, 150, 220)  # Clean drinking water bottle
COLOR_ITEM_FOOD           = (180, 120, 60)  # Non-perishable food pack
COLOR_ITEM_FIRSTAID       = (220, 70, 70)   # First-Aid Kit
COLOR_ITEM_FLASHLIGHT     = (240, 220, 90)  # Flashlight / Torch
COLOR_ITEM_RADIO          = (120, 130, 140) # Emergency radio device
COLOR_ITEM_KEY            = (230, 190, 60)  # Facility control key
COLOR_ITEM_LOG            = (160, 140, 200) # Research log / recording
COLOR_ITEM_MAP            = (210, 195, 150) # Signal communications map

# UI Accent Colors
COLOR_UI_PANEL            = (38, 25, 16)
COLOR_UI_BORDER           = (195, 150, 78)  # Antique brass
COLOR_UI_TEXT             = (248, 244, 230) # Cream parchment
COLOR_UI_ACCENT           = (255, 190, 61)  # Honey gold
COLOR_UI_DANGER           = (226, 75, 58)   # Coral red
COLOR_UI_SAFE             = (76, 165, 98)   # Sage green
