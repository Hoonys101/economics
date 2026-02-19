# Genealogy System + API Endpoints Report

## Architectural Insights
1. **Genealogy Service Architecture**:
   - Implemented a dedicated `GenealogyService` in `modules/demographics/genealogy/service.py`.
   - The service depends on `IAgentRegistry` to access agent data, ensuring loose coupling and adhering to the "Logic Separation" guardrail.
   - It performs graph traversal on the `parent_id` and `children_ids` fields of `Household` agents to reconstruct lineage.

2. **DTO Purity**:
   - Defined strict Pydantic models in `modules/demographics/genealogy/dtos.py` (`AncestorDTO`, `DescendantDTO`, `GenealogyTreeDTO`, `GenealogyNodeDTO`).
   - All API endpoints return these typed DTOs, preventing raw dictionary leakage and ensuring schema validation.

3. **API Integration**:
   - Created a new router in `modules/demographics/genealogy/router.py`.
   - The router uses a dependency injection pattern (`get_genealogy_service`) to access the global simulation state safely, handling potential import cycles via runtime imports.
   - Integrated into `server.py` via `app.include_router()`.

4. **Zero-Sum Integrity**:
   - The genealogy system is read-only and does not affect financial state, thus preserving zero-sum integrity.

## Test Evidence
Ran `python -m pytest modules/demographics/genealogy/tests/test_genealogy.py`.

```
modules/demographics/genealogy/tests/test_genealogy.py::test_get_ancestors PASSED [ 25%]
modules/demographics/genealogy/tests/test_genealogy.py::test_get_descendants PASSED [ 50%]
modules/demographics/genealogy/tests/test_genealogy.py::test_get_tree PASSED [ 75%]
modules/demographics/genealogy/tests/test_genealogy.py::test_api_endpoints
-------------------------------- live log call ---------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/genealogy/3/ancestors "HTTP/1.1 200 OK"
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/genealogy/2/descendants "HTTP/1.1 200 OK"
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/genealogy/2/tree "HTTP/1.1 200 OK"
PASSED                                                                   [100%]

============================== 4 passed in 0.95s ===============================
```
