import pandas as pd
import random

# Read base dataset
base = pd.read_csv("data/scam_dataset.csv")
new_rows = []

# Scam templates
scam_templates = [
    "This is {entity} calling about your {topic}. Please {action} immediately.",
    "Dear customer, your {account} has been {status}. Call us now to {action}.",
    "Attention! Your {topic} has been flagged. To avoid {status}, please {action}.",
]

fillers = {
    "entity": ["bank security", "IRS", "Amazon support", "Microsoft technician", "Medicare agent", "PayPal verification team", "loan department"],
    "topic": ["credit card", "bank account", "social security", "refund", "subscription", "insurance policy"],
    "action": ["verify your identity", "make a payment", "avoid suspension", "update details", "confirm ownership"],
    "account": ["bank account", "credit card", "insurance policy", "customer account"],
    "status": ["locked", "compromised", "on hold", "under review", "deactivated"],
}

# Generate 1,000 scam lines
for _ in range(1000):
    row = random.choice(scam_templates).format(
        entity=random.choice(fillers["entity"]),
        topic=random.choice(fillers["topic"]),
        action=random.choice(fillers["action"]),
        account=random.choice(fillers["account"]),
        status=random.choice(fillers["status"])
    )
    new_rows.append([row, 1])

# Safe templates
safe_templates = [
    "Hi, this is {entity}. Just confirming your {appointment}.",
    "Hello, this is {company} support. Your {service} has been {status}.",
    "Good afternoon, this is {entity} reminding you about your {appointment}.",
]

fillers_safe = {
    "entity": ["pharmacy", "bank", "insurance company", "hospital", "delivery service", "school", "hotel"],
    "appointment": ["meeting", "pickup", "service appointment", "renewal", "reservation"],
    "company": ["FedEx", "Comcast", "Delta Airlines", "AT&T", "Verizon"],
    "service": ["subscription", "order", "reservation", "shipment"],
    "status": ["confirmed", "shipped", "scheduled", "ready for pickup"],
}

# Generate 1,000 safe lines
for _ in range(1000):
    row = random.choice(safe_templates).format(
        entity=random.choice(fillers_safe["entity"]),
        appointment=random.choice(fillers_safe["appointment"]),
        company=random.choice(fillers_safe["company"]),
        service=random.choice(fillers_safe["service"]),
        status=random.choice(fillers_safe["status"])
    )
    new_rows.append([row, 0])

# Combine & save
df = pd.DataFrame(new_rows, columns=["text", "label"])
base = pd.concat([base, df], ignore_index=True)
base.to_csv("data/scam_dataset_aug.csv", index=False)
print("✅ Saved data/scam_dataset_aug.csv with", len(base), "rows")
