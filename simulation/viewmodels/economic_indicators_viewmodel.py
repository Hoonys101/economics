from typing import List, Dict, Any, Optional
from simulation.db.repository import SimulationRepository
import logging

class EconomicIndicatorsViewModel:
    """
    경제 지표 데이터를 웹 UI에 제공하기 위한 ViewModel입니다.
    SimulationRepository를 통해 데이터를 조회하고, 필요한 형태로 가공합니다.
    """
    def __init__(self, repository: Optional[SimulationRepository] = None):
        self.repository = repository if repository else SimulationRepository()

    def get_economic_indicators(self, start_tick: Optional[int] = None, end_tick: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        경제 지표 데이터를 조회하여 반환합니다.
        """
        indicators = self.repository.get_economic_indicators(start_tick, end_tick)
        # 여기에서 필요에 따라 데이터를 추가 가공할 수 있습니다.
        # 예: 특정 지표만 선택하거나, 포맷을 변경하거나, 평균을 계산하는 등.
        return indicators

    def get_unemployment_rate_data(self, start_tick: Optional[int] = None, end_tick: Optional[int] = None) -> Dict[str, List[Any]]:
        """
        실업률 차트 데이터를 Chart.js 형식에 맞게 가공하여 반환합니다.
        """
        indicators = self.get_economic_indicators(start_tick, end_tick)
        times = [ind['time'] for ind in indicators]
        unemployment_rates = [ind['unemployment_rate'] for ind in indicators]
        
        return {
            "labels": times,
            "datasets": [
                {
                    "label": "실업률",
                    "data": unemployment_rates,
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                }
            ]
        }

    def get_total_production_data(self, start_tick: Optional[int] = None, end_tick: Optional[int] = None) -> Dict[str, List[Any]]:
        """
        총 생산량 차트 데이터를 Chart.js 형식에 맞게 가공하여 반환합니다.
        """
        indicators = self.get_economic_indicators(start_tick, end_tick)
        times = [ind['time'] for ind in indicators]
        total_production = [ind['total_production'] for ind in indicators]
        
        return {
            "labels": times,
            "datasets": [
                {
                    "label": "총 생산량",
                    "data": total_production,
                    "borderColor": "rgb(255, 99, 132)",
                    "tension": 0.1
                }
            ]
        }

    def get_avg_wage_data(self, start_tick: Optional[int] = None, end_tick: Optional[int] = None) -> Dict[str, List[Any]]:
        """
        평균 임금 차트 데이터를 Chart.js 형식에 맞게 가공하여 반환합니다.
        """
        indicators = self.get_economic_indicators(start_tick, end_tick)
        times = [ind['time'] for ind in indicators]
        avg_wages = [ind['avg_wage'] for ind in indicators]
        
        return {
            "labels": times,
            "datasets": [
                {
                    "label": "평균 임금",
                    "data": avg_wages,
                    "borderColor": "rgb(54, 162, 235)",
                    "tension": 0.1
                }
            ]
        }

if __name__ == '__main__':
    # 테스트 코드
    # 이 테스트를 실행하기 전에 simulation_data.db 파일이 존재하고 데이터가 채워져 있어야 합니다.
    # main.py를 한 번 실행하여 데이터를 생성한 후 이 테스트를 실행하세요.
    
    # 임시 데이터베이스 파일 생성 (테스트용)
    # import os
    # if os.path.exists('test_simulation_data.db'):
    #     os.remove('test_simulation_data.db')
    # conn = sqlite3.connect('test_simulation_data.db')
    # from simulation.db.schema import create_tables
    # create_tables(conn)
    # conn.close()
    # from simulation.db.database import DATABASE_NAME
    # original_db_name = DATABASE_NAME
    # DATABASE_NAME = 'test_simulation_data.db' # 테스트용 DB로 변경

    repo = SimulationRepository()
    # 여기에 테스트 데이터를 repo에 저장하는 로직 추가 (예: save_economic_indicator)
    # 예시:
    # for i in range(1, 11):
    #     repo.save_economic_indicator({
    #         'time': i,
    #         'unemployment_rate': 10.0 - i,
    #         'avg_wage': 1000 + i*10,
    #         'food_avg_price': 5.0 + i*0.1,
    #         'total_production': 100 + i*5,
    #         'total_consumption': 50 + i*2,
    #         'total_household_assets': 10000 + i*100,
    #         'total_firm_assets': 5000 + i*50,
    #         'total_food_consumption': 30 + i*1,
    #         'total_inventory': 200 - i*5
    #     })

    vm = EconomicIndicatorsViewModel(repo)
    
    logging.info(f"Economic Indicators (all): {vm.get_economic_indicators()}")
    logging.info(f"Unemployment Rate Data (Chart.js format): {vm.get_unemployment_rate_data()}")
    logging.info(f"Total Production Data (Chart.js format): {vm.get_total_production_data(start_tick=5, end_tick=10)}")
    logging.info(f"Avg Wage Data (Chart.js format): {vm.get_avg_wage_data()}")

    repo.close()
    # if 'original_db_name' in locals():
    #     DATABASE_NAME = original_db_name # 원본 DB 이름으로 복원
    #     os.remove('test_simulation_data.db') # 테스트용 DB 파일 삭제
