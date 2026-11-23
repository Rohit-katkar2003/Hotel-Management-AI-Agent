"""Exposes hotel operations over the Model Context Protocol.
Run:  python -m mcp_server.server
Test in Claude Desktop / Cursor by pointing to this process.
"""
import json
from datetime import date
from mcp.server.fastmcp import FastMCP
from database.connection import SessionLocal
from database.models import Room, Customer, Booking, Payment

mcp = FastMCP("grand-hotel")


@mcp.tool()
def search_rooms(room_type: str = "", guests: int = 0) -> str:
    """Search available rooms. Empty room_type returns all."""
    s = SessionLocal()
    try:
        q = s.query(Room).filter(Room.status == "available")
        if room_type: q = q.filter(Room.room_type == room_type.lower())
        if guests:    q = q.filter(Room.capacity >= guests)
        return json.dumps([{
            "id": r.id, "number": r.room_number, "type": r.room_type,
            "price": r.price_per_night, "capacity": r.capacity
        } for r in q.all()])
    finally: s.close()


@mcp.tool()
def book_room(name: str, email: str, phone: str,
              room_id: int, check_in: str, check_out: str) -> str:
    """Book a room for a guest (creates customer if needed)."""
    s = SessionLocal()
    try:
        ci, co = date.fromisoformat(check_in), date.fromisoformat(check_out)
        if ci >= co: return "checkout must be after checkin"
        room = s.query(Room).filter(Room.id == room_id).first()
        if not room: return f"room {room_id} not found"
        conflict = s.query(Booking).filter(
            Booking.room_id == room.id,
            Booking.status.in_(["confirmed","checked_in"]),
            Booking.check_in < co, Booking.check_out > ci
        ).first()
        if conflict: return f"room {room.room_number} booked"
        cust = s.query(Customer).filter(Customer.email == email.lower()).first() \
               or Customer(name=name, email=email.lower(), phone=phone, address="")
        s.add(cust); s.flush()
        nights = (co-ci).days
        bk = Booking(customer_id=cust.id, room_id=room.id,
                     check_in=ci, check_out=co, status="confirmed",
                     total_amount=nights * room.price_per_night)
        s.add(bk); s.commit()
        return json.dumps({"booking_id": bk.id, "total": bk.total_amount})
    finally: s.close()


@mcp.tool()
def list_bookings(status: str = "") -> str:
    """List bookings, optionally by status."""
    s = SessionLocal()
    try:
        q = s.query(Booking)
        if status: q = q.filter(Booking.status == status)
        return json.dumps([{
            "id": b.id, "customer": b.customer.name,
            "room": b.room.room_number, "status": b.status,
            "check_in": str(b.check_in), "check_out": str(b.check_out),
            "total": b.total_amount
        } for b in q.limit(50).all()])
    finally: s.close()


if __name__ == "__main__":
    mcp.run()