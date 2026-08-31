"""
Deletes a single test booking and everything that depends on it, in
the correct child-before-parent order, reversing loyalty points
precisely rather than zeroing them. Deliberately single-booking only
-- no bulk "delete all test data" mode, since the system can't
reliably distinguish a test booking from a real one on its own; that
judgment call stays explicitly with whoever runs this.

Requires typed confirmation before anything is deleted. Everything
happens within one transaction: if any step raises before the final
commit, nothing is persisted at all.
"""
from app import db
from app.models.bookmodel import Bookings, Payments, HostEarning, Refund
from app.models.usermodel import User
from app.models.chatmodel import Conversation, Message


def delete_test_booking(booking_id, confirm_fn):
    """
    confirm_fn: a callable that prints a prompt and returns True/False
    for confirmation -- injected rather than calling click.confirm()
    directly, so this function stays testable without needing a real
    terminal attached.
    """
    booking = Bookings.query.get(booking_id)
    if not booking:
        return False, f"No booking found with id {booking_id}."

    payment = Payments.query.filter_by(booking_id=booking.id).first()
    guest = User.query.get(booking.user_id)
    room_name = booking.rooms.room_name if booking.rooms else "(room not found)"

    print("")
    print("=" * 50)
    print(f"Booking:      {booking.booking_num}")
    print(f"Guest:        {booking.primary_guest} ({booking.pguest_email})")
    print(f"Room:         {room_name}")
    print(f"Dates:        {booking.arrival} to {booking.departure}")
    print(f"Status:       {booking.status}")
    if payment:
        print(f"Paid:         {payment.total_paid_guest} {payment.payment_currency}")
        print(f"Points earned: {payment.points_earned}")
    else:
        print("Payment:      (no payment record found)")
    print("=" * 50)
    print("")

    if not confirm_fn(f"Type 'yes' to permanently delete booking {booking.booking_num}"):
        return False, "Cancelled -- nothing was deleted."

    # Conversation/Message, if a chat thread exists for this booking
    conversation = Conversation.query.filter_by(booking_id=booking.id).first()
    if conversation:
        Message.query.filter_by(conversation_id=conversation.id).delete()
        db.session.delete(conversation)

    # HostEarning and Refund, both keyed directly to the booking
    HostEarning.query.filter_by(booking_id=booking.id).delete()
    Refund.query.filter_by(booking_id=booking.id).delete()

    # Reverse loyalty points precisely -- subtract the exact amount
    # earned from this booking, never just zero the field, in case
    # the guest has genuine points from elsewhere. Floored at 0 in
    # case some of these points were already spent since being
    # earned.
    if payment and payment.points_earned and guest:
        guest.rzerv_points = max(0, guest.rzerv_points - payment.points_earned)

    if payment:
        db.session.delete(payment)

    db.session.delete(booking)
    db.session.commit()

    return True, f"Booking {booking.booking_num} and all related records deleted."