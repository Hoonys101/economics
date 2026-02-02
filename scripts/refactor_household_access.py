import os
import re

replacements = {
    # Econ
    "assets": "_econ_state.assets",
    "inventory": "_econ_state.inventory",
    "is_employed": "_econ_state.is_employed",
    "employer_id": "_econ_state.employer_id",
    "current_wage": "_econ_state.current_wage",
    "wage_modifier": "_econ_state.wage_modifier",
    "labor_skill": "_econ_state.labor_skill",
    "education_xp": "_econ_state.education_xp",
    "education_level": "_econ_state.education_level",
    "expected_wage": "_econ_state.expected_wage",
    "talent": "_econ_state.talent",
    "skills": "_econ_state.skills",
    "aptitude": "_econ_state.aptitude",
    "portfolio": "_econ_state.portfolio",
    "durable_assets": "_econ_state.durable_assets",
    "owned_properties": "_econ_state.owned_properties",
    "residing_property_id": "_econ_state.residing_property_id",
    "is_homeless": "_econ_state.is_homeless",
    "home_quality_score": "_econ_state.home_quality_score",
    "housing_target_mode": "_econ_state.housing_target_mode",
    "inventory_quality": "_econ_state.inventory_quality",
    "labor_income_this_tick": "_econ_state.labor_income_this_tick",
    "capital_income_this_tick": "_econ_state.capital_income_this_tick",
    "current_consumption": "_econ_state.current_consumption",
    "current_food_consumption": "_econ_state.current_food_consumption",
    "expected_inflation": "_econ_state.expected_inflation",
    "perceived_avg_prices": "_econ_state.perceived_avg_prices",
    "initial_assets_record": "_econ_state.initial_assets_record",
    "credit_frozen_until_tick": "_econ_state.credit_frozen_until_tick",

    # Bio
    "age": "_bio_state.age",
    "gender": "_bio_state.gender",
    "parent_id": "_bio_state.parent_id",
    "generation": "_bio_state.generation",
    "spouse_id": "_bio_state.spouse_id",
    "children_ids": "_bio_state.children_ids",
    "needs": "_bio_state.needs",
    "is_active": "_bio_state.is_active",

    # Social
    "personality": "_social_state.personality",
    "social_status": "_social_state.social_status",
    "approval_rating": "_social_state.approval_rating",
    "discontent": "_social_state.discontent",
    "conformity": "_social_state.conformity",
    "social_rank": "_social_state.social_rank",
    "quality_preference": "_social_state.quality_preference",
    "brand_loyalty": "_social_state.brand_loyalty",
    "last_purchase_memory": "_social_state.last_purchase_memory",
    "patience": "_social_state.patience",
    "optimism": "_social_state.optimism",
    "ambition": "_social_state.ambition",
    "last_leisure_type": "_social_state.last_leisure_type",
    "desire_weights": "_social_state.desire_weights",
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content

    # Handle demographics legacy property
    new_content = re.sub(r'\bhousehold\.demographics\.', 'household.', new_content)
    new_content = re.sub(r'\bh\.demographics\.', 'h.', new_content)

    # Handle shares_owned specially
    new_content = re.sub(r'\bhousehold\.shares_owned\b', 'household._econ_state.portfolio.to_legacy_dict()', new_content)
    new_content = re.sub(r'\bh\.shares_owned\b', 'h._econ_state.portfolio.to_legacy_dict()', new_content)

    # Handle children_count specially
    new_content = re.sub(r'\bhousehold\.children_count\b', 'len(household._bio_state.children_ids)', new_content)
    new_content = re.sub(r'\bh\.children_count\b', 'len(h._bio_state.children_ids)', new_content)

    for old_prop, new_path in replacements.items():
        # Replace household.prop
        pattern1 = r'\bhousehold\.' + old_prop + r'\b'
        repl1 = 'household.' + new_path
        new_content = re.sub(pattern1, repl1, new_content)

        # Replace h.prop
        pattern2 = r'\bh\.' + old_prop + r'\b'
        repl2 = 'h.' + new_path
        new_content = re.sub(pattern2, repl2, new_content)

        # NOTE: Not replacing agent.prop automatically to avoid Firm breakage.

    if new_content != content:
        print(f"Modifying {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

def main():
    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                # Exclude core_agents.py to avoid self-modification loops (though we are deleting properties there manually)
                if file == "core_agents.py":
                    continue
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
