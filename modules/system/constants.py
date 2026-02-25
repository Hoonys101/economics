"""
System-wide constants for transaction types and other identifiers.
Addressing TD-209: Hardcoded Agent Identifiers and Strings.
"""

# Transaction Types
TX_LABOR = "labor"
TX_GOODS = "goods"
TX_REAL_ESTATE = "real_estate" # Generic prefix or type
TX_HOUSING = "housing"
TX_STOCK = "stock"
TX_EMERGENCY_BUY = "emergency_buy"
TX_ASSET_TRANSFER = "asset_transfer"
TX_RESEARCH_LABOR = "research_labor"
TX_TAX = "tax"
TX_SUBSIDY = "subsidy"

# System Agent IDs (Fixed Integers)
ID_CENTRAL_BANK = 0
ID_GOVERNMENT = 1
ID_BANK = 2
ID_ESCROW = 3
ID_PUBLIC_MANAGER = 4
ID_SYSTEM = 5  # System-level distributions (e.g. Inheritance)

# M2 Exclusion Set (Sovereign & System Agents)
# Commercial Banks are excluded by Type (IBank), not just ID.
NON_M2_SYSTEM_AGENT_IDS = {ID_SYSTEM, ID_CENTRAL_BANK, ID_ESCROW, ID_PUBLIC_MANAGER, ID_GOVERNMENT}
