import pytest
from modules.household.political_component import PoliticalComponent
from modules.household.dtos import SocialStateDTO
from simulation.ai.enums import Personality, PoliticalParty

def test_initialize_state_growth_oriented():
    comp = PoliticalComponent()
    vision, trust = comp.initialize_state(Personality.GROWTH_ORIENTED)
    # Base 0.9 +/- 0.15 noise -> 0.75 to 1.0 (clamped)
    assert 0.75 <= vision <= 1.0
    assert trust == 0.5

def test_initialize_state_conservative():
    comp = PoliticalComponent()
    vision, trust = comp.initialize_state(Personality.CONSERVATIVE)
    # Base 0.3 +/- 0.15 -> 0.15 to 0.45
    assert 0.15 <= vision <= 0.45
    assert trust == 0.5

def test_update_opinion_match():
    comp = PoliticalComponent()
    # High vision (Growth), Low Survival Need (Satisfied), Gov Blue (Growth)
    state = SocialStateDTO(
        personality=Personality.GROWTH_ORIENTED,
        social_status=0.0, discontent=0.0, approval_rating=0,
        conformity=0.5, social_rank=0.5, quality_preference=0.5,
        brand_loyalty={}, last_purchase_memory={}, patience=0.5, optimism=0.5, ambition=0.5,
        last_leisure_type="", demand_elasticity=1.0,
        economic_vision=0.9, trust_score=0.5
    )

    # Gov Blue -> Stance 0.9. Match = 1.0 - |0.9 - 0.9| = 1.0
    # Survival Need 10 -> Discontent 0.1, Satisfaction 0.9
    # Approval = 0.4*0.9 + 0.6*1.0 = 0.36 + 0.6 = 0.96

    new_state = comp.update_opinion(state, survival_need=10.0, gov_party=PoliticalParty.BLUE)

    assert new_state.approval_rating == 1
    assert new_state.discontent == 0.1
    # Trust should increase: 0.95*0.5 + 0.05*0.9 = 0.475 + 0.045 = 0.52
    assert new_state.trust_score > 0.5

def test_update_opinion_mismatch_and_discontent():
    comp = PoliticalComponent()
    # High vision (Growth), High Survival Need (Dissatisfied), Gov Red (Safety)
    state = SocialStateDTO(
        personality=Personality.GROWTH_ORIENTED,
        social_status=0.0, discontent=0.0, approval_rating=1,
        conformity=0.5, social_rank=0.5, quality_preference=0.5,
        brand_loyalty={}, last_purchase_memory={}, patience=0.5, optimism=0.5, ambition=0.5,
        last_leisure_type="", demand_elasticity=1.0,
        economic_vision=0.9, trust_score=0.5
    )

    # Gov Red -> Stance 0.1. Match = 1.0 - |0.9 - 0.1| = 0.2
    # Survival Need 80 -> Discontent 0.8, Satisfaction 0.2
    # Approval = 0.4*0.2 + 0.6*0.2 = 0.08 + 0.12 = 0.2

    new_state = comp.update_opinion(state, survival_need=80.0, gov_party=PoliticalParty.RED)

    assert new_state.approval_rating == 0
    assert new_state.discontent == 0.8
    # Trust should decrease: 0.95*0.5 + 0.05*0.2 = 0.475 + 0.01 = 0.485
    assert new_state.trust_score < 0.5

def test_trust_damper():
    comp = PoliticalComponent()
    # Trust very low
    state = SocialStateDTO(
        personality=Personality.GROWTH_ORIENTED,
        social_status=0.0, discontent=0.0, approval_rating=1,
        conformity=0.5, social_rank=0.5, quality_preference=0.5,
        brand_loyalty={}, last_purchase_memory={}, patience=0.5, optimism=0.5, ambition=0.5,
        last_leisure_type="", demand_elasticity=1.0,
        economic_vision=0.9, trust_score=0.1
    )

    # Perfect match and satisfaction
    new_state = comp.update_opinion(state, survival_need=0.0, gov_party=PoliticalParty.BLUE)

    # Calculated approval would be high, but trust < 0.2 -> damper -> 0
    # New trust will update: 0.95*0.1 + 0.05*1.0 = 0.095 + 0.05 = 0.145 (< 0.2)

    assert new_state.approval_rating == 0
