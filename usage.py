from models import db, Usage
from limits import LIMITS, get_limit
from datetime import datetime
from flask_login import current_user

def get_today_usage(user_id, tool):
    today = datetime.utcnow().date()
    records = Usage.query.filter_by(
        user_id=user_id,
        tool=tool,
        date=today
    ).all()
    return sum(r.amount for r in records)

def add_usage(user_id, tool, amount=1):
    today = datetime.utcnow().date()
    usage = Usage(user_id=user_id, tool=tool, amount=amount, date=today)
    db.session.add(usage)
    db.session.commit()

def can_use(user, tool, amount=1):
    """ALWAYS ALLOW - No restrictions"""
    limit = 999999
    current = 0
    return True, limit, current

def get_all_usage(user_id, plan):
    today = datetime.utcnow().date()
    usage = {}
    for tool in LIMITS[plan].keys():
        usage[tool] = get_today_usage(user_id, tool)
    return usage
