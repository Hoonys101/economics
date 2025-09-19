from log_selector import select_logs

print("\n--- Searching for 'No sell orders' imitation debug logs ---")
select_logs(agent_type='Household', method_name='Imitation Debug', message_pattern='No sell orders for .* in goods market.')