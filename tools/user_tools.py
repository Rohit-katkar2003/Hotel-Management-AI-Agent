import json
from datetime import date
from langchain_core.tools import tool
from database.connection import SessionLocal
from database.models import Customer, Room, Booking, ChatSession
from tools._image_map import image_for


@tool
def search_available_rooms(room_type: str = None, guests: int = None,
                           check_in: str = None, check_out: str = None) -> str:
    """Search rooms. Returns JSON with rooms (incl. image URLs) for UI rendering."""
    s = SessionLocal()
    try:
        q = s.query(Room).filter(Room.status != "maintenance")
        if room_type: q = q.filter(Room.room_type == room_type.lower())
        if guests:    q = q.filter(Room.capacity >= guests)
        rooms = q.order_by(Room.price_per_night).all()

        if check_in and check_out:
            ci, co = date.fromisoformat(check_in), date.fromisoformat(check_out)
            def free(r):
                return not s.query(Booking).filter(
                    Booking.room_id == r.id,
                    Booking.status.in_(["confirmed", "checked_in"]),
                    Booking.check_in < co, Booking.check_out > ci
                ).first()
            rooms = [r for r in rooms if free(r)]
        else:
            rooms = [r for r in rooms if r.status == "available"]

        payload = {
            "rooms": [{
                "id": r.id, "number": r.room_number, "type": r.room_type,
                "price": r.price_per_night, "capacity": r.capacity,
                "image": image_for(r.room_type),
            } for r in rooms]
        }
        if not payload["rooms"]:
            return json.dumps({"rooms": [], "summary": "No rooms match those criteria."})
        return json.dumps(payload)
    finally:
        s.close()


@tool
def book_room(name: str, email: str, phone: str, room_id: int,
              check_in: str, check_out: str, thread_id: str = "") -> str:
    """Book a room for a guest. Creates the customer if new. Links session->customer."""
    s = SessionLocal()
    try:
        ci, co = date.fromisoformat(check_in), date.fromisoformat(check_out)
        if ci >= co:            return "❌ Check-out must be after check-in."
        if ci < date.today():   return "❌ Check-in cannot be in the past."

        room = s.query(Room).filter(Room.id == room_id).first()
        if not room:            return f"❌ Room {room_id} not found."

        conflict = s.query(Booking).filter(
            Booking.room_id == room.id,
            Booking.status.in_(["confirmed", "checked_in"]),
            Booking.check_in < co, Booking.check_out > ci
        ).first()
        if conflict:            return f"❌ Room {room.room_number} is busy those dates."

        cust = s.query(Customer).filter(Customer.email == email.lower()).first()
        if not cust:
            cust = Customer(name=name, email=email.lower(), phone=phone, address="not provided")
            s.add(cust); s.flush()

        nights = (co - ci).days
        total = nights * room.price_per_night
        bk = Booking(customer_id=cust.id, room_id=room.id, check_in=ci,
                     check_out=co, status="confirmed", total_amount=total)
        s.add(bk); room.status = "occupied"

        if thread_id:
            sess = s.query(ChatSession).filter(ChatSession.thread_id == thread_id).first()
            if sess: sess.customer_id = cust.id
            else:    s.add(ChatSession(thread_id=thread_id, customer_id=cust.id))

        s.commit()
        return (f"✅ Booking #{bk.id} confirmed for {cust.name}.\n"
                f"   Room {room.room_number} · {check_in} → {check_out}\n"
                f"   {nights} night(s) · Total ${total:.2f}")
    except Exception as e:
        s.rollback(); return f"❌ Error: {e}"
    finally:
        s.close()


@tool
def get_my_bookings(thread_id: str) -> str:
    """Return the current chat session's bookings."""
    s = SessionLocal()
    try:
        sess = s.query(ChatSession).filter(ChatSession.thread_id == thread_id).first()
        if not sess or not sess.customer_id:
            return "You don't have any bookings yet — ask me to book a room!"
        bks = s.query(Booking).filter(Booking.customer_id == sess.customer_id)\
                              .order_by(Booking.id.desc()).all()
        if not bks: return "No bookings on file yet."
        lines = [f"📋 Your bookings ({len(bks)}):"]
        for b in bks:
            lines.append(f"  #{b.id} · Room {b.room.room_number} · "
                         f"{b.check_in}→{b.check_out} · ${b.total_amount:.2f} · {b.status}")
        return "\n".join(lines)
    finally:
        s.close()


USER_TOOLS = [search_available_rooms, book_room, get_my_bookings]