import pandas as pd


def select_logs(
    filename="simulation_results.csv",
    agent_type=None,
    agent_id=None,
    method_name=None,
    tick_start=None,
    tick_end=None,
    message_contains=None,
    item_id=None,
    return_df=False,
):
    try:
        df = pd.read_csv(filename)

        filtered_df = df.copy()

        if agent_type is not None:
            filtered_df = filtered_df[filtered_df["agent_type"] == agent_type]
        if agent_id is not None:
            filtered_df = filtered_df[filtered_df["agent_id"] == agent_id]
        if method_name is not None:
            filtered_df = filtered_df[filtered_df["method_name"] == method_name]
        if message_contains is not None:
            filtered_df = filtered_df[
                filtered_df["message"].str.contains(message_contains, na=False)
            ]
        if item_id is not None:
            filtered_df = filtered_df[filtered_df["item_id"] == item_id]

        if tick_start is not None:
            filtered_df = filtered_df[filtered_df["time"] >= tick_start]
        if tick_end is not None:
            filtered_df = filtered_df[filtered_df["time"] <= tick_end]
            return filtered_df

        if filtered_df.empty:
            print("No data found matching the criteria.")
        else:
            # Print all columns for EconomicIndicatorTracker logs
            print(filtered_df.to_string())

    except FileNotFoundError:
        print(f"Error: Log file not found at {filename}")
        return pd.DataFrame()  # 빈 DataFrame 반환
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()  # 빈 DataFrame 반환


def count_filtered_logs(
    filename="simulation_results.csv",
    agent_type=None,
    agent_id=None,
    method_name=None,
    tick_start=None,
    tick_end=None,
    message_contains=None,
    item_id=None,
):
    try:
        df = pd.read_csv(filename)

        filtered_df = df.copy()

        if tick_start is not None:
            filtered_df = filtered_df[filtered_df["time"] >= tick_start]
        if tick_end is not None:
            filtered_df = filtered_df[filtered_df["time"] <= tick_end]

        return len(filtered_df)

    except FileNotFoundError:
        print(f"Error: Log file not found at {filename}")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0


if __name__ == "__main__":
    # EconomicIndicatorTracker 로그 확인
    print("\n--- Economic Indicator Tracker Results ---")
    select_logs(filename="simulation_results.csv")
