# AUDIT_SPEC_CONFIG_COMPLIANCE: Configuration Compliance Audit (v1.0)

**목표**: 코드베이스의 설정 외부화(Externalization) 수준을 검증하여, 하드코딩된 매직 넘버·사용되지 않는 설정·설정 변경의 폭발 반경(Blast Radius) 등을 식별한다.

**관심사 경계 (SoC Boundary)**:
> 이 감사는 오직 **"파라미터가 올바르게 외부화되었는가 (Configuration Hygiene)"**만을 다룬다.
> - ✅ Magic Number (하드코딩 상수) 탐지
> - ✅ Dead Config (YAML에 정의되었으나 코드에서 미참조)
> - ✅ Config Blast Radius (하나의 config → 몇 곳에서 참조?)
> - ✅ 설정-코드 동기화 (config default vs 코드 default 불일치)
> - ❌ 하드코딩이 설계 의도와 맞는가 → `AUDIT_PARITY`
> - ❌ float 하드코딩이 화폐 누수 유발 → `AUDIT_ECONOMIC`
> - ❌ 설정의 구조적 위치/모듈 → `AUDIT_STRUCTURAL`

## 1. 용어 정의 (Terminology)
- **Magic Number**: 비즈니스 로직에 리터럴 숫자가 직접 사용되어, 변경 시 코드 수정이 필요한 상태. 명명된 상수(Named Constant)나 설정 파일로 외부화되어야 함.
- **Dead Config**: `SimulationConfig` YAML이나 설정 dataclass에 정의되었으나, 런타임 코드에서 전혀 참조되지 않는 설정 항목.
- **Config Blast Radius**: 단일 설정 값을 변경했을 때 영향을 받는 코드 위치의 수. 높을수록 변경 위험도가 큼.
- **Default Drift**: 설정 파일의 기본값과 코드의 fallback 기본값이 서로 다른 상태.

## 2. Severity Scoring Rubric

| Severity | 기준 | 예시 |
| :--- | :--- | :--- |
| **Critical** | 핵심 경제 파라미터가 하드코딩 | `interest_rate = 0.03` in production code |
| **High** | Default Drift (설정 vs 코드 불일치) | YAML: `tax_rate: 0.15`, Code: `tax_rate = getattr(config, 'tax_rate', 0.10)` |
| **Medium** | Dead Config 또는 높은 Blast Radius (>10) | YAML에 30개 항목 중 5개 미참조 |
| **Low** | 비핵심 상수 하드코딩 | 로깅 메시지의 숫자, UI 표시용 상수 |

## 3. 감사 범위 (Audit Scope)

### 3.1 Magic Number 탐지
- **탐지**: 비즈니스 로직 파일(`simulation/`, `modules/`)에서 리터럴 숫자를 검색.
  - 패턴: `grep -rnE "=\s*(0\.\d+|\d{4,})" simulation/ modules/` (소수점 상수 및 큰 정수)
- **예외**: `0`, `1`, `-1`, `100`(퍼센트 변환) 등 관용적 상수는 제외.
- **권고**: `modules/finance/constants.py` 또는 `SimulationConfig` 외부화.

### 3.2 Dead Config 탐지
- **방법**: `SimulationConfig` dataclass 또는 YAML의 모든 키를 추출하고, 코드베이스에서 각 키의 참조 횟수를 검색.
- **보고**: 참조 횟수 0인 항목을 "Dead Config"으로 등재.

### 3.3 Config Blast Radius 분석
- **방법**: 주요 설정 키(예: `tax_rate`, `interest_rate`, `initial_capital`)별로 코드에서 참조되는 위치 수를 카운트.
- **보고**: Blast Radius > 10인 항목을 "High Risk Config"으로 등재.

### 3.4 Default Drift 탐지
- **탐지**: `getattr(config, 'key', DEFAULT)` 패턴에서 `DEFAULT` 값이 YAML의 기본값과 다른 경우.
- **보고**: 불일치 항목과 두 값을 나란히 표시.

## 4. Output Configuration
- **Output Location**: `reports/audit/`
- **Recommended Filename**: `AUDIT_REPORT_CONFIG_COMPLIANCE.md`
