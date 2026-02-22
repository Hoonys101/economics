from enum import Enum

class IndustryDomain(str, Enum):
    """
    Wave 3: Standardized Industry Domains.
    Replaces string literals in 'major' fields.
    """
    FOOD_PROD = "FOOD_PROD"       # Was FOOD / AGRICULTURE
    MANUFACTURING = "MANUFACTURING" # Was GOODS / MANUFACTURING
    TECHNOLOGY = "TECHNOLOGY"     # Was TECH
    FINANCE = "FINANCE"
    REAL_ESTATE = "REAL_ESTATE"
    SERVICES = "SERVICES"         # Was SERVICE
    EDUCATION = "EDUCATION"
    HEALTH = "HEALTH"
    GOVERNMENT = "GOVERNMENT"
    RAW_MATERIALS = "RAW_MATERIALS" # Was MATERIAL (sector)
    LUXURY_GOODS = "LUXURY_GOODS"   # Was LUXURY (sector)
    GENERAL = "GENERAL"           # Fallback / Unskilled
