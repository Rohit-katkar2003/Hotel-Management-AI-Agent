from langchain_core.tools import tool
from database.connection import SessionLocal
from database.models import Booking, Payment


@tool
def generate_bill(booking_id: int) -> str:
    """Generate a detailed bill for a booking.
    Args:
        booking_id: Booking ID
    """
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return f"❌ Booking ID {booking_id} not found."

        nights = (booking.check_out - booking.check_in).days
        price_per_night = booking.room.price_per_night
        room_charges = nights * price_per_night

        # Payment history
        payments = booking.payments
        total_paid = sum(p.amount for p in payments if p.status == "completed")
        balance = booking.total_amount - total_paid

        bill = (
            f"🧾 ═══════════════════════════════════\n"
            f"   HOTEL BILL — Booking #{booking.id}\n"
            f"═══════════════════════════════════\n"
            f"   Guest: {booking.customer.name}\n"
            f"   Room:  {booking.room.room_number} ({booking.room.room_type})\n"
            f"   Check-in:  {booking.check_in}\n"
            f"   Check-out: {booking.check_out}\n"
            f"   ────────────────────────────\n"
            f"   Room Charges: {nights} nights × ${price_per_night} = ${room_charges:.2f}\n"
            f"   ────────────────────────────\n"
            f"   TOTAL:    ${booking.total_amount:.2f}\n"
            f"   PAID:     ${total_paid:.2f}\n"
            f"   BALANCE:  ${balance:.2f}\n"
            f"═══════════════════════════════════\n"
        )

        if payments:
            bill += "   Payment History:\n"
            for p in payments:
                bill += f"     • ${p.amount:.2f} via {p.method.upper()} on {p.paid_at.strftime('%Y-%m-%d')} [{p.status}]\n"

        if balance > 0:
            bill += f"\n   ⚠️ Outstanding: ${balance:.2f}. Use process_payment to record payment."
        else:
            bill += "\n   ✅ Bill is fully paid!"

        return bill
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        session.close()


@tool
def process_payment(booking_id: int, amount: float, method: str = "card") -> str:
    """Process a payment for a booking.
    Args:
        booking_id: Booking ID
        amount: Payment amount
        method: Payment method - cash, card, or upi
    """
    session = SessionLocal()
    try:
        method = method.lower()
        if method not in ("cash", "card", "upi"):
            return "❌ Invalid payment method. Use: cash, card, or upi."

        if amount <= 0:
            return "❌ Payment amount must be positive."

        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return f"❌ Booking ID {booking_id} not found."

        # Check how much is already paid
        total_paid = sum(p.amount for p in booking.payments if p.status == "completed")
        balance = booking.total_amount - total_paid

        if balance <= 0:
            return "✅ This booking is already fully paid."

        if amount > balance:
            return (
                f"⚠️ Payment ${amount:.2f} exceeds outstanding balance ${balance:.2f}.\n"
                f"   Maximum payment needed: ${balance:.2f}"
            )

        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            method=method,
            status="completed"
        )
        session.add(payment)
        session.commit()

        new_total_paid = total_paid + amount
        new_balance = booking.total_amount - new_total_paid

        result = (
            f"✅ Payment processed!\n"
            f"   Amount: ${amount:.2f} via {method.upper()}\n"
            f"   Booking #{booking_id}: ${booking.total_amount:.2f} total | "
            f"${new_total_paid:.2f} paid | ${new_balance:.2f} remaining"
        )
        if new_balance <= 0:
            result += "\n   🎉 Bill is now fully paid!"
        return result
    except Exception as e:
        session.rollback()
        return f"❌ Error: {str(e)}"
    finally:
        session.close()