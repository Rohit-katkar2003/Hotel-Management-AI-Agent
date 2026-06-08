from langchain_core.tools import tool
from database.connection import SessionLocal
from database.models import Customer, Room, Booking
from datetime import date


@tool
def create_booking(customer_id: int, room_id: int, check_in: str, check_out: str) -> str:
    """Create a new booking for a customer.
    Args:
        customer_id: Customer ID
        room_id: Room ID
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
    """
    session = SessionLocal()
    try:
        ci = date.fromisoformat(check_in)
        co = date.fromisoformat(check_out)

        # Validate dates
        if ci >= co:
            return "❌ Check-out must be after check-in."
        if ci < date.today():
            return "❌ Check-in date cannot be in the past."

        # Validate customer
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return f"❌ Customer ID {customer_id} not found."

        # Validate room
        room = session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return f"❌ Room ID {room_id} not found."

        # Check for booking conflicts
        conflict = session.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.status.in_(["confirmed", "checked_in"]),
            Booking.check_in < co,
            Booking.check_out > ci
        ).first()
        if conflict:
            return (
                f"❌ Room {room.room_number} is already booked from "
                f"{conflict.check_in} to {conflict.check_out}."
            )

        # Calculate total
        nights = (co - ci).days
        total = nights * room.price_per_night

        booking = Booking(
            customer_id=customer_id,
            room_id=room_id,
            check_in=ci,
            check_out=co,
            status="confirmed",
            total_amount=total
        )
        session.add(booking)

        # Update room status
        room.status = "occupied"

        session.commit()

        return (
            f"✅ Booking created successfully!\n"
            f"   Booking ID: {booking.id}\n"
            f"   Customer: {customer.name}\n"
            f"   Room: {room.room_number} ({room.room_type})\n"
            f"   Check-in: {check_in}\n"
            f"   Check-out: {check_out}\n"
            f"   Nights: {nights}\n"
            f"   Total: ${total:.2f} ({nights} × ${room.price_per_night})\n"
            f"   Status: CONFIRMED"
        )
    except ValueError:
        return "❌ Invalid date format. Use YYYY-MM-DD."
    except Exception as e:
        session.rollback()
        return f"❌ Error creating booking: {str(e)}"
    finally:
        session.close()


@tool
def cancel_booking(booking_id: int, confirmed: bool = False) -> str:
    """Cancel a booking. Requires confirmation.
    Args:
        booking_id: Booking ID to cancel
        confirmed: Must be True to confirm cancellation
    """
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return f"❌ Booking ID {booking_id} not found."

        if booking.status in ("checked_out", "cancelled"):
            return f"❌ Booking is already {booking.status}."

        if not confirmed:
            return (
                f"⚠️ CANCELLATION CONFIRMATION\n"
                f"   Booking #{booking.id}: {booking.customer.name}\n"
                f"   Room {booking.room.room_number} | {booking.check_in} → {booking.check_out}\n"
                f"   Total: ${booking.total_amount:.2f}\n"
                f"   Confirm with the user, then call with confirmed=True."
            )

        booking.status = "cancelled"
        # Free up the room
        booking.room.status = "available"
        session.commit()

        return (
            f"✅ Booking #{booking_id} has been CANCELLED.\n"
            f"   Room {booking.room.room_number} is now available."
        )
    except Exception as e:
        session.rollback()
        return f"❌ Error: {str(e)}"
    finally:
        session.close()


@tool
def get_booking(booking_id: int) -> str:
    """Get details of a specific booking.
    Args:
        booking_id: Booking ID
    """
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return f"❌ Booking ID {booking_id} not found."

        nights = (booking.check_out - booking.check_in).days

        # Payment info
        total_paid = sum(p.amount for p in booking.payments if p.status == "completed")
        balance = booking.total_amount - total_paid

        return (
            f"📋 Booking Details:\n"
            f"   Booking ID: {booking.id}\n"
            f"   Customer: {booking.customer.name} (ID: {booking.customer_id})\n"
            f"   Room: {booking.room.room_number} ({booking.room.room_type})\n"
            f"   Check-in: {booking.check_in}\n"
            f"   Check-out: {booking.check_out}\n"
            f"   Nights: {nights}\n"
            f"   Total: ${booking.total_amount:.2f}\n"
            f"   Paid: ${total_paid:.2f}\n"
            f"   Balance: ${balance:.2f}\n"
            f"   Status: {booking.status.upper()}"
        )
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        session.close()


@tool
def list_bookings(customer_id: int = None, status: str = None) -> str:
    """List bookings, optionally filtered by customer or status.
    Args:
        customer_id: Filter by customer ID (optional)
        status: Filter by status - confirmed, checked_in, checked_out, cancelled (optional)
    """
    session = SessionLocal()
    try:
        query = session.query(Booking)
        if customer_id:
            query = query.filter(Booking.customer_id == customer_id)
        if status:
            query = query.filter(Booking.status == status.lower())

        bookings = query.order_by(Booking.id.desc()).limit(20).all()

        if not bookings:
            return "❌ No bookings found."

        lines = [f"📋 Bookings ({len(bookings)} found):\n"]
        for b in bookings:
            lines.append(
                f"   #{b.id} | {b.customer.name} | Room {b.room.room_number} | "
                f"{b.check_in} → {b.check_out} | ${b.total_amount:.2f} | {b.status.upper()}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        session.close()


@tool
def check_in_guest(booking_id: int) -> str:
    """Check in a guest using their booking ID.
    Args:
        booking_id: Booking ID
    """
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return f"❌ Booking ID {booking_id} not found."

        if booking.status == "checked_in":
            return f"⚠️ Guest is already checked in."
        if booking.status != "confirmed":
            return f"❌ Cannot check in — booking status is '{booking.status}'."

        if booking.check_in > date.today():
            return f"❌ Check-in date is {booking.check_in}. Too early to check in."

        booking.status = "checked_in"
        booking.room.status = "occupied"
        session.commit()

        return (
            f"✅ Check-in successful!\n"
            f"   Guest: {booking.customer.name}\n"
            f"   Room: {booking.room.room_number} ({booking.room.room_type})\n"
            f"   Stay: {booking.check_in} → {booking.check_out}\n"
            f"   Status: CHECKED IN 🏨"
        )
    except Exception as e:
        session.rollback()
        return f"❌ Error: {str(e)}"
    finally:
        session.close()


@tool
def check_out_guest(booking_id: int) -> str:
    """Check out a guest and free up the room.
    Args:
        booking_id: Booking ID
    """
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return f"❌ Booking ID {booking_id} not found."

        if booking.status != "checked_in":
            return f"❌ Cannot check out — booking status is '{booking.status}'. Must be checked_in first."

        booking.status = "checked_out"
        booking.room.status = "available"
        session.commit()

        # Check balance
        total_paid = sum(p.amount for p in booking.payments if p.status == "completed")
        balance = booking.total_amount - total_paid

        result = (
            f"✅ Check-out complete!\n"
            f"   Guest: {booking.customer.name}\n"
            f"   Room {booking.room.room_number} is now available.\n"
            f"   Total: ${booking.total_amount:.2f} | Paid: ${total_paid:.2f} | Balance: ${balance:.2f}"
        )
        if balance > 0:
            result += f"\n   ⚠️ Outstanding balance: ${balance:.2f}. Generate bill for payment."
        return result
    except Exception as e:
        session.rollback()
        return f"❌ Error: {str(e)}"
    finally:
        session.close()