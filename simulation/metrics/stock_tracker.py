"""
주식 시장 지표 추적기

기업별 주가, 거래량, 성과 지표를 추적합니다.
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
import logging
from statistics import median

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.markets.stock_market import StockMarket

logger = logging.getLogger(__name__)


class StockMarketTracker:
    """주식 시장 지표 추적기"""

    def __init__(self, config_module: Any):
        self.config_module = config_module
        
        # 이전 틱의 기업 데이터 (수익률 계산용)
        self.previous_firm_data: Dict[int, Dict[str, float]] = {}
        
    def track_firm_stock_data(
        self,
        firm: "Firm",
        stock_market: "StockMarket",
    ) -> Dict[str, Any]:
        """
        개별 기업의 주식 시장 데이터를 수집합니다.
        """
        firm_id = firm.id
        
        # 주가 정보
        stock_price = stock_market.get_stock_price(firm_id) or 0.0
        bps = firm.get_book_value_per_share()
        pbr = stock_price / bps if bps > 0 else 0.0
        
        # 거래량 및 주문 정보
        summary = stock_market.get_market_summary(firm_id)
        trade_volume = summary.get("daily_volume", 0.0)
        buy_order_count = summary.get("buy_order_count", 0)
        sell_order_count = summary.get("sell_order_count", 0)
        
        # 기업 실적
        firm_assets = firm.assets
        firm_profit = getattr(firm, "current_profit", 0.0)
        dividend_paid = getattr(firm, "last_dividend_paid", 0.0)
        market_cap = firm.get_market_cap(stock_price)
        
        return {
            "firm_id": firm_id,
            "stock_price": stock_price,
            "book_value_per_share": bps,
            "price_to_book_ratio": pbr,
            "trade_volume": trade_volume,
            "buy_order_count": buy_order_count,
            "sell_order_count": sell_order_count,
            "firm_assets": firm_assets,
            "firm_profit": firm_profit,
            "dividend_paid": dividend_paid,
            "market_cap": market_cap,
        }
    
    def track_all_firms(
        self,
        firms: List["Firm"],
        stock_market: "StockMarket",
    ) -> List[Dict[str, Any]]:
        """
        모든 기업의 주식 시장 데이터를 수집합니다.
        """
        results = []
        for firm in firms:
            if firm.is_active:
                data = self.track_firm_stock_data(firm, stock_market)
                results.append(data)
        return results
    
    def calculate_aggregate_metrics(
        self,
        firms: List["Firm"],
        stock_market: "StockMarket",
    ) -> Dict[str, Any]:
        """
        주식 시장 집계 지표를 계산합니다.
        """
        if not firms:
            return {}
        
        active_firms = [f for f in firms if f.is_active]
        
        total_market_cap = 0.0
        total_volume = 0.0
        prices = []
        
        for firm in active_firms:
            price = stock_market.get_stock_price(firm.id) or 0.0
            market_cap = firm.get_market_cap(price)
            volume = stock_market.daily_volumes.get(firm.id, 0.0)
            
            total_market_cap += market_cap
            total_volume += volume
            if price > 0:
                prices.append(price)
        
        avg_price = sum(prices) / len(prices) if prices else 0.0
        
        return {
            "stock_market_total_market_cap": total_market_cap,
            "stock_market_total_volume": total_volume,
            "stock_market_avg_price": avg_price,
            "stock_market_active_firms": len(active_firms),
        }


class PersonalityStatisticsTracker:
    """성향별 통계 추적기"""

    def __init__(self, config_module: Any):
        self.config_module = config_module
        
        # 이전 틱의 가계 자산 (증가율 계산용)
        self.previous_assets: Dict[int, float] = {}
    
    def calculate_personality_statistics(
        self,
        households: List["Household"],
        stock_market: Optional["StockMarket"] = None,
    ) -> List[Dict[str, Any]]:
        """
        성향별 통계를 계산합니다.
        """
        from simulation.ai.enums import Personality
        
        # 성향별 그룹화
        groups: Dict[str, List["Household"]] = {
            "MISER": [],
            "STATUS_SEEKER": [],
            "GROWTH_ORIENTED": [],
        }
        
        for h in households:
            if hasattr(h, "personality") and h.is_active:
                personality_name = h.personality.name
                if personality_name in groups:
                    groups[personality_name].append(h)
        
        results = []
        
        for personality_type, members in groups.items():
            if not members:
                continue
            
            stats = self._calculate_group_statistics(
                personality_type, members, stock_market
            )
            results.append(stats)
        
        return results
    
    def _calculate_group_statistics(
        self,
        personality_type: str,
        members: List["Household"],
        stock_market: Optional["StockMarket"],
    ) -> Dict[str, Any]:
        """개별 성향 그룹의 통계를 계산합니다."""
        n = len(members)
        
        # 기본 자산 통계
        assets = [h.assets for h in members]
        avg_assets = sum(assets) / n
        median_assets = median(assets)
        
        # 고용 통계
        employed_count = sum(1 for h in members if h.is_employed)
        employment_rate = employed_count / n
        
        # 포트폴리오 통계
        portfolio_values = []
        stock_holdings = []
        
        for h in members:
            portfolio_value = 0.0
            total_shares = 0.0
            
            if stock_market is not None:
                for firm_id, shares in h.shares_owned.items():
                    price = stock_market.get_stock_price(firm_id) or 0.0
                    portfolio_value += shares * price
                    total_shares += shares
            
            portfolio_values.append(portfolio_value)
            stock_holdings.append(total_shares)
        
        # 욕구 통계
        survival_needs = [h.needs.get("survival", 0.0) for h in members]
        social_needs = [h.needs.get("social", 0.0) for h in members]
        improvement_needs = [h.needs.get("improvement", 0.0) for h in members]
        
        # 자산 증가율
        growth_rates = []
        for h in members:
            prev_assets = self.previous_assets.get(h.id)
            if prev_assets is not None and prev_assets > 0:
                growth_rate = (h.assets - prev_assets) / prev_assets
                growth_rates.append(growth_rate)
            self.previous_assets[h.id] = h.assets
        
        avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
        
        return {
            "personality_type": personality_type,
            "count": n,
            "avg_assets": avg_assets,
            "median_assets": median_assets,
            "avg_labor_income": 0.0,  # TODO: 소득 추적 필요
            "avg_capital_income": 0.0,  # TODO: 소득 추적 필요
            "labor_income_ratio": 0.0,
            "employment_rate": employment_rate,
            "avg_portfolio_value": sum(portfolio_values) / n,
            "avg_stock_holdings": sum(stock_holdings) / n,
            "avg_survival_need": sum(survival_needs) / n,
            "avg_social_need": sum(social_needs) / n,
            "avg_improvement_need": sum(improvement_needs) / n,
            "avg_wealth_growth_rate": avg_growth_rate,
        }
