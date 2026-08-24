"""
Paystack payment integration.

Two core functions: initialize_transaction() starts a payment and
returns the URL to redirect the guest to; verify_transaction() confirms
what actually happened after they return.

Deliberately built with a direct requests call rather than a
third-party Python wrapper (several exist -- pypaystack2, paystackease
-- but their maintenance status is uncertain, and Paystack's own API is
a simple, well-documented REST interface that doesn't need one).
"""
import requests
from flask import current_app

PAYSTACK_BASE_URL = "https://api.paystack.co"


def _headers():
    return {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }


def initialize_transaction(email, amount, currency, reference, callback_url, metadata=None):
    """
    Starts a Paystack transaction and returns the URL to redirect the
    guest to.

    amount: the real amount in the guest's currency (e.g. Decimal('20000.00')
    for 20,000 XOF) -- NOT yet converted to the API's smallest-unit
    format. This function does that conversion internally.

    IMPORTANT, confirmed directly in Paystack's own docs: every
    currency requires multiplying by 100, XOF included, even though
    XOF has no real subunit in practice -- it's a fixed API convention,
    not currency-dependent. For XOF specifically, the pre-multiplication
    amount must also be a whole number (no fractional part) -- this
    isn't separately enforced here, since the app's existing TWO_DP
    rounding is applied uniformly across all currencies already: a
    genuinely fractional XOF amount reaching this function would be a
    symptom of that broader, pre-existing convention, not something to
    silently special-case in just this one function.

    metadata: an optional dict carried through to Paystack's response
    on verify -- used here to preserve booking/voucher/discount context
    across the redirect-to-Paystack-and-back round trip, since Flask
    session state isn't guaranteed to survive it reliably.

    Returns the full Paystack response dict on success. Raises
    requests.HTTPError if the call itself fails (network issue, bad
    key, Paystack downtime) -- the caller must handle that and show
    the guest a real error rather than silently proceeding as if
    payment had started.
    """
    payload = {
        "email": email,
        "amount": int(amount * 100),
        "currency": currency,
        "reference": reference,
        "callback_url": callback_url,
    }
    if metadata:
        payload["metadata"] = metadata

    response = requests.post(
        f"{PAYSTACK_BASE_URL}/transaction/initialize",
        json=payload,
        headers=_headers(),
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def verify_transaction(reference):
    """
    Confirms what actually happened for a given transaction reference,
    directly from Paystack -- never trust a browser redirect alone as
    proof of payment.

    Returns the full Paystack response dict. The caller must check
    response['data']['status'] == 'success' before treating the
    payment as genuine, and should compare response['data']['amount']
    against the amount originally expected -- a mismatch is a sign of
    tampering or a bug, not something to wave through. This function
    only fetches the data; it doesn't judge it.
    """
    response = requests.get(
        f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers=_headers(),
        timeout=15,
    )
    response.raise_for_status()
    return response.json()