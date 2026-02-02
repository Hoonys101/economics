import os
import re

# Properties to search for
econ_properties = [
    "assets", "inventory", "is_employed", "employer_id", "current_wage", "wage_modifier",
    "labor_skill", "education_xp", "education_level", "expected_wage", "talent", "skills",
    "aptitude", "portfolio", "shares_owned", "durable_assets", "owned_properties",
    "residing_property_id", "is_homeless", "home_quality_score", "housing_target_mode",
    "inventory_quality", "labor_income_this_tick", "capital_income_this_tick",
    "current_consumption", "current_food_consumption", "expected_inflation",
    "perceived_avg_prices", "initial_assets_record", "credit_frozen_until_tick"
]

bio_properties = [
    "age", "gender", "parent_id", "generation", "spouse_id", "children_ids",
    "children_count", "needs", "is_active"
]

social_properties = [
    "personality", "social_status", "approval_rating", "discontent", "conformity",
    "social_rank", "quality_preference", "brand_loyalty", "last_purchase_memory",
    "patience", "optimism", "ambition", "last_leisure_type", "desire_weights"
]

all_properties = set(econ_properties + bio_properties + social_properties)

pattern = re.compile(r"\.(" + "|".join(all_properties) + r")\b")

def analyze():
    log_file = "refactor_call_sites.log"
    with open(log_file, "w") as f:
        f.write("# Call Sites Analysis\n")

        for root, dirs, files in os.walk("."):
            if ".git" in root or "__pycache__" in root:
                continue

            for file in files:
                if not file.endswith(".py"):
                    continue

                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as py_file:
                        lines = py_file.readlines()
                        for i, line in enumerate(lines):
                            if pattern.search(line):
                                # Filter out definitions (def property...)
                                if "def " in line and "@property" not in lines[i-1]:
                                    # Might be a method def, but we are looking for property usage.
                                    # Actually we want to find property definitions too so we can remove them (in core_agents.py)
                                    pass

                                f.write(f"{filepath}:{i+1}: {line.strip()}\n")
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

if __name__ == "__main__":
    analyze()
