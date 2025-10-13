from log_selector import select_logs
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

logging.info("\n--- Searching for 'No sell orders' imitation debug logs ---")
select_logs(agent_type='Household', method_name='Imitation Debug', message_pattern='No sell orders for .* in goods market.')