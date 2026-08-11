from app import db
from app.models.bookmodel import Bookings, HostEarning, Withdrawal


# Helper function to compute host available balance
def get_host_balance(user_id):
    total_earned = db.session.query(db.func.sum(HostEarning.host_earning_host)
                                    ).filter(HostEarning.user_id == user_id,
                                            HostEarning.status == "Approved"
                                             ).scalar() or 0

    total_withdrawn = db.session.query(db.func.sum(Withdrawal.amount_host)
                                       ).filter(Withdrawal.user_id == user_id,
                                        Withdrawal.status.in_(
                                        ["Pending", "Approved"])).scalar() or 0

    return total_earned - total_withdrawn

