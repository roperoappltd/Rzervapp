# ==========================================
# CHAT MESSAGE SECURITY CHECK
# ==========================================
import re

FORBIDDEN_WORDS = [
    "payment",
    "pay directly",
    "bank",
    "bank account",
    "iban",
    "swift",
    "paypal",
    "cash",
    "transfer",
    "exchange email",
    "email me",
    "my email",
    "phone number",
    "whatsapp",
    "telegram",
    "wave",
    "orange money",
    "western union",
    "ria"
]


def check_message(text):
    """
    Returns warning information
    if suspicious words are detected
    """
    text_lower = text.lower()

    detected_words = []

    # ==========================
    # Keyword detection
    # ==========================

    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            detected_words.append(word)

    # ==========================
    # Email detection
    # ==========================

    email_pattern = r'\S+@\S+\.\S+'

    if re.search(email_pattern, text):
        detected_words.append("email address")

    # ==========================
    # Phone detection
    # ==========================

    phone_pattern = r'\b\d{10,15}\b'

    if re.search(phone_pattern, text):
        detected_words.append( "phone number")

    return {
        "flagged": len(detected_words) > 0,
        "words": detected_words
    }