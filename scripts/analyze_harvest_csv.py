import csv
import statistics


def analyze_harvest():
    data = {
        "tick": [],
        "food_price": [],
        "population": [],
        "engel_coeff": [],
        "total_production": [],
        "total_inventory": [],
        "total_sales": [],
        "active_food_firms": [],
        "avg_firm_cash": [],
    }

    with open("harvest_data.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in data.keys():
                if k in row:
                    data[k].append(float(row[k]))

    # 1. Price Trend
    initial_price = data["food_price"][0]
    final_price = data["food_price"][-1]
    price_drop = (initial_price - final_price) / initial_price
    print(f"Price: {initial_price} -> {final_price} (Drop: {price_drop * 100:.1f}%)")

    # 2. Population Trend
    initial_pop = data["population"][0]
    final_pop = data["population"][-1]
    pop_growth = final_pop / initial_pop
    print(f"Population: {initial_pop} -> {final_pop} (Growth: {pop_growth:.2f}x)")

    # 3. Engel Trend
    print(
        f"Engel Coefficient: Start {data['engel_coeff'][0]:.2f} -> End {data['engel_coeff'][-1]:.2f}"
    )

    # 4. Supply Dynamics
    print(f"Total Inventory (Peak): {max(data['total_inventory'])}")
    print(f"Total Inventory (End): {data['total_inventory'][-1]}")
    print(f"Active Food Firms (End): {data['active_food_firms'][-1]}")

    # 5. Production vs Sales
    avg_production = statistics.mean(data["total_production"])
    avg_sales = statistics.mean(data["total_sales"])
    print(f"Avg Production/Tick: {avg_production:.2f}")
    print(f"Avg Sales/Tick: {avg_sales:.2f}")

    # 6. Check for Price Crash causing insolvency
    # If price < cost, firms lose money.
    # We can infer cost loosely or look at firm cash trend.
    initial_cash = data["avg_firm_cash"][0]
    final_cash = data["avg_firm_cash"][-1]
    print(f"Avg Firm Cash: {initial_cash:.2f} -> {final_cash:.2f}")

    # Detect period where inventory spiked but sales didn't
    # Simple correlation?


if __name__ == "__main__":
    analyze_harvest()
