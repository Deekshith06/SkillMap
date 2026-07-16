"""tokens.py — Spacing, radius, shadow tokens as dicts."""

SPACING = {
    "1": "0.25rem",
    "2": "0.5rem",
    "3": "0.75rem",
    "4": "1rem",
    "6": "1.5rem",
    "8": "2rem",
    "12": "3rem",
    "16": "4rem",
}

RADIUS = {
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
    "xl": "16px",
    "pill": "9999px",
}

SHADOWS = {
    "sm": "0 2px 8px rgba(22, 19, 17, 0.04)",
    "md": "0 4px 16px rgba(22, 19, 17, 0.06)",
    "lg": "0 12px 32px rgba(22, 19, 17, 0.08)",
}

TRANSITIONS = {
    "fast": "150ms cubic-bezier(0.4, 0, 0.2, 1)",
    "base": "250ms cubic-bezier(0.4, 0, 0.2, 1)",
    "slow": "350ms cubic-bezier(0.4, 0, 0.2, 1)",
}
