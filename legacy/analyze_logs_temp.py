from log_selector import select_logs

for i in range(100): 
    imitation_logs_df = select_logs(agent_type='Household', method_name='Imitation Debug', tick_start=i, tick_end=i, return_df=True)
    if not imitation_logs_df.empty:
        print(f'\n--- Tick {i} Imitation Debug Logs ---')
        for index, row in imitation_logs_df.iterrows():
            print(f"Tick: {int(row['tick'])}, ID: {row['agent_id']}, Message: {row['message']}")