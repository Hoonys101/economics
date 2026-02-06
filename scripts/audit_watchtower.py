import os
import subprocess
import sys
from pathlib import Path
import json

# Configuration
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
PROMPTS_DIR = BASE_DIR / "design" / "2_operations" / "prompts"
REPORTS_DIR = BASE_DIR / "reports" / "audits"

# Audit Domains and their Context Groupings
AUDIT_DOMAINS = {
    "AGENTS": {
        "prompt": PROMPTS_DIR / "audit_agents.md",
        "context": [
            "simulation/base_agent.py",
            "simulation/firms.py",
            "simulation/households.py",
            "design/1_governance/architecture/ARCH_AGENTS.md"
        ]
    },
    "FINANCE": {
        "prompt": PROMPTS_DIR / "audit_finance.md",
        "context": [
            "simulation/finance/api.py",
            "simulation/monetary/central_bank.py",
            "simulation/finance/settlement_system.py",
            "design/1_governance/architecture/ARCH_FINANCE.md"
        ]
    },
    "MARKETS": {
        "prompt": PROMPTS_DIR / "audit_markets.md",
        "context": [
            "simulation/interfaces/market_interface.py",
            "simulation/markets/",
            "design/1_governance/architecture/ARCH_MARKETS.md"
        ]
    },
    "SYSTEMS": {
        "prompt": PROMPTS_DIR / "audit_systems.md",
        "context": [
            "simulation/systems/",
            "utils/simulation_builder.py",
            "design/1_governance/architecture/ARCH_SEQUENCING.md"
        ]
    }
}

def run_modular_audit(domain, config):
    print(f"\n🔍 [Watchtower] Starting Modular Audit: {domain}")
    
    # 1. Prepare Command
    cmd = [
        "python", str(SCRIPTS_DIR / "gemini_worker.py"),
        "reporter", f"Perform a strict domain audit for {domain} based on the provided manual.",
        "--context"
    ] + config["context"]
    
    # Use manual_override if we can, but since gemini_worker.py uses a fixed map, 
    # we'll use 'reporter' worker but tell it to use our specific prompt as a context file 
    # OR we can modify gemini_worker.py to accept any manual.
    # For now, let's use the 'reporter' worker but give it the prompt content as instruction.
    
    prompt_content = config["prompt"].read_text(encoding='utf-8')
    instruction = f"{prompt_content}\n\n[TASK]\nRun this audit on the provided context files and output the result."
    
    # Calling via subprocess to keep environments isolated
    # We'll use a temporary file for the instruction if it's too long, but CLI should handle it.
    
    process = subprocess.run(
        ["python", str(SCRIPTS_DIR / "gemini_worker.py"), "reporter", instruction, "--context"] + config["context"],
        capture_output=True, text=True, encoding='utf-8'
    )
    
    if process.returncode != 0:
        print(f"❌ Audit failed for {domain}: {process.stderr}")
        return None
        
    return process.stdout

def run_watchtower():
    print("🦅 [Watchtower Audit] Initiating Recursive Feedback Loop...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    domain_reports = {}
    
    # Phase 1: Modular Integrities
    for domain, config in AUDIT_DOMAINS.items():
        report = run_modular_audit(domain, config)
        if report:
            domain_reports[domain] = report
            # Save modular report
            report_file = REPORTS_DIR / f"audit_{domain.lower()}.md"
            report_file.write_text(report, encoding='utf-8')
            print(f"✅ {domain} Audit Complete -> {report_file.name}")

    # Phase 2: Management Aggregation
    if domain_reports:
        print("\n📈 [Watchtower] Aggregating results for Management...")
        
        agg_instruction = (
            "You are the Lead Management Auditor. Below are modular audit reports for different domains.\n"
            "Your task is to aggregate these findings into a single 'Project Watchtower Audit Report'.\n"
            "Identify global architectural drifts and update the recommended next steps for 'PROJECT_STATUS.md'.\n\n"
        )
        for domain, content in domain_reports.items():
            agg_instruction += f"### {domain} Report Snippet:\n{content[:500]}...\n\n"
            
        # Call Aggregator
        agg_process = subprocess.run(
            ["python", str(SCRIPTS_DIR / "gemini_worker.py"), "context", agg_instruction, "--output", str(REPORTS_DIR / "WATCHTOWER_SUMMARY.md")],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if agg_process.returncode == 0:
            print(f"🏆 Final Watchtower Summary created: {REPORTS_DIR / 'WATCHTOWER_SUMMARY.md'}")
        else:
            print(f"❌ Aggregation failed: {agg_process.stderr}")

if __name__ == "__main__":
    run_watchtower()
