def calculate_position_risk(balance: float, risk_percent: float) -> dict[str, float]:
    risk_amount = balance * (risk_percent / 100)
    return {"balance": balance, "risk_percent": risk_percent, "risk_amount": risk_amount}
