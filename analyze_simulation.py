import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def analyze_simulation_results(input_csv_path="simulation_results.csv", output_csv_path="summary_results.csv"):
    try:
        df = pd.read_csv(input_csv_path)

        # 주요 지표 요약
        summary_df = df[['time', 'total_household_assets', 'total_firm_assets',
                         'unemployment_rate', 'avg_goods_price', 'avg_wage',
                         'total_production', 'total_consumption', 'total_inventory']]

        # CSV로 저장
        summary_df.to_csv(output_csv_path, index=False)
        logging.info(f"Summary results saved to {output_csv_path}")

    except FileNotFoundError:
        logging.error(f"Error: Input file not found at {input_csv_path}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    analyze_simulation_results()
