from enum import Enum

class IndustryDomain(str, Enum):
    """
    Wave 3: Standardized Industry Domains.
    Replaces string literals in 'major' fields.
    """
    FOOD_PROD = 'FOOD_PROD'
    MANUFACTURING = 'MANUFACTURING'
    TECHNOLOGY = 'TECHNOLOGY'
    FINANCE = 'FINANCE'
    REAL_ESTATE = 'REAL_ESTATE'
    SERVICES = 'SERVICES'
    EDUCATION = 'EDUCATION'
    HEALTH = 'HEALTH'
    GOVERNMENT = 'GOVERNMENT'
    RAW_MATERIALS = 'RAW_MATERIALS'
    LUXURY_GOODS = 'LUXURY_GOODS'
    GENERAL = 'GENERAL'
