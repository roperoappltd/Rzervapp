from app import db
from app.models.bookmodel import Bookings, HostEarning, Withdrawal


# Helper function to compute host available balance
def get_host_balance(user_id):
    # AMENDED: was summing host_earning_host / amount_host (host's local
    # currency). Same cross-currency risk as the dashboard routes -- a
    # host with rooms/withdrawals in more than one currency would have
    # had those figures silently added together as if they were the same
    # unit. Using the GBP-normalized fields instead, since GBP is the
    # one currency guaranteed consistent across every HostEarning/
    # Withdrawal row for this user, regardless of which currency each
    # individual room or withdrawal request was actually in.
    total_earned = db.session.query(db.func.sum(HostEarning.host_earning_gbp)
                                    ).filter(HostEarning.user_id == user_id,
                                            HostEarning.status == "Approved"
                                             ).scalar() or 0
 
    total_withdrawn = db.session.query(db.func.sum(Withdrawal.amount_gbp)
                                       ).filter(Withdrawal.user_id == user_id,
                                        Withdrawal.status.in_(
                                        ["Pending", "Approved"])).scalar() or 0
 
    return total_earned - total_withdrawn
 
