from enum import Enum

class IndustryDomain(str, Enum):
    """
    Wave 3: Standardized Industry Domains.
    Replaces string literals in 'major' fields.
    """
    FOOD = "FOOD"
    MANUFACTURING = "MANUFACTURING"
    TECH = "TECH"
    FINANCE = "FINANCE"
    REAL_ESTATE = "REAL_ESTATE"
    SERVICE = "SERVICE"
    EDUCATION = "EDUCATION"
    HEALTH = "HEALTH"
    GOVERNMENT = "GOVERNMENT"
    GENERAL = "GENERAL"  # Fallback / Unskilled
