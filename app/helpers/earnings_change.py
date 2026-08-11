from datetime import datetime
from dateutil.relativedelta import relativedelta
from app import db
from app.models.bookmodel import HostEarning



def calculate_monthly_earnings_change(user_id):
    """
    Calculate current month earnings percentage change compared with previous month.
    Returns:
        Positive value  = increase %
        Negative value  = decrease %
        Zero            = no change
    """
    today = datetime.today()
    # Current month start
    current_month_start = datetime(today.year, today.month, 1)
    # Next month start
    next_month_start = current_month_start + relativedelta(months=1)
    # Previous month start
    previous_month_start = current_month_start - relativedelta(months=1)
    # Current month earnings
    current_earnings = db.session.query(db.func.sum(HostEarning.net_earning)).filter(
                                HostEarning.user_id == user_id,
                                HostEarning.created_at >= current_month_start,
                                HostEarning.created_at < next_month_start
                            ).scalar() or 0
    # Previous month earnings
    previous_earnings = db.session.query(db.func.sum(HostEarning.net_earning)).filter(
                                    HostEarning.user_id == user_id,
                                    HostEarning.created_at >= previous_month_start,
                                    HostEarning.created_at < current_month_start
                                ).scalar() or 0
    # Avoid division by zero
    if previous_earnings == 0:
        if current_earnings > 0:
            return 100
        return 0

    # Percentage change
    percentage_change = ((current_earnings - previous_earnings) /
                                                        previous_earnings) * 100
    return round(percentage_change, 2)
