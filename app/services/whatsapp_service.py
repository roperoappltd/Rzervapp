"""
WhatsApp notifications for hosts, on new bookings.

Structurally different from sms_service.py in one important way:
WhatsApp doesn't allow free-text for a business-initiated conversation
(one the host didn't message first) -- only a pre-approved Meta
template, submitted and approved once, then reused by filling in its
named parameters. send_whatsapp() reflects that constraint directly.

BSP (Business Solution Provider) not yet finalized -- Africa's Talking
offers WhatsApp alongside SMS, Twilio and others also viable. Left
generic on purpose, same approach as sms_service.py.
"""
import requests
from flask import current_app


def send_whatsapp(phone_number, template_params):
    """
    Sends a WhatsApp notification via the pre-approved template named
    in config (WHATSAPP_TEMPLATE_NAME). Returns True on confirmed
    success, False otherwise -- like send_sms(), never raises for
    expected failure modes, since a failed notification must never
    break the booking confirmation flow that triggered it.

    phone_number: WhatsApp Business API requires E.164 format (e.g.
    +2250700000000) -- no normalization is done here yet, so this
    should be validated/converted before this is called.

    template_params: an ordered list of values filling the template's
    named placeholders -- the exact parameter order must match what
    was actually submitted and approved in the Meta template.
    """
    if not phone_number or phone_number == 'Change me':
        current_app.logger.warning(f"send_whatsapp called with no real phone number: {phone_number!r}")
        return False

    api_key = current_app.config.get('WHATSAPP_API_KEY')
    api_url = current_app.config.get('WHATSAPP_API_URL')
    template_name = current_app.config.get('WHATSAPP_TEMPLATE_NAME')

    if not api_key or not api_url:
        current_app.logger.error("WHATSAPP_API_KEY or WHATSAPP_API_URL not configured -- cannot send WhatsApp message")
        return False

    try:
        # PLACEHOLDER: exact request shape depends on the BSP chosen --
        # these are NOT interchangeable the way SMS APIs often are,
        # since the template must be pre-registered with that specific
        # provider/Meta account.
        response = requests.post(
            api_url,
            json={
                "to": phone_number,
                "template": {
                    "name": template_name,
                    "language": "en",
                    "parameters": template_params,
                },
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"WhatsApp send failed to {phone_number}: {e}")
        return False