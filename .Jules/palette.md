## 2024-05-22 - [Accessibility in Hybrid UI]
**Learning:** This project mixes Bootstrap 5 and Tailwind CSS. While Bootstrap handles some accessibility (like modal focus management), custom components (like the transaction list) and dynamic updates (Status cards) often lack ARIA attributes.
**Action:** When adding new dynamic UI elements, explicitly check `aria-live` needs and ensure custom containers like `div` scroll areas have `tabindex="0"` if they replace native scrolling regions.

## 2024-05-22 - [State Feedback]
**Learning:** The control panel buttons did not reflect the simulation state (Running/Paused), leading to potential user error (clicking Start multiple times).
**Action:** Always pair async control actions with immediate UI feedback (disabling buttons, spinners) before the backend confirms the state change.
