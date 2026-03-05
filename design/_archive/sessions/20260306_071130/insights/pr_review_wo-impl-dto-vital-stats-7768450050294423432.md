🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached 11 context files using Smart Context Injector.
📊 [GeminiWorker] Total Context Size: 131.37 kb (134522 chars)
⚠️ Warning: Context exceeds limit (128000). Truncating.
  ✂️  Dropping Tier 2 (STRUCTURAL): C:\coding\economics\gemini-output\review\pr_diff_wo-impl-dto-vital-stats-7768450050294423432.txt
  📊 After atomic truncation: 112406 chars (10 files retained)
🚀 [GeminiWorker] Running task with manual: git-review.md
🛡️  Memory Guard Active: Limit = 2048MB
📡 [GeminiWorker] Feeding prompt to STDIN (112406 chars)...
✅ [GeminiWorker] STDIN feed complete.
❌ Error: Gemini timeout (180s) reached.
❌ Error: Error executing gemini subprocess: Gemini CLI Error (Code None):
[STDOUT]

[STDERR]
Loaded cached credentials.
Hook registry initialized with 0 hook entries
Error executing tool read_file: File path 'C:\coding\economics\gemini-output\review\pr_diff_wo-impl-dto-vital-stats-7768450050294423432.txt' is ignored by configured ignore patterns.
Error executing tool grep_search: Invalid regular expression pattern provided: (?s)diff --git a/simulation/systems/demographic_manager\.py.*?diff --git a/simulation/systems/immigration_manager\.py. Error: Invalid regular expression: /(?s)diff --git a/simulation/systems/demographic_manager\.py.*?diff --git a/simulation/systems/immigration_manager\.py/: Invalid group


--- STDERR ---
📉 Budget Tight: Stubbing primary tests/integration/test_phase20_integration.py
📉 Budget Tight: Stubbing primary tests/system/test_audit_integrity.py
🛑 Budget Critical: Metadata-only for primary tests/unit/systems/test_demographic_manager_newborn.py
