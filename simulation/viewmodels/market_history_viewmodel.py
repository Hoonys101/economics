from typing import List, Dict, Any, Optional
from simulation.db.repository import SimulationRepository

class MarketHistoryViewModel:
    """
    시장 이력 데이터를 웹 UI에 제공하기 위한 ViewModel입니다.
    SimulationRepository를 통해 데이터를 조회하고, 필요한 형태로 가공합니다.
    """
    def __init__(self, repository: Optional[SimulationRepository] = None):
        self.repository = repository if repository else SimulationRepository()

    def get_market_history(self, market_id: str, start_tick: Optional[int] = None, end_tick: Optional[int] = None, item_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        특정 시장의 이력 데이터를 조회하여 반환합니다.
        """
        history = self.repository.get_market_history(market_id, start_tick, end_tick, item_id)
        return history

    def get_market_price_data(self, market_id: str, item_id: str, start_tick: Optional[int] = None, end_tick: Optional[int] = None) -> Dict[str, List[Any]]:
        """
        특정 시장 및 아이템의 평균 가격 차트 데이터를 Chart.js 형식에 맞게 가공하여 반환합니다.
        """
        history = self.get_market_history(market_id, start_tick, end_tick, item_id)
        times = [h['time'] for h in history]
        avg_prices = [h['avg_price'] for h in history]
        
        return {
            "labels": times,
            "datasets": [
                {
                    "label": f"{item_id} 평균 가격 ({market_id})",
                    "data": avg_prices,
                    "borderColor": "rgb(153, 102, 255)",
                    "tension": 0.1
                }
            ]
        }

    def get_market_trade_volume_data(self, market_id: str, item_id: str, start_tick: Optional[int] = None, end_tick: Optional[int] = None) -> Dict[str, List[Any]]:
        """
        특정 시장 및 아이템의 거래량 차트 데이터를 Chart.js 형식에 맞게 가공하여 반환합니다.
        """
        history = self.get_market_history(market_id, start_tick, end_tick, item_id)
        times = [h['time'] for h in history]
        trade_volumes = [h['trade_volume'] for h in history]
        
        return {
            "labels": times,
            "datasets": [
                {
                    "label": f"{item_id} 거래량 ({market_id})",
                    "data": trade_volumes,
                    "backgroundColor": "rgba(255, 205, 86, 0.2)",
                    "borderColor": "rgb(255, 205, 86)",
                    "borderWidth": 1
                }
            ]
        }

if __name__ == '__main__':
    # 테스트 코드
    # 이 테스트를 실행하기 전에 simulation_data.db 파일이 존재하고 데이터가 채워져 있어야 합니다.
    # main.py를 한 번 실행하여 데이터를 생성한 후 이 테스트를 실행하세요.
    
    repo = SimulationRepository()
    vm = MarketHistoryViewModel(repo)
    
    # 예시: 상품 시장의 'food' 아이템 이력 조회
    print("Goods Market Food History (all):", vm.get_market_history(market_id='goods_market', item_id='food'))
    print("\nGoods Market Food Price Data (Chart.js format):", vm.get_market_price_data(market_id='goods_market', item_id='food'))
    print("\nLabor Market Trade Volume Data (Chart.js format):", vm.get_market_trade_volume_data(market_id='labor_market', item_id='labor'))

    repo.close()
