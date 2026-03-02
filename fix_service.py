with open('modules/housing/service.py', 'r') as f:
    content = f.read()

content = content.replace("lien['lien_type']", "lien.lien_type")

old_str1 = """        new_lien: LienDTO = {
            "loan_id": loan_id_str,
            "lienholder_id": int(lienholder_id_val) if lienholder_id_val is not None else -1,
            "principal_remaining": int(principal_val) if principal_val is not None else 0,
            "lien_type": "MORTGAGE"
        }"""
new_str1 = """        new_lien = LienDTO(
            loan_id=loan_id_str,
            lienholder_id=int(lienholder_id_val) if lienholder_id_val is not None else -1,
            principal_remaining=int(principal_val) if principal_val is not None else 0,
            lien_type="MORTGAGE"
        )"""
content = content.replace(old_str1, new_str1)

old_str2 = """                new_lien: LienDTO = {
                    "loan_id": loan_id,
                    "lienholder_id": lender_id,
                    "principal_remaining": loan_principal,
                    "lien_type": "MORTGAGE"
                }"""
new_str2 = """                new_lien = LienDTO(
                    loan_id=loan_id,
                    lienholder_id=lender_id,
                    principal_remaining=loan_principal,
                    lien_type="MORTGAGE"
                )"""
content = content.replace(old_str2, new_str2)

content = content.replace("l['loan_id']", "l.loan_id")
content = content.replace("lien['loan_id']", "lien.loan_id")

content = content.replace("{unit_id)", "{unit_id}")
content = content.replace("{seller_id)", "{seller_id}")
content = content.replace("{buyer.id)", "{buyer.id}")
content = content.replace("{tx.item_id)", "{tx.item_id}")
content = content.replace("{e)", "{e}")
content = content.replace("{tx_type)", "{tx_type}")
content = content.replace("{item_id)", "{item_id}")


with open('modules/housing/service.py', 'w') as f:
    f.write(content)

with open('tests/unit/systems/test_housing_service.py', 'r') as f:
    test_content = f.read()

test_content = test_content.replace("l['loan_id']", "l.loan_id")
test_content = test_content.replace("l['lien_type']", "l.lien_type")

with open('tests/unit/systems/test_housing_service.py', 'w') as f:
    f.write(test_content)
