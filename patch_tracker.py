import re

with open('simulation/metrics/economic_tracker.py', 'r') as f:
    content = f.read()

# Replace calculate_social_cohesion
content = re.sub(
    r'def calculate_social_cohesion\(self, households: List\[Household\]\) -> float:.*?return total_trust / len\(active_households\)',
    r'''def calculate_social_cohesion(self, households: List[HouseholdAnalyticsDTO]) -> float:
        """
        TD-015: Calculate Social Cohesion based on average Trust Score of active households.
        """
        active_households = [h for h in households if h.is_active]
        if not active_households:
            return 0.5 # Default neutral

        total_trust = sum(h.trust_score for h in active_households)
        return total_trust / len(active_households)''',
    content, flags=re.DOTALL
)

# Replace calculate_population_metrics
content = re.sub(
    r'def calculate_population_metrics\(self, households: List\[Household\], markets: Optional\[Dict\[str, Market\]\] = None\) -> Dict\[str, Any\]:.*?return \{\n\s+"active_count": active_count,\n\s+"distribution": distribution,\n\s+"all_assets": all_assets\n\s+\}',
    r'''def calculate_population_metrics(self, households: List[HouseholdAnalyticsDTO], markets: Optional[List[MarketAnalyticsDTO]] = None) -> Dict[str, Any]:
        """
        TD-015: Calculate Population Metrics (Distribution, Active Count).
        Returns a dictionary with 'distribution' (quintiles) and 'active_count'.
        Now includes Stock Portfolio value in Total Assets.
        """
        active_households = [h for h in households if h.is_active]
        active_count = len(active_households)

        if not active_households:
            return {
                "active_count": 0,
                "distribution": {f"q{i}": 0.0 for i in range(1, 6)},
                "all_assets": []
            }

        # Calculate assets for Gini
        all_assets = []
        for h in active_households:
             # 1. Cash (Wallet)
             cash_val = float(h.total_cash_pennies) / 100.0

             # 2. Portfolio (Stocks)
             stock_val = float(h.portfolio_value_pennies) / 100.0

             all_assets.append(cash_val + stock_val)

        sorted_assets = sorted(all_assets)

        # Quintiles (Average Assets per Quintile)
        n = len(sorted_assets)
        quintile_size = max(1, n // 5)

        distribution = {}
        for i in range(5):
            start = i * quintile_size
            end = (i + 1) * quintile_size if i < 4 else n
            q_slice = sorted_assets[start:end]
            avg = statistics.mean(q_slice) if q_slice else 0.0
            distribution[f"q{i+1}"] = avg

        return {
            "active_count": active_count,
            "distribution": distribution,
            "all_assets": all_assets
        }''',
    content, flags=re.DOTALL
)

# Replace track with track_tick
track_code = r'''    def track_tick(self, snapshot: EconomyAnalyticsSnapshotDTO) -> None:
        """현재 시뮬레이션 틱의 경제 지표를 계산하고 기록합니다."""
        time = snapshot.tick
        households = snapshot.households
        firms = snapshot.firms
        markets = snapshot.markets
        m2_leak = float(snapshot.m2_leak_pennies) / 100.0

        self.logger.debug(
            f"TRACKER_UPDATE | Starting tracker update for tick {time}",
            extra={"tick": time, "tags": ["tracker"]},
        )
        record: Dict[str, Any] = {"time": time}

        # WO-043: Track Money Supply
        record["money_supply"] = float(snapshot.money_supply_pennies) / 100.0
        record["monetary_base"] = float(snapshot.monetary_base_pennies) / 100.0

        # Perform calculations...
        # TD-213: Tracks all assets converted to DEFAULT_CURRENCY.
        # WO-IMPL-FINANCIAL-PRECISION: Cast to int (Pennies) for strict compliance
        total_household_assets = sum(h.total_cash_pennies for h in households if h.is_active)

        # WO-106: Initial Sink Fix
        total_firm_assets = sum(f.total_assets_pennies for f in firms if f.is_active)

        # WO-IMPL-FINANCIAL-PRECISION: Ensure total_firm_assets is int
        total_firm_assets = int(total_firm_assets)

        record["total_household_assets"] = total_household_assets
        record["total_firm_assets"] = total_firm_assets

        total_households = len([h for h in households if h.is_active])
        unemployed_households = 0
        for h in households:
            if h.is_active:
                if not h.is_employed:
                    unemployed_households += 1
        record["unemployment_rate"] = (
            (unemployed_households / total_households) * 100
            if total_households > 0
            else 0
        )

        # Market Data
        total_volume = 0.0
        weighted_price_sum = 0.0
        food_price_sum = 0.0
        food_volume_sum = 0.0
        primary_food_key = "basic_food"

        for market in markets:
            market_id = market.market_id
            if market_id in ["labor", "loan_market", "stock_market", "housing"]:
                continue

            avg_price = market.avg_price
            volume = market.volume

            if volume > 0:
                weighted_price_sum += avg_price * volume
                total_volume += volume

            if "food" in market_id:
                if volume > 0:
                     food_price_sum += avg_price * volume
                     food_volume_sum += volume

        if food_volume_sum > 0:
            record["food_avg_price"] = int(food_price_sum / food_volume_sum)
        else:
            f_market = next((m for m in markets if m.market_id == primary_food_key), None)
            if f_market:
                 record["food_avg_price"] = int(f_market.avg_price)
            else:
                 record["food_avg_price"] = 0

        record["food_trade_volume"] = food_volume_sum

        if total_volume > 0:
            record["avg_goods_price"] = int(weighted_price_sum / total_volume)
        else:
            fallback_prices = []
            for market in markets:
                market_id = market.market_id
                if market_id in ["labor", "loan_market", "stock_market", "housing"]:
                    continue
                price = market.current_price
                if price <= 0:
                    price = market.avg_price
                if price > 0:
                    fallback_prices.append(price)

            if fallback_prices:
                record["avg_goods_price"] = int(sum(fallback_prices) / len(fallback_prices))
            else:
                record["avg_goods_price"] = 0

        # Sync to goods_price_index for CPI tracking
        record["goods_price_index"] = record["avg_goods_price"]

        # Production & Consumption
        total_production = sum(
            f.current_production
            for f in firms
            if getattr(f, "is_active", False)
        )
        record["total_production"] = total_production

        # WO-IMPL-FINANCIAL-PRECISION: Maintain Penny Standard (int)
        total_consumption = sum(
            h.consumption_expenditure_pennies for h in households if h.is_active
        )
        record["total_consumption"] = int(total_consumption)

        # WO-IMPL-FINANCIAL-PRECISION: Maintain Penny Standard (int)
        total_food_consumption = sum(
            h.food_expenditure_pennies
            for h in households
            if h.is_active
        )
        record["total_food_consumption"] = int(total_food_consumption)

        total_inventory = sum(
            f.inventory_volume for f in firms if f.is_active
        )
        record["total_inventory"] = total_inventory

        # Avg Survival Need
        active_households_count = 0
        total_survival_need = 0.0
        for h in households:
            if h.is_active:
                active_households_count += 1
                total_survival_need += h.survival_need

        record["avg_survival_need"] = (
            total_survival_need / active_households_count
            if active_households_count > 0 else 0.0
        )

        # --- WO-043: Comprehensive Metrics ---
        # 1. Labor Share
        # Sum labor income (pennies). Kept in pennies for reporting parity with GDP (Pennies).
        # WO-IMPL-FINANCIAL-PRECISION: Removed conversion to dollars.
        total_labor_income_pennies = sum(
            h.labor_income_pennies
            for h in households
            if h.is_active
        )
        total_labor_income = total_labor_income_pennies
        record["total_labor_income"] = int(total_labor_income)

        # Sales Volume
        total_sales_volume = sum(
            f.sales_volume for f in firms if f.is_active
        )
        record["total_sales_volume"] = total_sales_volume

        # Nominal GDP
        nominal_gdp = record["total_production"] * record["avg_goods_price"]
        record["gdp"] = nominal_gdp  # Explicitly store as 'gdp'

        if nominal_gdp > 0:
            record["labor_share"] = total_labor_income / nominal_gdp
        else:
            record["labor_share"] = 0.0

        # 2. Velocity of Money
        money_supply_m1 = total_household_assets + total_firm_assets
        if money_supply_m1 > 0:
            record["velocity_of_money"] = nominal_gdp / money_supply_m1
        else:
            record["velocity_of_money"] = 0.0

        # 3. Inventory Turnover
        if total_inventory > 0:
            record["inventory_turnover"] = total_volume / total_inventory
        else:
            record["inventory_turnover"] = 0.0

        # --- Phase 23: Opportunity Index & Education Metrics ---
        total_edu = sum(h.education_level for h in households if h.is_active)
        record["avg_education_level"] = total_edu / total_households if total_households > 0 else 0.0

        brain_waste = [
            h for h in households
            if h.is_active
            and h.aptitude >= 0.8
            and h.education_level < 2.0
        ]
        record["brain_waste_count"] = len(brain_waste)

        # --- TD-015: Centralized Metrics (Gini, Cohesion, Population) ---
        pop_metrics = self.calculate_population_metrics(households, markets)

        record["active_population"] = pop_metrics["active_count"]

        # Quintiles
        dist = pop_metrics["distribution"]
        record["quintile_1_avg_assets"] = dist.get("q1", 0.0)
        record["quintile_2_avg_assets"] = dist.get("q2", 0.0)
        record["quintile_3_avg_assets"] = dist.get("q3", 0.0)
        record["quintile_4_avg_assets"] = dist.get("q4", 0.0)
        record["quintile_5_avg_assets"] = dist.get("q5", 0.0)

        # Gini
        gini = self.calculate_gini_coefficient(pop_metrics["all_assets"])
        record["gini"] = gini

        # Social Cohesion
        cohesion = self.calculate_social_cohesion(households)
        record["social_cohesion"] = cohesion

        for field in self.all_fieldnames:
            record.setdefault(field, 0)

        # Store the record in metrics with bounded size to prevent OOM
        for key, value in record.items():
            if key != "time":
                # Ensure we have a list for this key
                lst = self.metrics.setdefault(key, [])
                lst.append(value)
                # Keep max 2000 points to bound memory usage
                if len(lst) > 2000:
                    lst.pop(0)

        # Update SMA Histories
        self.gdp_history.append(record.get("gdp", 0.0))
        self.cpi_history.append(record.get("goods_price_index", 0.0))
        self.m2_leak_history.append(m2_leak)'''

content = re.sub(
    r'    def track\(.*?self\.m2_leak_history\.append\(m2_leak\)',
    track_code,
    content, flags=re.DOTALL
)

content = content.replace(
    'from simulation.core_agents import Household',
    'from simulation.core_agents import Household\nfrom modules.analytics.api import EconomyAnalyticsSnapshotDTO, HouseholdAnalyticsDTO, FirmAnalyticsDTO, MarketAnalyticsDTO'
)

with open('simulation/metrics/economic_tracker.py', 'w') as f:
    f.write(content)
