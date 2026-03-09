"""Test fixture application with known issues for gate validation."""
import sqlite3


# ISSUE: Hardcoded API key (Layer 0 — secrets hook should catch on write)
API_KEY = "AKIA1234567890ABCDEF"


def get_user(user_id: str) -> dict:
    """Fetch user by ID."""
    # ISSUE: SQL injection vulnerability (Layer 2 — security auditor should catch)
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "email": row[2]}
    return {}


def process_payment(amount: float) -> dict:
    """Process a payment."""
    # ISSUE: Stub — NotImplementedError (Layer 0 — Stop hook + Layer 1 — stub gate)
    raise NotImplementedError


def calculate_tax(amount: float, rate: float) -> float:
    """Calculate tax on amount."""
    # ISSUE: Swallowed error (Layer 1 — stub gate should catch)
    try:
        return amount * rate
    except Exception:
        pass
