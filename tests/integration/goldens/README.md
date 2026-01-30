# 🧪 Golden Fixtures

이 폴더에는 테스트용 **골든 픽스처** 파일들이 저장됩니다.

## ⚠️ 중요: Mock 생성 시 반드시 이 파일들을 사용하세요!

### ❌ 하지 마세요
```python
# 수동 MagicMock은 타입 불일치 오류를 유발합니다
firm = MagicMock()
firm.id = 100
firm.assets = 5000  # 실제 값과 다를 수 있음
# ... 30줄의 수동 설정 ...
```

### ✅ 이렇게 하세요
```python
# conftest.py의 골든 픽스처를 사용하세요
def test_my_feature(golden_firms):
    # golden_firms는 실제 시뮬레이션 데이터에서 자동 생성됨
    assert golden_firms[0].assets > 0
    snapshot = golden_firms[0].get_financial_snapshot()  # 자동 구현됨!
```

## 📁 파일 목록

| 파일명 | 용도 | 생성일 |
|---|---|---|
| `demo_fixture.json` | 기본 테스트용 (5 가구, 3 기업) | 2026-01-19 |

## 🔧 새 골든 파일 생성

```python
from scripts.fixture_harvester import quick_harvest

# 시뮬레이션 실행 후
quick_harvest(sim, tick=100)
# => tests/goldens/agents_tick_100.json 생성
```

## 📚 관련 파일
- `scripts/fixture_harvester.py` - 수집/로드 도구
- `tests/conftest.py` - pytest 픽스처 정의
