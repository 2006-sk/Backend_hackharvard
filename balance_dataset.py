import pandas as pd
import random

# Read the augmented dataset
print("Loading dataset from data/scam_dataset_aug.csv")
df = pd.read_csv("data/scam_dataset_aug.csv")

# Base templates for sensitive legitimate messages
sensitive_legit_templates = [
    "This is your bank reminding you about your new debit card shipment.",
    "Your loan payment has been received. Thank you for banking with us.",
    "Your electricity account has been credited successfully.",
    "This is Microsoft support confirming your license renewal.",
    "Your password was changed successfully from your request.",
    "Your insurance claim has been approved and will be processed soon.",
    "Your credit card statement is ready for review in your online account.",
    "Your mortgage payment has been processed successfully.",
    "Your investment account statement is now available for download.",
    "Your health insurance claim has been submitted for processing.",
    "Your car insurance policy has been renewed automatically.",
    "Your internet service has been restored after maintenance.",
    "Your phone bill has been paid successfully.",
    "Your retirement account contribution has been processed.",
    "Your tax documents are ready for download from our secure portal."
]

# Base templates for subtle scams
subtle_scams_templates = [
    "We noticed unusual activity on your account, please call our support line.",
    "Your tax refund is ready, please verify your details to claim.",
    "Your Amazon Prime subscription was auto-renewed. To cancel, press one.",
    "Your PayPal account needs re-verification. Click the link to confirm.",
    "We are offering a bonus credit if you update your payment details today.",
    "Your account has been flagged for review, please contact us immediately.",
    "We need to verify your identity to prevent account suspension.",
    "Your payment method has expired, please update to avoid service interruption.",
    "We detected suspicious login attempts, please confirm your account details.",
    "Your subscription will be charged unless you cancel within 24 hours.",
    "We need additional verification for your recent transaction.",
    "Your account is under review, please provide additional documentation.",
    "We noticed changes to your account settings, please confirm if this was you.",
    "Your account access has been temporarily restricted for security reasons.",
    "We need to update your account information to maintain service."
]

# Filler variations for realism
companies = ["Chase", "Bank of America", "Wells Fargo", "Citibank", "Capital One", "American Express", "Discover", "Mastercard", "Visa"]
services = ["banking", "credit card", "loan", "mortgage", "investment", "insurance", "utility", "internet", "phone", "subscription"]
polite_closings = ["Thank you for your business.", "We appreciate your patience.", "Please contact us if you have questions.", "Have a great day!", "We're here to help.", "Thank you for choosing us."]
scam_entities = ["security team", "fraud department", "verification center", "account services", "billing department", "customer support", "compliance team"]

# Generate 150 new sensitive legitimate examples
print("Generating 150 sensitive legitimate examples...")
sensitive_legit_rows = []

for _ in range(150):
    # Pick a random template
    template = random.choice(sensitive_legit_templates)
    
    # Add random variations
    if random.random() < 0.3:  # 30% chance to add company name
        company = random.choice(companies)
        template = template.replace("your bank", f"{company}")
        template = template.replace("Microsoft", company)
    
    if random.random() < 0.2:  # 20% chance to add polite closing
        closing = random.choice(polite_closings)
        template = f"{template} {closing}"
    
    sensitive_legit_rows.append([template, 0])

# Generate 75 new subtle scam examples
print("Generating 75 subtle scam examples...")
subtle_scams_rows = []

for _ in range(75):
    # Pick a random template
    template = random.choice(subtle_scams_templates)
    
    # Add random variations
    if random.random() < 0.4:  # 40% chance to add entity name
        entity = random.choice(scam_entities)
        template = template.replace("We", f"This is the {entity}. We")
        template = template.replace("We noticed", f"The {entity} noticed")
    
    if random.random() < 0.3:  # 30% chance to add service name
        service = random.choice(services)
        template = template.replace("your account", f"your {service} account")
    
    if random.random() < 0.2:  # 20% chance to add polite closing
        closing = random.choice(polite_closings)
        template = f"{template} {closing}"
    
    subtle_scams_rows.append([template, 1])

# Convert to DataFrames
sensitive_legit_df = pd.DataFrame(sensitive_legit_rows, columns=["text", "label"])
subtle_scams_df = pd.DataFrame(subtle_scams_rows, columns=["text", "label"])

# Combine with original dataset
print("Combining with original dataset...")
df_combined = pd.concat([df, sensitive_legit_df, subtle_scams_df], ignore_index=True)

# Shuffle the dataset
print("Shuffling dataset...")
df_balanced = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)

# Save the balanced dataset
output_path = "data/scam_dataset_balanced.csv"
df_balanced.to_csv(output_path, index=False)

# Print statistics
total_samples = len(df_balanced)
scam_samples = len(df_balanced[df_balanced["label"] == 1])
safe_samples = len(df_balanced[df_balanced["label"] == 0])

print(f"\n✅ Dataset balanced and saved to {output_path}")
print(f"Total samples: {total_samples}")
print(f"Scam samples (label=1): {scam_samples}")
print(f"Safe samples (label=0): {safe_samples}")
print(f"Balance ratio: {scam_samples/total_samples:.1%} scams, {safe_samples/total_samples:.1%} safe")
