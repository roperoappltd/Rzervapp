from app import db
from app.models.bookmodel import Refund, Payments

def cancel_and_refund_if_paid(booking, reason='guest_cancelled'):
    '''
    Cancels a booking. If it has an associated payment (i.e. it was
    actually paid for, not just Pending), creates a full-refund Refund
    record using the same logic as the guest-initiated cancel_booking()
    route. Extracted here so that route and delete_account() below don't
    duplicate the same refund-construction logic and risk drifting apart.

    reason defaults to 'guest_cancelled' (a deliberate, individual
    cancellation) -- delete_account() passes 'account_deleted' instead,
    since those bookings are swept up as a side effect of closing the
    whole account, not cancelled one at a time by choice. Same
    reasoning as Bookings.status_reason on the Expired path: one status
    value, multiple real causes worth distinguishing for audit.

    Does NOT commit -- caller controls the transaction.
    '''
    booking.status = "Cancelled"
    booking.status_reason = reason
    booking.active = False

    payment = Payments.query.filter_by(booking_id=booking.id).first()
    if payment is None:
        return  # was Pending / never paid -- nothing to refund

    payment.status = "Refundable"

    refund = Refund(
        booking_id=booking.id,
        payment_id=payment.id,
        user_id=booking.user_id,
        amount_refund_guest=payment.total_paid_guest,
        amount_refund_gbp=payment.accounting_amount,
        refund_currency=payment.payment_currency,
        exchange_rate=payment.pay_exchange_rate,
        status='Pending',
    )
    db.session.add(refund)