modules/simulation/api.py
```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Protocol, runtime_checkable, Any
from modules.system.api import AgentID, SimulationState

@dataclass
class DeathResultDTO:
    """
    Result of the DeathSystem's evaluation.
    Follows the SEO Pattern: The Engine identifies who dies, the Orchestrator executes the removal.
    """
    dead_agent_ids: List[AgentID] = field(default_factory=list)
    inheritance_map: Dict[AgentID, AgentID] = field(default_factory=dict) # Key: Dead Agent, Value: Heir Agent
    liquidated_assets: Dict[AgentID, Dict[str, Any]] = field(default_factory=dict) # Assets to be transferred/auctioned
    cause_of_death: Dict[AgentID, str] = field(default_factory=dict) # For telemetry

@runtime_checkable
class IDeathEngine(Protocol):
    """
    Protocol for the Death System Engine.
    Must be pure: evaluates state and returns a decision DTO.
    """
    def evaluate_mortality(self, state: SimulationState) -> DeathResultDTO:
        """
        Scans agents in SimulationState for death conditions (starvation, age).
        Returns a DTO containing the IDs of agents to be removed.
        Does NOT mutate state.agents.
        """
        ...

@runtime_checkable
class IMissionScanner(Protocol):
    """
    Protocol for the Mission Auto-Discovery Service.
    Parses specification files to extract mission metadata without runtime imports.
    """
    def scan_directory(self, root_path: str) -> List[Dict[str, Any]]:
        """
        Scans target directory for *_SPEC.md files.
        Parses headers/frontmatter to return raw mission data dicts.
        """
        ...

    def parse_spec_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parses a single spec file content.
        """
        ...
```

design/3_work_artifacts/specs/MISSION_wave7_dx_automation_SPEC.md
```markdown
# MISSION SPEC: wave7-dx-automation

## 1. Objective
To modernize the developer experience (DX) by automating the mission registration process and to resolve a performance bottleneck in the agent lifecycle system.

## 2. Scope
- **Component**: `_internal/registry`, `modules/simulation`
- **Tech Debt Resolved**:
    - `TD-DX-AUTO-CRYSTAL` (Mission Registration Friction)
    - `TD-SYS-PERF-DEATH` (O(N) Death Rebuild)

## 3. Detailed Design

### 3.1. Auto-Discovery Service (`SpecScanner`)
Instead of manually editing `gemini_manifest.py`, we will implement a file-system scanner that reads Markdown spec files directly.

#### Logic (Pseudo-code)
```python
class MarkdownSpecScanner(IMissionScanner):
    def scan_directory(self, root_path: Path):
        specs = []
        # Walk directory looking for *_SPEC.md
        for file in root_path.glob("artifacts/specs/*_SPEC.md"):
            data = self.parse_spec_file(file)
            if data: specs.append(data)
        return specs

    def parse_spec_file(self, file_path):
        # Read file as TEXT (Do not import)
        content = file_path.read_text()
        
        # Parse Mission Key
        key_match = re.search(r"# MISSION SPEC: ([\w-]+)", content)
        if not key_match: return None
        
        # Parse Objectives/Instructions (Simple heuristic)
        # ... extract text between headers ...
        
        return {
            "key": key_match.group(1),
            "type": "GEMINI",
            "file_path": str(file_path)
            # ...
        }
```
**Constraint**: Strict avoidance of `importlib`. Use `re` (Regex) or simple string parsing to avoid side-effects and circular imports.

### 3.2. Death System Optimization (`Mark & Sweep`)
The current O(N) dictionary rebuild in `death_system.py` is unsafe and slow. We will refactor to use the **SEO Pattern** with a `DeathResultDTO`.

#### 3.2.1. Engine Refactor (`IDeathEngine`)
The `DeathSystem` will no longer receive `SimulationState` to mutate. It will strictly analyze and report.

```python
# modules/simulation/system/death.py

class DeathSystem(IDeathEngine):
    def evaluate_mortality(self, state: SimulationState) -> DeathResultDTO:
        result = DeathResultDTO()
        
        # Iteration is safe here as we are NOT modifying state.agents
        for agent_id, agent in state.agents.items():
            if self._should_die(agent):
                result.dead_agent_ids.append(agent_id)
                # ... handle inheritance logic ...
                
        return result
```

#### 3.2.2. Orchestrator Update (`SimulationEngine`)
The orchestrator handles the dangerous operation of removing keys from the dictionary.

```python
# simulation/engine.py

def _handle_deaths(self, state: SimulationState):
    # 1. MARK (Think)
    death_result = self.death_system.evaluate_mortality(state)
    
    # 2. SWEEP (Act)
    if death_result.dead_agent_ids:
        # Optimization: O(K) where K is dead agents
        for agent_id in death_result.dead_agent_ids:
            # Safe localized removal
            if agent_id in state.agents:
                del state.agents[agent_id] # or .pop()
                
        # 3. REPORT
        self.logger.log_deaths(death_result)
```

## 4. Verification Plan

### 4.1. New Test Cases
- **Test Auto-Discovery**:
    - Create a dummy `temp_SPEC.md`.
    - Run `SpecScanner.parse_spec_file`.
    - Assert correct Key and Metadata extraction.
- **Test Death Performance**:
    - Mock `SimulationState` with 10,000 agents.
    - Mark 5 agents as dead.
    - Measure time for `evaluate_mortality` + `del` loop.
    - Assert `state.agents` count decreased by 5.

### 4.2. Existing Test Impact
- **`test_death_system.py`**:
    - Will likely break because the signature of `process` or `evaluate` changes.
    - **Action**: Update test to expect `DeathResultDTO` return instead of checking side-effects on the passed state object immediately.
- **`launcher.py` Integration**:
    - Verify `python launcher.py sync` triggers the new scanner.

### 4.3. Risk Audit
- **Concurrency**: The 'Sweep' phase must happen when no other thread/process is iterating `state.agents`. This is guaranteed by the synchronous Tick Lifecycle.
- **Data Loss**: Ensure `inheritance_map` in DTO captures assets before deletion.

## 5. Mandatory Reporting
- [ ] Create `communications/insights/wave7-dx-automation.md` with findings.
- [ ] Log any performance benchmarks comparing O(N) vs O(K) removal.
```

communications/insights/wave7-dx-automation.md
```markdown
# Insight Report: wave7-dx-automation

## 1. Architectural Insights
- **Scanner Pattern**: Adopting a "Static Analysis" approach (Text Parsing) for Mission Discovery is significantly safer than "Dynamic Discovery" (Runtime Import). It decouples the Registry tool from the complex dependency graph of the Simulation engine.
- **Death System SEO**: Moving the Death System to a pure SEO pattern (returning `DeathResultDTO`) not only solves the O(N) performance issue but also eliminates a class of "RuntimeError: dictionary changed size" bugs. This reinforces the architectural standard that **Agents/Engines do not mutate the Universe; they only request changes**.

## 2. Technical Debt Analysis
- **Resolved**: 
    - `TD-DX-AUTO-CRYSTAL`: Manual manifest editing is replaced by file presence.
    - `TD-SYS-PERF-DEATH`: Dictionary rebuilding replaced by targeted deletion.
- **Created**: None expected.
- **Risk**: The Regex parser for Spec files might be brittle if Markdown formatting varies wildly. Standardizing the Spec Header format is crucial.

## 3. Testing Strategy
- **Unit**: Verify `SpecScanner` against various valid/invalid MD files.
- **Integration**: Verify `launcher.py sync` correctly populates `mission_db.json`.
- **Performance**: Benchmark `DeathSystem` with N=10k.

## 4. Protocol & DTO Audit
- Defined `DeathResultDTO` in `modules/simulation/api.py`.
- Defined `IMissionScanner` protocol for future extensibility (e.g., scanning Python docstrings).
```