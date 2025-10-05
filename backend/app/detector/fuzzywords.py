from rapidfuzz import fuzz

# 🔑 Define scam-related keywords
SCAM_KEYWORDS = [
    # 🏦 Banking & Credit
    "credit card",
    "bank account",
    "debit card",
    "routing number",
    "account verification",
    "transaction alert",
    "fraud department",
    "bank security",
    "wire transfer",
    "direct deposit",
    "payment authorization",
    "unauthorized charge",
    "update your account",
    "suspicious transaction",
    "billing issue",
    "refund department",
    "financial department",
    "loan approval",
    "investment opportunity",
    "verify your payment",

    # 🧾 IRS / Government Impersonation
    "social security",
    "irs",
    "internal revenue service",
    "federal agent",
    "tax department",
    "arrest warrant",
    "outstanding balance",
    "criminal investigation",
    "legal enforcement action",
    "police department",
    "law enforcement",
    "court appearance",
    "tax evasion",
    "government officer",
    "national insurance number",

    # 🎁 Lottery / Rewards / Offers
    "lottery",
    "jackpot",
    "free prize",
    "congratulations you have won",
    "you are selected",
    "claim your reward",
    "exclusive offer",
    "cash prize",
    "sweepstakes",
    "lucky winner",
    "redeem your gift",
    "free vacation",
    "travel voucher",
    "win a car",
    "bonus offer",
    "special promotion",

    # 💻 Tech Support Scams
    "microsoft support",
    "apple support",
    "amazon support",
    "your computer has a virus",
    "malware detected",
    "windows security",
    "your device is infected",
    "technical support",
    "security alert",
    "system breach",
    "remote access",
    "install software",
    "grant access",
    "update your system",
    "verify your computer",
    "call this number",
    "download this app",

    # 🧓 Insurance & Extended Warranty
    "warranty",
    "vehicle warranty",
    "car insurance",
    "life insurance",
    "health insurance",
    "medicare",
    "policy renewal",
    "coverage expired",
    "beneficiary update",
    "extended coverage",
    "insurance claim",
    "medical plan",
    "final expense",

    # 🧍 Identity / OTP / Account Access
    "verify your identity",
    "one time password",
    "otp",
    "verification code",
    "identity confirmation",
    "two factor authentication",
    "security code",
    "confirm your login",
    "reset your password",
    "account suspended",
    "account deactivated",
    "update credentials",
    "change password",

    # 🧠 Social Engineering / Psychological Hooks
    "urgent",
    "immediate action required",
    "limited time",
    "final notice",
    "act now",
    "don’t share this",
    "keep this confidential",
    "this call is recorded",
    "you must comply",
    "failure to respond",
    "penalty will be applied",
    "do not hang up",
    "sensitive information",
    "disclose details",
    "confidential offer",
    "urgent message",

    # 🛍️ E-commerce / Delivery Scams
    "amazon",
    "paypal",
    "ebay",
    "package delivery",
    "tracking number",
    "shipment failed",
    "customs fee",
    "delivery attempt",
    "update your shipping",
    "verify your order",
    "order confirmation",
    "unauthorized order",

    # 💰 Crypto / Investment Fraud
    "bitcoin",
    "crypto",
    "ethereum",
    "wallet address",
    "send us money",
    "deposit funds",
    "investment return",
    "guaranteed profit",
    "double your money",
    "trading platform",
    "withdraw your profit",
    "financial freedom",
    "limited time investment",
    "mining opportunity",

    # 💸 Loan / Debt Scams
    "payday loan",
    "personal loan",
    "debt relief",
    "consolidate debt",
    "loan forgiveness",
    "interest reduction",
    "credit score boost",
    "pre-approved loan",
    "no credit check",
    "instant approval",

    # 📞 Common Scam Phrases
    "this is not a scam",
    "do not tell anyone",
    "trust me",
    "i am calling from",
    "official representative",
    "financial department",
    "confidential matter",
    "limited availability",
    "authorization needed",
    "claim department",
    "provide your information",
    "stay on the line",
]




def check_keywords(transcript: str, threshold: int = 80):
    matches = []
    transcript_lower = transcript.lower()
    for keyword in SCAM_KEYWORDS:
        score = fuzz.partial_ratio(keyword, transcript_lower)
        if score >= threshold:
            matches.append((keyword, score))
    return matches


def scam_score(transcript: str) -> float:
    matches = check_keywords(transcript)
    if not matches:
        return 0.0
    total_score = sum(score for _, score in matches)
    normalized = min(total_score / 10, 100)  # soft cap at 100
    return round(normalized, 1)

    
   
