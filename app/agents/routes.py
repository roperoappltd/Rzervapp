# agent_routes.py
#
# Wires the booking chat widget to Claude via tool use (function calling).
# Two tools are exposed: a read-only search tool the model can call freely,
# and a two-step booking flow (request_booking -> confirm_booking) where the
# actual database write only ever happens inside confirm_booking, and only
# once a draft was already staged by request_booking. This means even if the
# model *thinks* it should book something, nothing is written to the DB
# until confirm_booking runs -- which only fires when the user has replied
# to a shown summary. That is the real confirmation gate; the prompt
# instructions are a second layer, not the only one.

#import os
import json
from datetime import datetime

import anthropic
from flask import Blueprint, request, jsonify, session, current_app, url_for
from flask_login import current_user

from app.helpers.booking import create_booking         # the shared function from booking.py
from app.models.roommodel import Rooms                 # adjust import path to your app structure
#from ..rooms.routes import roomsearch                  # <- point this at your existing search logic

agent = Blueprint('agent', __name__)


def get_anthropic_client():
    return anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
 
SYSTEM_PROMPT = """You are Asseta, the booking assistant for Jambo, a room
booking platform. You help guests find and book rooms through conversation.
 
Core rules:
1. Never state room availability, prices, or details from memory. Always
   call search_rooms and report only what it returns.
1b. Never silently reuse a city, guest count, price range, or dates from
    an earlier search_rooms call in a new search unless the user is
    clearly continuing/refining that same request (e.g. "what about
    cheaper ones"). If the user names a new city without repeating other
    details, treat unspecified fields as not given rather than carrying
    over the old values -- ask if something important is missing instead
    of guessing it stayed the same.
2. After showing search results as text, always ask the user whether
   they'd like to book one of the rooms or see a photo of one -- don't
   just leave the list hanging. Something like: "Want me to show you a
   photo of any of these, or are you ready to book one?"
3. Only call show_room_photo when the user has explicitly asked to see a
   picture/photo of a specific room, or clearly said yes after you offered.
   Never call it automatically right after search_rooms.
3b. Never say a photo has been shown, a booking has been made, or any
    other tool action has happened unless you actually called that tool
    in this same turn and it returned success. If you haven't called the
    tool yet, call it now instead of describing the result in advance.
4. Never invent a room_id. Only offer to book or show a photo of a room
   the user has actually seen in a search_rooms result in this conversation.
5. Booking is a two-step process and you must never skip a step:
   a. Call request_booking once you have the room and the guest's contact
      details (full name, email, phone). This only stages a draft -- it
      does not create a real booking.
   b. Show the user the returned summary and ask them to confirm.
   c. Only call confirm_booking after the user clearly says yes/confirm/
      book it in their own words. If they say no, change something, or
      seem unsure, do not call confirm_booking -- update the draft with
      request_booking again or ask what they'd like to change instead.
5b. confirm_booking creates a booking that is pending payment, not a
    finished transaction -- do not say "you're all booked" or "enjoy your
    stay." Instead, tell them their booking was created and they need to
    complete payment to secure it, and give them the checkout link
    returned by the tool.
6. Never call request_booking and confirm_booking in the same turn.
7. The number of guests a room sleeps is fixed to that room's max
   occupancy -- there is no way to book a custom guest count. If a user
   asks for a specific guest count, tell them which rooms accommodate that
   many rather than promising a custom number.
8. If a booking action is attempted and the user is not logged in, tell
   them they need to log in first, in a friendly way -- don't just repeat
   an error. If they're logged in but their email isn't verified yet,
   tell them to check their inbox for the verification link before they
   can book -- also friendly, not a raw error dump.
9. Reply in whatever language the user is writing in (this platform
   supports English and French).
10. Keep replies short and conversational -- this is a chat widget, not an
    email.
11. Never use markdown formatting -- no **bold**, no bullet points, no
    headers, no backticks. The chat bubble renders plain text only, so
    markdown symbols would show up literally instead of being styled.
    Write plain, natural sentences instead (emoji are fine).
12. If a user asks about visa or entry requirements to travel somewhere,
    use web_search to find current information -- don't answer from
    memory, since visa rules change often and depend on both the
    traveler's nationality and the destination. If they haven't told you
    their nationality, ask before searching. Always end a visa answer by
    telling them to confirm with the destination country's embassy or
    consulate before traveling, since this is general information, not
    official guidance. Only use web_search for visa/entry-requirement
    questions -- not for other topics.
"""
 
# ---------------------------------------------------------------------------
# Tool schemas (Anthropic tool-use format)
# ---------------------------------------------------------------------------
 
TOOLS = [
    {
        "name": "search_rooms",
        "description": (
            "Search available rooms by city, dates, guests, room type, and "
            "price. Read-only and safe to call directly any time the user "
            "is looking for or comparing rooms -- no confirmation needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City or location."},
                "borough": {"type": "string", "description": "Optional neighborhood/borough within the city."},
                "arrival": {"type": "string", "description": "Check-in date, YYYY-MM-DD."},
                "departure": {"type": "string", "description": "Check-out date, YYYY-MM-DD."},
                "guests": {"type": "integer", "description": "Number of guests."},
                "room_type": {"type": "string", "description": "Optional room category filter."},
                "max_price": {"type": "number", "description": "Optional max price per night."},
            },
            "required": ["city", "arrival", "departure"],
        },
    },
    {
        "name": "request_booking",
        "description": (
            "Stage a booking draft for a room the user picked from search "
            "results. Does NOT create a real booking -- only prepares a "
            "summary for the user to confirm. Call this again to update the "
            "draft if the user changes their mind before confirming."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "room_id": {"type": "integer", "description": "Room id from a prior search_rooms result."},
                "arrival": {"type": "string"},
                "departure": {"type": "string"},
                "primary_guest": {"type": "string", "description": "Full name of the primary guest."},
                "pguest_email": {"type": "string"},
                "pguest_phone": {"type": "string"},
                "ad_info": {"type": "string", "description": "Optional extra requests/notes."},
            },
            "required": ["room_id", "arrival", "departure", "primary_guest", "pguest_email", "pguest_phone"],
        },
    },
    {
        "name": "confirm_booking",
        "description": (
            "Finalize the booking that was staged by request_booking. Only "
            "call this after the user has explicitly confirmed the summary "
            "you showed them (e.g. 'yes', 'confirm', 'book it')."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "show_room_photo",
        "description": (
            "Display a photo of one specific room to the user. Only call "
            "this when the user explicitly asks to see a picture/photo of "
            "a room, or after you've offered to show one and they said yes. "
            "Do not call this automatically after search_rooms -- search "
            "results are text-only; always ask first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "room_id": {"type": "integer", "description": "Room id from a prior search_rooms result."},
            },
            "required": ["room_id"],
        },
    },

]

# Anthropic's built-in server-side web search tool. Unlike the tools above,
# this one is executed by Anthropic's infrastructure, not by our code --
# there's no matching entry in TOOL_IMPLS and no client round-trip needed.
# max_uses caps how many searches Claude can run in a single turn, mainly
# to bound latency/cost on a single visa question.
WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 3,
}
 
# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
 
from ..helpers.searches import build_room_query, serialize_room  # the refactored functions from search.py
 
 
def _search_rooms_impl(params):
    guests = params.get("guests")

    result = build_room_query(
        location=params.get("city"),
        borough=params.get("borough"),
        room_category=params.get("room_type"),
        min_price=None,
        max_price=params.get("max_price"),
        arrival=params.get("arrival"),
        departure=params.get("departure"),
        guests=guests,
    )
 
    if result["error"] == "invalid_dates":
        return {"error": "Those dates couldn't be understood. Please use YYYY-MM-DD."}
    if result["error"] == "departure_before_arrival":
        return {"error": "Departure date must be after the arrival date."}
 
    # "no_availability" isn't a hard error -- it's a valid, empty result.
    rooms = result["query"].limit(10).all()
    serialized = [serialize_room(r) for r in rooms]
 
    # Remember which room_ids were actually shown, so request_booking can
    # reject any room_id the model didn't get from a real search result.
    session['last_search_room_ids'] = [r["id"] for r in serialized]
 
    response = {"results": serialized, "count": len(serialized)}

    # If nothing came back and a guest count was given, check whether the
    # guest filter itself is what zeroed things out -- otherwise the model
    # tends to blame general availability instead of room size, which is
    # misleading. Re-run the same search without the guest filter to find out.
    if not serialized and guests is not None:
        no_guest_filter = build_room_query(
            location=params.get("city"),
            borough=params.get("borough"),
            room_category=params.get("room_type"),
            max_price=params.get("max_price"),
            arrival=params.get("arrival"),
            departure=params.get("departure"),
            guests=None,
        )
        if no_guest_filter["error"] is None:
            fallback_rooms = no_guest_filter["query"].all()
            if fallback_rooms:
                max_cap = max(r.max_occupancy for r in fallback_rooms)
                response["note"] = (
                    f"No room here sleeps {guests} guests -- the largest "
                    f"available room for these dates/location sleeps "
                    f"{max_cap}. Tell the user specifically that room size "
                    f"is the issue, not general availability, and mention "
                    f"the {max_cap}-guest option if it might work for them."
                )

    return response

def _show_room_photo_impl(params):
    room_id = params.get("room_id")
    shown_ids = session.get('last_search_room_ids', [])
    if room_id not in shown_ids:
        return {"error": "That room wasn't part of the last search results. Please search again."}
 
    room = Rooms.query.get(room_id)
    if room is None:
        return {"error": "Room not found."}
 
    serialized = serialize_room(room)
    if not serialized.get("image_url"):
        return {"error": "No photo is available for that room."}
 
    return {"room": serialized}
 
 
def _request_booking_impl(params):
    if not current_user.is_authenticated:
        return {"error": "The user is not logged in. Ask them to log in before booking."}
    if not current_user.email_verified:
        return {"error": "The user's email is not verified yet. Ask them to check their inbox and verify their email before booking."}

    room_id = params.get("room_id")
    shown_ids = session.get('last_search_room_ids', [])
    if room_id not in shown_ids:
        return {"error": "That room wasn't part of the last search results. Please search again."}
 
    room = Rooms.query.get(room_id)
    if room is None:
        return {"error": "Room not found."}
 
    try:
        arrival = datetime.strptime(params["arrival"], "%Y-%m-%d").date()
        departure = datetime.strptime(params["departure"], "%Y-%m-%d").date()
    except (ValueError, KeyError):
        return {"error": "Invalid arrival/departure date format, expected YYYY-MM-DD."}
 
    draft = {
        "room_id": room_id,
        "room_name": getattr(room, "room_name", None) or f"Room {room.id}",
        "arrival": params["arrival"],
        "departure": params["departure"],
        "primary_guest": params.get("primary_guest", ""),
        "pguest_email": params.get("pguest_email", ""),
        "pguest_phone": params.get("pguest_phone", ""),
        "ad_info": params.get("ad_info", ""),
        "max_occupancy": room.max_occupancy,
    }
    # Staged only -- nothing is written to the database yet.
    session['pending_booking'] = draft
    return {"status": "draft_ready", "draft": draft}
 
 
def _confirm_booking_impl():
    if not current_user.is_authenticated:
        return {"error": "The user is not logged in. Ask them to log in before booking."}
    if not current_user.email_verified:
        return {"error": "The user's email is not verified yet. Ask them to check their inbox and verify their email before booking."}
 
    draft = session.get('pending_booking')
    if not draft:
        return {"error": "No booking draft is currently staged. Use request_booking first."}
 
    room = Rooms.query.get(draft["room_id"])
    if room is None:
        return {"error": "Room no longer exists."}
 
    arrival = datetime.strptime(draft["arrival"], "%Y-%m-%d").date()
    departure = datetime.strptime(draft["departure"], "%Y-%m-%d").date()
 
    bookinfo, error = create_booking(
        room=room,
        arrival=arrival,
        departure=departure,
        primary_guest=draft["primary_guest"],
        pguest_email=draft["pguest_email"],
        pguest_phone=draft["pguest_phone"],
        ad_info=draft.get("ad_info", ""),
        user_id=current_user.id,
    )
 
    if error:
        return {"error": error}
 
    # One-time use: clear the draft so a repeat confirm_booking call can't
    # double-book.
    session.pop('pending_booking', None)
 
    return {
        "status": "booked",
        "booking_num": bookinfo.booking_num,
        "room_id": room.id,
        "checkout_url": url_for('rooms.checkout', room_id=room.id),
    }
 
 
TOOL_IMPLS = {"search_rooms": _search_rooms_impl,
              "request_booking": _request_booking_impl,
              "confirm_booking": lambda params: _confirm_booking_impl(),
              "show_room_photo": _show_room_photo_impl,
            }
 
# ---------------------------------------------------------------------------
# Chat route
# ---------------------------------------------------------------------------
 
@agent.route("/api/agent/chat", methods=['POST'])
def agent_chat():
    '''
    Body: { "message": "..." }
    Conversation history is kept server-side in the session so the model
    always has the full context (previous search results, staged draft,
    etc.) without the client needing to resend it.
    '''
    client = get_anthropic_client()
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify(error="Empty message."), 400
 
    history = session.get('agent_messages', [])
    history.append({"role": "user", "content": user_message})

    rooms_shown = None       # populated if show_room_photo is called this turn
    checkout_url_shown = None  # populated if confirm_booking succeeds this turn
 
    # Agentic loop: keep calling Claude and executing any tool calls it
    # requests, until it returns a plain text answer with no more tool use.
    for _ in range(6):  # hard cap so a runaway loop can't hang the request
        response = client.messages.create(model=MODEL, max_tokens=1024,
                                          system=SYSTEM_PROMPT, tools=TOOLS + [WEB_SEARCH_TOOL],
                                          messages=history,
                                        )
    
        # response.content is a list of SDK objects (TextBlock, ToolUseBlock)
        # which are NOT JSON-serializable -- convert to plain dicts before
        # this goes anywhere near session storage or the next API call.
        content_blocks = [block.model_dump() for block in response.content]
        history.append({"role": "assistant", "content": content_blocks})
 
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            final_text = "".join(b.text for b in response.content if b.type == "text")
            session['agent_messages'] = history
            return jsonify(reply=final_text, rooms=rooms_shown, checkout_url=checkout_url_shown)
 
        tool_results = []
        for block in tool_uses:
            impl = TOOL_IMPLS.get(block.name)
            result = impl(block.input) if impl else {"error": f"Unknown tool {block.name}"}
            
            if block.name == "show_room_photo" and "room" in result:
                rooms_shown = [result["room"]]  # single room card, shown on request only

            if block.name == "confirm_booking" and result.get("status") == "booked":
                checkout_url_shown = result.get("checkout_url")
            
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })
 
        history.append({"role": "user", "content": tool_results})
 
    session['agent_messages'] = history
    return jsonify(reply="Sorry, something went wrong processing that. Could you try again?", 
                        rooms=None, checkout_url=None)
 
@agent.route("/api/agent/reset", methods=['POST'])
def agent_reset():
    '''Clears conversation + any staged draft. Call when the chat widget closes/reopens fresh.'''
    session.pop('agent_messages', None)
    session.pop('pending_booking', None)
    session.pop('last_search_room_ids', None)
    return jsonify(status="cleared")