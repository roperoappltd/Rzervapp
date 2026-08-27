"""
SMS notifications for hosts, on new bookings.

Provider-agnostic on purpose -- Africa's Talking vs Twilio vs a local
aggregator is still an open decision. send_sms() is the one function
everything else calls; swapping providers later means rewriting the
inside of this function only, nothing that calls it.
"""
import requests
from flask import current_app


def send_sms(phone_number, message):
    """
    Sends an SMS. Returns True on confirmed success, False otherwise --
    deliberately never raises for expected failure modes (bad number,
    provider downtime, network issue), since a failed SMS must never
    break the booking confirmation flow that triggered it.
    """
    if not phone_number or phone_number == 'Change me':
        current_app.logger.warning(f"send_sms called with no real phone number: {phone_number!r}")
        return False

    api_key = current_app.config.get('SMS_API_KEY')
    api_url = current_app.config.get('SMS_API_URL')

    if not api_key or not api_url:
        current_app.logger.error("SMS_API_KEY or SMS_API_URL not configured -- cannot send SMS")
        return False

    try:
        # PLACEHOLDER: exact request shape depends on the provider
        # chosen -- adjust to match whichever provider's documented
        # request format once one is confirmed.
        response = requests.post(
            api_url,
            json={
                "to": phone_number,
                "message": message,
                "from": current_app.config.get('SMS_SENDER_ID', 'Jambo'),
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"SMS send failed to {phone_number}: {e}")
        return False


def build_booking_notification(host_name, guest_name, room_name, arrival_date):
    """
    Builds the notification text. Kept short and plain -- standard SMS
    length limits (160 chars for a single, non-Unicode message) charge
    extra per message beyond that.
    """
    return (
        f"Jambo: New booking! {guest_name} booked {room_name} "
        f"for {arrival_date}. Check your dashboard for details."
    )