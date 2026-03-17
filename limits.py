from datetime import datetime

# ============================================================
# PLAN LIMITS - ALL RESTRICTIONS REMOVED
# ============================================================

LIMITS = {
    'free': {
        'tts': 999999,
        'pdf_to_text': 999999,
        'text_to_pdf': 999999,
        'pdf_to_word': 999999,
        'word_to_pdf': 999999,
        'qr': 999999,
        'translator': 999999,
        'image': 999999,
        'image_to_text': 999999,
    },
    'basic': {
        'tts': 999999,
        'pdf_to_text': 999999,
        'text_to_pdf': 999999,
        'pdf_to_word': 999999,
        'word_to_pdf': 999999,
        'qr': 999999,
        'translator': 999999,
        'image': 999999,
        'image_to_text': 999999,
    },
    'pro': {
        'tts': 999999,
        'pdf_to_text': 999999,
        'text_to_pdf': 999999,
        'pdf_to_word': 999999,
        'word_to_pdf': 999999,
        'qr': 999999,
        'translator': 999999,
        'image': 999999,
        'image_to_text': 999999,
    }
}

PLAN_PRICES = {
    'free': 0,
    'basic': 0,
    'pro': 0,
}

PLAN_NAMES = {
    'free': 'Free',
    'basic': 'Basic',
    'pro': 'Pro',
}

def get_limit(plan, tool):
    return 999999

def check_limit(user_usage, plan, tool, amount=1):
    limit = 999999
    current = user_usage.get(tool, 0)
    return True, limit, current
