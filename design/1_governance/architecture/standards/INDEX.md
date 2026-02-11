# ⚖️ Architectural Standards Index

Welcome to the central repository of architectural rules and coding patterns for the Economics simulation. These standards ensure the integrity, testability, and scalability of our "Living Digital Economy".

---

## 🏛️ 1. Design Patterns
- **[SEO_PATTERN.md](./SEO_PATTERN.md)**: Stateless Engine & Orchestrator. The foundational logic/state separation.
- **[FINANCIAL_INTEGRITY.md](./FINANCIAL_INTEGRITY.md)**: The Penny Standard, Double-Entry rules, and Zero-Sum enforcement.

## 🔌 2. Infrastructure & Lifecycle
- **[LIFECYCLE_HYGIENE.md](./LIFECYCLE_HYGIENE.md)**: Tick sequencing, Late-Reset principle, and state transition safety.
- **[TESTING_STABILITY.md](./TESTING_STABILITY.md)**: Mock Purity, Golden Fixtures, and library-less environment stability.

---

## 🚀 How to use these Standards
1. **In Specs**: Reference the specific standard file (e.g., "Must follow [SEO_PATTERN.md]") in the design principles section.
2. **In Reviews**: Use these files as criteria for checking `Hard-Fail` violations.
3. **In Audits**: Map violations back to the specific standard IDs defined in these documents.