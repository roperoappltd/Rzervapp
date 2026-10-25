from sqlalchemy.exc import IntegrityError
from flask import session
from app import db
from app.helpers.is_avail import is_available
from app.models.roommodel import Deals
from app.models.bookmodel import Bookings
from app.models.chatmodel import Conversation
from ..rooms.roomutils import number_generator
from flask_babel import _
from decimal import Decimal
from app.services.currency import get_exchange_rates  
from app.services.preference_service import VisitorPreferences
from datetime import date

# TODO: update to Decimal('0.03') - Decimal('0.05') once the service charge
# actually launches. Zero for now per current business rules.
SERVICE_CHARGE_RATE = Decimal('0.00')

# How long a Pending (unpaid) booking stays resumable before being
# considered abandoned. Shared between booknow() (checks this window to
# resume an existing Pending booking instead of creating a duplicate)
# and the run-booking-maintenance CLI command (marks anything older than
# this as Expired) -- defined once here so both always agree on the
# same cutoff.
PENDING_BOOKING_EXPIRY_MINUTES = 30


def deal_applies_to_room(deal, room_id):
    '''True if this deal may be used for a booking of `room_id` today:
    it is active, inside its date window (if any), and is either a
    platform-wide campaign (room_id NULL) or the room's own deal.'''
    if deal is None or not deal.active:
        return False
    if deal.room_id is not None and deal.room_id != room_id:
        return False
    today = date.today()
    if deal.start_date and today < deal.start_date:
        return False
    if deal.end_date and today > deal.end_date:
        return False
    return True


def get_room_active_deal(room_id):
    '''Returns this room's own host-set Deal if one exists, is active,
    and (if scheduled) is currently within its date window. Returns None
    otherwise. Used both to auto-attach a discount at booking time and
    to pre-populate the room edit form with the host's current setting.'''
    deal = Deals.query.filter_by(room_id=room_id, active=True).first()
    if not deal:
        return None
    today = date.today()
    if deal.start_date and today < deal.start_date:
        return None
    if deal.end_date and today > deal.end_date:
        return None
    return deal
 
 
def create_booking(room, arrival, departure, primary_guest, pguest_email,
                    pguest_phone, ad_info, user_id, deal_id=None):
    '''
    Shared booking-creation logic used by both the HTML form route
    (booknow) and the JSON agent route (agent_booknow).
 
    Returns a tuple: (bookinfo_or_None, error_message_or_None)
    error_message is a plain string safe to show to a user/agent when
    booking cannot proceed (e.g. dates unavailable, missing exchange
    rate). Raises nothing on expected failure paths so callers don't
    need try/except for them.
    '''
    # Basic date sanity, independent of the web form (the agent route
    # and any future caller go through here too).
    if arrival and departure:
        if departure <= arrival or arrival < date.today():
            return None, _("Please choose valid dates: check-in cannot be in the past and check-out must be after check-in.")

    if arrival and departure:
        if not is_available(room.id, arrival, departure):
            return None, _("Sorry, this room is not available for selected dates.")
 
    deal = None
    if deal_id:
        deal = Deals.query.get_or_404(deal_id)
        # SECURITY/MONEY: deal_id comes from a URL parameter, so it must
        # be proven to apply to THIS room and to be live today. Otherwise
        # a guest can attach any deal (another host's, an expired or
        # switched-off one) to any room by editing ?deal_id=. An invalid
        # id is ignored and the room's own current deal, if any, applies.
        if not deal_applies_to_room(deal, room.id):
            deal = get_room_active_deal(room.id)
    else:
        # AMENDED: no deal was explicitly passed (i.e. this booking isn't
        # coming through a platform campaign link like the homepage deal
        # cards) -- check whether the room itself has a host-set discount
        # and apply it automatically, since a host's own discount should
        # always apply, not require the guest to click a special link.
        deal = get_room_active_deal(room.id)
 
    # --------------------------------------------------------------
    # Service charge: set by the app, paid by the guest, in the
    # guest's own currency -- requires chaining room.room_currency ->
    # GBP -> guest_currency, since ExchangeRate only stores rates
    # relative to GBP as base.
    # --------------------------------------------------------------
    guest_currency = VisitorPreferences().currency
 
    rates = get_exchange_rates()  # {currency_code: rate_per_1_gbp, ..., 'GBP': 1}
 
    raw_host_rate = rates.get(room.room_currency)
    if raw_host_rate is None:
        return None, _("Booking currently unavailable: missing exchange rate for %(currency)s.", currency=room.room_currency)
 
    raw_guest_rate = rates.get(guest_currency)
    if raw_guest_rate is None:
        return None, _("Booking currently unavailable: missing exchange rate for %(currency)s.", currency=guest_currency)
 
    # get_exchange_rates() may return plain float/int -- Decimal cannot be
    # mixed with either in arithmetic, so wrap defensively regardless of
    # whether ExchangeRate.rate has been migrated to Numeric yet.
    rate_host_per_gbp = Decimal(str(raw_host_rate))
    rate_guest_per_gbp = Decimal(str(raw_guest_rate))
 
    room_price_gbp = room.price / rate_host_per_gbp
    room_price_guest = room_price_gbp * rate_guest_per_gbp
 
    serv_charge_guest = (room_price_guest * SERVICE_CHARGE_RATE).quantize(Decimal('0.01'))
    serv_charge_gbp = (room_price_gbp * SERVICE_CHARGE_RATE).quantize(Decimal('0.01'))
 
    # --------------------------------------------------------------
    # booking_num is now unique=True -- retry a few times on the
    # (statistically unlikely, but no longer silently ignorable)
    # chance number_generator() collides with an existing booking.
    # --------------------------------------------------------------
    bookinfo = None
    last_error = None
    for _attempt in range(5):
        candidate_num = number_generator()
        try:
            bookinfo = Bookings(
                booking_num=candidate_num,
                arrival=arrival, departure=departure,
                num_guests=room.max_occupancy, room_type=room.room_category,
                ad_info=ad_info, primary_guest=primary_guest,
                pguest_email=pguest_email, pguest_phone=pguest_phone,
                room_id=room.id, user_id=user_id, deal_id=deal.id if deal else None,
                serv_charge=serv_charge_guest,
                serv_charge_gbp=serv_charge_gbp,
                serv_charge_currency=guest_currency,
                serv_charge_exchange_rate=rate_guest_per_gbp,
            )
            db.session.add(bookinfo)
            db.session.flush()  # surfaces the unique-constraint collision here, before Conversation is built
            break
        except IntegrityError:
            db.session.rollback()
            bookinfo = None
            last_error = "booking_num collision"
            continue
 
    if bookinfo is None:
        return None, _("Could not generate a unique booking reference. Please try again.")
 
    # Create a conversation between host and guest
    conversation = Conversation(booking_id=bookinfo.id, guest_id=bookinfo.user_id,
                                host_id=bookinfo.rooms.user_id)
    db.session.add(conversation)
 
    db.session.commit()
    return bookinfo, None