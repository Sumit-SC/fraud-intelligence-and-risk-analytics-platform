import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import numpy as np
import os

fake = Faker()
random.seed(42)
np.random.seed(42)

BASE_PATH = "data/raw"

def ensure_dirs():
    subdirs = [
        "transactions",
        "merchants",
        "devices",
        "cards",
        "rules",
        "investigations",
    ]
    for s in subdirs:
        os.makedirs(os.path.join(BASE_PATH, s), exist_ok=True)

def generate_merchants(n=2000):
    """
    Generate merchants and return a mapping of merchant_id -> risk_tier
    so transactions can correlate fraud with merchant risk.
    """
    rows = []
    risk_by_merchant = {}
    for i in range(n):
        merchant_id = f"m_{i:05d}"
        risk_tier = random.choice(["LOW", "MEDIUM", "HIGH"])
        rows.append({
            "merchant_id": merchant_id,
            "merchant_name": fake.company(),
            "mcc": random.choice([5411, 5812, 5732, 5311, 5541]),
            "country": random.choice(["IN", "US", "GB", "DE", "SG"]),
            "risk_tier": risk_tier,
        })
        risk_by_merchant[merchant_id] = risk_tier
    df = pd.DataFrame(rows)
    df.to_csv(f"{BASE_PATH}/merchants/merchants.csv", index=False)
    return risk_by_merchant

def generate_devices(n=5000):
    """
    Generate devices and return a mapping of device_id -> is_emulator
    so transactions can correlate fraud with emulator usage.
    """
    rows = []
    emulator_by_device = {}
    for i in range(n):
        device_id = f"d_{i:06d}"
        is_emulator = random.choice([0, 0, 0, 1])  # skewed toward non-emulator
        rows.append({
            "device_id": device_id,
            "os": random.choice(["Android", "iOS", "Windows", "Linux"]),
            "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
            "is_emulator": is_emulator,
        })
        emulator_by_device[device_id] = is_emulator
    pd.DataFrame(rows).to_csv(f"{BASE_PATH}/devices/devices.csv", index=False)
    return emulator_by_device

def generate_cards(n=8000):
    rows = []
    for i in range(n):
        rows.append({
            "card_id": f"c_{i:06d}",
            "bin": random.randint(400000, 559999),
            "issuer": random.choice(["HDFC", "ICICI", "SBI", "CHASE", "CITI"]),
            "card_type": random.choice(["DEBIT", "CREDIT"]),
        })
    pd.DataFrame(rows).to_csv(f"{BASE_PATH}/cards/cards.csv", index=False)


def generate_transactions(
    month,
    merchant_risk_map,
    device_emulator_map,
    n=150_000,
):
    """
    Generate transactions for a given month with scenario-based fraud labels.

    Fraud probability is driven by:
      - high transaction amount
      - high-risk merchants
      - emulator devices
      - foreign (non-IN) countries
    plus a low base rate and some label noise.
    """
    merchants = [f"m_{i:05d}" for i in range(2000)]
    devices = [f"d_{i:06d}" for i in range(5000)]
    cards = [f"c_{i:06d}" for i in range(8000)]

    start = datetime.strptime(month, "%Y-%m")
    rows = []

    for i in range(n):
        ts = start + timedelta(
            seconds=random.randint(0, 30 * 24 * 3600)
        )
        amount = round(np.random.lognormal(3.2, 1.1), 2)

        card_id = random.choice(cards)
        merchant_id = random.choice(merchants)
        device_id = random.choice(devices)
        channel = random.choice(["WEB", "MOBILE", "API"])
        country = random.choice(["IN", "US", "GB", None])  # missing values

        # --- Scenario-based fraud probability ---
        # Base fraud rate (<1%)
        p_fraud = 0.003

        # High amount → higher risk
        if amount > 10000:
            p_fraud += 0.03
        if amount > 50000:
            p_fraud += 0.07

        # High-risk merchants
        merchant_risk = merchant_risk_map.get(merchant_id, "LOW")
        if merchant_risk == "HIGH":
            p_fraud += 0.04
        elif merchant_risk == "MEDIUM":
            p_fraud += 0.01

        # Emulator devices
        is_emulator = device_emulator_map.get(device_id, 0)
        if is_emulator == 1:
            p_fraud += 0.03

        # Foreign country (non-IN) when country is present
        if country is not None and country != "IN":
            p_fraud += 0.02

        # Cap probability to avoid extremes
        p_fraud = min(p_fraud, 0.3)

        # Sample true fraud label
        is_fraud_true = random.random() < p_fraud

        # Inject label noise:
        #   - false negatives: flip ~10% of true frauds to non-fraud
        #   - false positives: flip ~0.3% of non-frauds to fraud
        if is_fraud_true:
            if random.random() < 0.10:  # 10% false negatives
                is_fraud_observed = 0
            else:
                is_fraud_observed = 1
        else:
            if random.random() < 0.003:  # rare false positives
                is_fraud_observed = 1
            else:
                is_fraud_observed = 0

        rows.append({
            "txn_id": f"tx_{month}_{i}",
            "txn_ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "device_id": device_id,
            "channel": channel,
            "country": country,
            "auth_result": random.choice(["APPROVED", "DECLINED", None]),
            "is_fraud": is_fraud_observed,
        })

        # introduce duplicates
        if random.random() < 0.01:
            rows.append(rows[-1])

    df = pd.DataFrame(rows)
    df.to_csv(
        f"{BASE_PATH}/transactions/transactions_{month}.csv",
        index=False
    )

def generate_rule_hits():
    rows = []
    for i in range(50_000):
        rows.append({
            "txn_id": f"tx_2024-01_{random.randint(0,149999)}",
            "rule_name": random.choice([
                "HIGH_AMOUNT",
                "VELOCITY_1H",
                "IP_REUSE",
                "ODD_COUNTRY"
            ]),
            "rule_score": random.randint(10, 90)
        })
    pd.DataFrame(rows).to_csv(
        f"{BASE_PATH}/rules/rule_hits.csv",
        index=False
    )

def generate_investigator_notes():
    notes = []
    for i in range(5000):
        notes.append({
            "txn_id": f"tx_2024-01_{random.randint(0,149999)}",
            "note_text": random.choice([
                "Cardholder reported unauthorized transaction.",
                "Merchant previously linked to fraud ring.",
                "Device fingerprint inconsistent.",
                "Multiple failed attempts before success."
            ]),
            "created_at": fake.date_time_this_year()
        })
    pd.DataFrame(notes).to_csv(
        f"{BASE_PATH}/investigations/investigator_notes.csv",
        index=False
    )

# if __name__ == "__main__":
#     ensure_dirs()
#     generate_merchants()
#     generate_devices()
#     generate_cards()
#     generate_transactions("2024-01")
#     generate_transactions("2024-02")
#     generate_rule_hits()
#     generate_investigator_notes()

if __name__ == "__main__":
    ensure_dirs()
    merchant_risk_map = generate_merchants()
    device_emulator_map = generate_devices()
    generate_cards()

    # Generate 12 months of transactions: 2024-01 to 2024-12
    for month in [
        "2024-01", "2024-02", "2024-03", "2024-04",
        "2024-05", "2024-06", "2024-07", "2024-08",
        "2024-09", "2024-10", "2024-11", "2024-12",
    ]:
        generate_transactions(month, merchant_risk_map, device_emulator_map)

    generate_rule_hits()
    generate_investigator_notes()
