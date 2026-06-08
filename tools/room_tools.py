from langchain_core.tools import tool 
from database.connection import SessionLocal 
from database.models import Room , Booking 
from datetime import date 



@tool 
def search_availabel_rooms(room_type:str =None , check_in:str=None,
                           check_out:str=None , guests:int=None)-> str: 
    """search availabel rooms. Optionally filter by type , date range and guest count 
    Args: 
        room_type: Room type - single , double , suite or deluxe (optional)
        check-in : check-in date in YYYY-MM-DD format (optional)
        check-out : check-out date in YYYY-MM-DD format (optional)
        guests : number of guests (optional).""" 
    session = SessionLocal() 

    try: 
        query = session.query(Room).filter(Room.status != "maintenance") 

        if room_type: 
            query = query.filter(Room.room_type==room_type.lower()) 
        if guests: 
            query = query.filter(Room.capacity >= guests) 
        
        rooms = query.order_by(Room.price_per_night).all() 

        if not rooms: 
            return f"No rooms found" 
        availabel_rooms = [] 

        if check_in and check_out: 
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out) 
            if ci>=co: 
                return "❌ Check-out date must be after check-in date." 

            for room in rooms: 
                conflict = session.query(Booking).filter(
                    Booking.room_id == room.id , 
                    Booking.status._in(["confirmed", "checked_in"]) , 
                    Booking.check_in < co  , 
                    Booking.check_out > ci 

                ).first() 
                if not conflict: 
                    availabel_rooms.append(room) 
        else: 
            available_rooms = [r for r in rooms if r.status == "available"] 

        if not available_rooms:
            return "❌ No rooms available for the given criteria/dates."

        lines = [f"🏨 Available Rooms ({len(available_rooms)} found):\n"]
        for r in available_rooms:
            lines.append(
                f"   Room {r.room_number} | {r.room_type.upper()} | "
                f"${r.price_per_night}/night | Capacity: {r.capacity} | Status: {r.status}"
            )
        return "\n".join(lines)
    except ValueError:
        return "❌ Invalid date format. Use YYYY-MM-DD."
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        session.close() 
    

@tool 
def get_rooms_details(room_number:str , room_id:int) -> str: 

    """get detailed information about the specific room. 
    Args: 
        room_number: number of room (e.g. '101')
        room_id: Room ID (alternative to room number)""" 
    
    session = SessionLocal() 

    try: 
        if room_number: 
            room = session.query(Room).filter(Room.room_number == room_number).first() 
        
        elif room_id: 
            room =session.query(Room).filter(Room.id == room_id).first()
        
        else: 
            return "❌ Provide room_number or room_id." 
        
        if not room: 
            return "❌ Room not found." 
        
        active_booking = session.query(Booking).filter(
            Booking.room_id == room_id , 
            Booking.status._in(["confirmed", "checked_in"])
        ).first() 
        booking_info = "No booking found" 

        if active_booking: 
            booking_info = (
                f"Booking #{active_booking.id} | {active_booking.customer.name} | "
                f"{active_booking.check_in} → {active_booking.check_out} | Status: {active_booking.status}"
            ) 
        
        return (
            f"🛏️ Room Details:\n"
            f"   ID: {room.id}\n"
            f"   Room Number: {room.room_number}\n"
            f"   Type: {room.room_type.upper()}\n"
            f"   Price: ${room.price_per_night}/night\n"
            f"   Capacity: {room.capacity} guests\n"
            f"   Status: {room.status}\n"
            f"   Current Booking: {booking_info}"
        ) 
    
    except Exception as e: 
        pass

    finally: 
        session.close()
     
     
@tool
def update_room_price(room_id:int , new_price:float , confirmed:bool = False) -> str: 
    """Update room's price per night. required confirmation. 
    Args: 
        room_id : Id of room 
        new_price : new price of room per night (must be positive) 
        confirmed : Must be True to apply change.""" 
    session = SessionLocal() 
    try: 
        if new_price <= 0: 
            return "price must be the positive number" 
        
        room = session.query(Room).filter(Room.id == room_id).first()  
        if not room : 
            return f"no room found with id : {room_id}" 
        
        old_price = room.price_per_night 

        if not confirmed: 
            return (
                f"⚠️ PRICE CHANGE CONFIRMATION\n"
                f"   Room {room.room_number} ({room.room_type})\n"
                f"   Current: ${old_price}/night → New: ${new_price}/night\n"
                f"   Difference: ${new_price - old_price:+.2f}\n"
                f"   Confirm with the user, then call with confirmed=True."
            )

        room.price_per_night = new_price 
        session.commit()

    except Exception as e: 
        session.rollback()
        return f"❌ Error: {str(e)}"

    finally: 
        session.close()



@tool
def list_rooms(status: str = None, room_type: str = None) -> str:
    """List all rooms with optional filters.
    Args:
        status: Filter by status - available, occupied, maintenance (optional)
        room_type: Filter by type - single, double, suite, deluxe (optional)
    """
    session = SessionLocal()
    try:
        query = session.query(Room)
        if status:
            query = query.filter(Room.status == status.lower())
        if room_type:
            query = query.filter(Room.room_type == room_type.lower())

        rooms = query.order_by(Room.room_number).all()

        if not rooms:
            return "❌ No rooms found."

        lines = [f"🏨 Rooms ({len(rooms)} found):\n"]
        for r in rooms:
            lines.append(
                f"   ID: {r.id} | Room {r.room_number} | {r.room_type.upper()} | "
                f"${r.price_per_night}/night | Cap: {r.capacity} | {r.status.upper()}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        session.close()