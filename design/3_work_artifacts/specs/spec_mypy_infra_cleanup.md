# Mission Guide: Final MyPy Infra Cleanup & Zero-Error Target

## 1. Objectives
- **Resolve Package Name Errors**: 숫자로 시작하거나 비코드 폴더(`design`, `docs`, `2_operations` 등)에 삽입된 `__init__.py`를 제거하여 MyPy의 'invalid package name' 오류를 해결합니다.
- **Global MyPy Hardening**: `mypy .`를 실행하여 잔존하는 모든 사소한 타입 힌트 에러를 해결합니다.
- **Verification**: 최종적으로 에러 0건(`Success: no issues found`) 상태를 달성합니다.

## 2. Reference Context (MUST READ)
- **Error Log**: `mypy_final_errors.log` (Package name errors)
- **Configuration**: [mypy.ini](file:///c:/coding/economics/mypy.ini) (Strict mode)

## 3. Implementation Roadmap
### Phase 1: Package Marker Cleanup
- 숫자로 시작하는 모든 디렉토리(`^\d`) 내의 `__init__.py`를 삭제하십시오.
- `_internal/design/`, `design/` 등 순수 문서/데이터 폴더 내의 `__init__.py`를 삭제하십시오.

### Phase 2: Systematic Fix
- `mypy . --config-file mypy.ini`를 실행합니다.
- 리포트되는 모든 에러를 하나씩 수정하십시오. 주로 DTO 타입 불일치나 캐스팅 누락일 가능성이 높습니다.

## 4. Verification
- `mypy . --config-file mypy.ini` 실행 시 `Success: no issues found` 출력을 확인하십시오.
