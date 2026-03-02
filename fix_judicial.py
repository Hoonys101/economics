with open('modules/governance/judicial/system.py', 'r') as f:
    content = f.read()

content = content.replace("agent_id = event['agent_id']", "agent_id = event['agent_id'] if isinstance(event, dict) else event.agent_id")
content = content.replace("creditor_id = event['creditor_id']", "creditor_id = event['creditor_id'] if isinstance(event, dict) else event.creditor_id")
content = content.replace("amount = int(event['defaulted_amount'])", "amount = int(event['defaulted_amount'] if isinstance(event, dict) else event.defaulted_amount)")
content = content.replace("loan_id = event.loan_id", "loan_id = event['loan_id'] if isinstance(event, dict) else event.loan_id")
content = content.replace("tick = event['tick']", "tick = event['tick'] if isinstance(event, dict) else event.tick")

with open('modules/governance/judicial/system.py', 'w') as f:
    f.write(content)
