with open('tests/unit/systems/test_housing_service.py', 'r') as f:
    content = f.read()

old_str = """    unit.liens = [{
        "loan_id": "old_loan",
        "lienholder_id": 99,
        "principal_remaining": 500,
        "lien_type": "MORTGAGE"
    }]"""

new_str = """    from modules.finance.dtos import LienDTO
    unit.liens = [LienDTO(
        loan_id="old_loan",
        lienholder_id=99,
        principal_remaining=500,
        lien_type="MORTGAGE"
    )]"""

content = content.replace(old_str, new_str)

with open('tests/unit/systems/test_housing_service.py', 'w') as f:
    f.write(content)
