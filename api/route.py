from fastapi import APIRouter , Query , HTTPException 
from schemas import  (ChatRequest , ChatResponse ,
                     CustomerResponse  , CustomerCreate ,
                     CustomerUpdate , RoomResponse , BookingCreate , BookingResponse , 
                     PaymentResponse , PaymentRequest)
from graph import graph 
from database import SessionLocal , Customer  , Room , Booking , Payment
from langchain_core.messages import AIMessage , HumanMessage
import uuid ,json 


router = APIRouter()

@router.post("/chat" , response_model=ChatResponse)
def chat(request: ChatRequest):

    thread_id = request.thread_id or str(uuid.uuid4) 
    config = {"configurable":{" thread_id" : str(thread_id)}}
    try: 
        response = graph.invoke({"messages":request.message} ,config) 

        reply = "" 
        for msg in reversed(response["messages"]): 
            if isinstance(msg , AIMessage) and msg.content:  
                reply = msg.content
                break 
 
        return ChatResponse(reply=reply , thread_id=thread_id)
    
    except Exception as e: 
        return f"Got error /chat : {e}" 

@router.post("/chat/stream") 
def chat_stream(request:ChatRequest): 
    """stream the chat responses  from Hotel AI Agent """ 
    from fastapi.responses import StreamingResponse 
    import json

    thread_id = request.thread_id or str(uuid.uuid4)
    config = {"configurable":{"thread_id":str(thread_id)}}

    def event_generator(): 
        for event in graph.stream({
            "messages": [HumanMessage(content=request.message)],
        } , config=config , 
        stream_mode="values" ): 
            if event.get("messages"):
                last_msg = event["messages"][-1] 
                if isinstance(last_msg , AIMessage) and last_msg.content: 
                    data = json.dumps({
                        "type": "AIMessage" , 
                        "content":last_msg.content , 
                        "thread_id":thread_id
                    }) 
                    yield f"data: {data} \n\n" 
        
        yield f"data: {json.dumps({"type":"done" , "thread_id":thread_id})}\n\n" 

    return StreamingResponse(event_generator() , media_type="text/event-stream") 


@router.get("chat/history/{thread_id}") 
def get_chat_history(thread_id:str): 
    """get chat history by thread""" 
    config = {"configurable": {"thread_id":str(thread_id)}} 
    try:
        state = graph.get_state(config)
        if not state or not state.values:
            return {"messages": [], "thread_id": thread_id}

        messages = []
        for msg in state.values.get("messages", []):
            messages.append({
                "role": msg.type,
                "content": msg.content
            })

        return {"messages": messages, "thread_id": thread_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Thread not found: {str(e)}")

 
## for customers 


@router.post("/customers" , response_model=CustomerResponse) 
def create_customer(data : CustomerCreate):  
    session = SessionLocal() 
    try: 
        existing = session.query(Customer).filter(Customer.email==data.email.lower()).first() 
        if existing: 
            raise HTTPException(status_code=400 , detail=f"Email {data.email.lower()} already exist.") 
        
        customer = Customer(
            name = data.name , email=data.email.lower() , 
            phone=data.phone , address = data.address
         )
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@router.get("/customers" , response_model=list[CustomerResponse] )
def get_customer(search:str = Query(None , description="search by the name and email")): 

    session = SessionLocal() 
    try: 
        query = session.query(Customer) 
        if search : 

            query = query.filter((Customer.name.ilike(f"%{search}%")) | (Customer.email.ilike(f"%{search}%")))
        return query.order_by(Customer.id).all()

    except Exception as e: 
        raise HTTPException(status_code=500  , detail=f"Got error  {e}") 
    
    finally: 
        session.close()


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int):
    """Get a specific customer by ID."""
    session = SessionLocal()
    try:
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    finally:
        session.close() 


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, data: CustomerUpdate):
    """Update customer details."""
    session = SessionLocal()
    try:
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        if data.name:
            customer.name = data.name
        if data.email:
            dup = session.query(Customer).filter(
                Customer.email == data.email.lower(), Customer.id != customer_id
            ).first()
            if dup:
                raise HTTPException(status_code=400, detail="Email already in use")
            customer.email = data.email.lower()
        if data.phone:
            customer.phone = data.phone
        if data.address:
            customer.address = data.address

        session.commit()
        session.refresh(customer)
        return customer
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: int):
    """Delete a customer."""
    session = SessionLocal()
    try:
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        active = [b for b in customer.bookings if b.status in ("confirmed", "checked_in")]
        if active:
            raise HTTPException(
                status_code=400,
                detail=f"Customer has {len(active)} active booking(s). Cancel them first."
            )

        session.delete(customer)
        session.commit()
        return {"message": f"Customer {customer_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


## Room Endpoints 
@router.get("/rooms" , response_model=list[RoomResponse]) 
def get_rooms(
    status : str = Query(None) , 
    room_type:str =Query(None)
):
    """List all the rooms.""" 
    session = SessionLocal() 

    try: 
        query = session.query(Room) 
        if status: 
            query = query.filter(Room.status==status.lower())
        if room_type: 
            query = query.filter(Room.room_type == room_type.lower()) 
        
        return query.order_by(Room.room_number).all() 
    
    except Exception as e: 
        raise HTTPException(status_code=500 , detail=f"Got error {e}") 
    finally: 
        session.close()


@router.get("/rooms/available")
def get_available_rooms(
    room_type: str = Query(None),
    check_in: str = Query(None),
    check_out: str = Query(None),
    guests: int = Query(None)
):
    """Find available rooms for given criteria."""
    session = SessionLocal()
    try:
        from datetime import date as date_type
        query = session.query(Room).filter(Room.status != "maintenance")
        if room_type:
            query = query.filter(Room.room_type == room_type.lower())
        if guests:
            query = query.filter(Room.capacity >= guests)

        rooms = query.order_by(Room.price_per_night).all()
        available = []

        if check_in and check_out:
            ci = date_type.fromisoformat(check_in)
            co = date_type.fromisoformat(check_out)
            for room in rooms:
                conflict = session.query(Booking).filter(
                    Booking.room_id == room.id,
                    Booking.status.in_(["confirmed", "checked_in"]),
                    Booking.check_in < co,
                    Booking.check_out > ci
                ).first()
                if not conflict:
                    available.append(room)
        else:
            available = [r for r in rooms if r.status == "available"]

        return [
            {
                "id": r.id, "room_number": r.room_number,
                "room_type": r.room_type, "price_per_night": r.price_per_night,
                "capacity": r.capacity, "status": r.status
            }
            for r in available
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room(room_id: int):
    """Get room details."""
    session = SessionLocal()
    try:
        room = session.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return room
    finally:
        session.close()


@router.patch("/rooms/{room_id}/price")
def update_room_price_api(room_id: int, new_price: float = Query(..., gt=0)):
    """Update room price via REST API."""
    session = SessionLocal()
    try:
        room = session.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        old_price = room.price_per_night
        room.price_per_night = new_price
        session.commit()
        return {
            "message": f"Room {room.room_number} price updated",
            "old_price": old_price, "new_price": new_price
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close() 


## Booking 

@router.post("/bookings", response_model=BookingResponse)
def create_booking(data: BookingCreate):
    """Create a new booking via REST API."""
    session = SessionLocal()
    try:
        customer = session.query(Customer).filter(Customer.id == data.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        room = session.query(Room).filter(Room.id == data.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if data.check_in >= data.check_out:
            raise HTTPException(status_code=400, detail="Check-out must be after check-in")

        conflict = session.query(Booking).filter(
            Booking.room_id == data.room_id,
            Booking.status.in_(["confirmed", "checked_in"]),
            Booking.check_in < data.check_out,
            Booking.check_out > data.check_in
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail="Room is booked for those dates")

        nights = (data.check_out - data.check_in).days
        total = nights * room.price_per_night

        booking = Booking(
            customer_id=data.customer_id, room_id=data.room_id,
            check_in=data.check_in, check_out=data.check_out,
            status="confirmed", total_amount=total
        )
        session.add(booking)
        room.status = "occupied"
        session.commit()
        session.refresh(booking)
        return booking
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/bookings", response_model=list[BookingResponse])
def get_bookings(
    customer_id: int = Query(None),
    status: str = Query(None)
):
    """List bookings with optional filters."""
    session = SessionLocal()
    try:
        query = session.query(Booking)
        if customer_id:
            query = query.filter(Booking.customer_id == customer_id)
        if status:
            query = query.filter(Booking.status == status.lower())
        return query.order_by(Booking.id.desc()).limit(50).all()
    finally:
        session.close()


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int):
    """Get booking details."""
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    finally:
        session.close()


@router.patch("/bookings/{booking_id}/cancel")
def cancel_booking_api(booking_id: int):
    """Cancel a booking."""
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status in ("checked_out", "cancelled"):
            raise HTTPException(status_code=400, detail=f"Booking already {booking.status}")

        booking.status = "cancelled"
        booking.room.status = "available"
        session.commit()
        return {"message": f"Booking {booking_id} cancelled", "room_freed": booking.room.room_number}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.patch("/bookings/{booking_id}/checkin")
def check_in_api(booking_id: int):
    """Check in a guest."""
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status != "confirmed":
            raise HTTPException(status_code=400, detail=f"Cannot check in — status is '{booking.status}'")

        booking.status = "checked_in"
        booking.room.status = "occupied"
        session.commit()
        return {"message": f"Guest checked in", "room": booking.room.room_number}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.patch("/bookings/{booking_id}/checkout")
def check_out_api(booking_id: int):
    """Check out a guest."""
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status != "checked_in":
            raise HTTPException(status_code=400, detail=f"Cannot check out — status is '{booking.status}'")

        total_paid = sum(p.amount for p in booking.payments if p.status == "completed")
        balance = booking.total_amount - total_paid

        booking.status = "checked_out"
        booking.room.status = "available"
        session.commit()
        return {
            "message": f"Guest checked out",
            "room_freed": booking.room.room_number,
            "total": booking.total_amount,
            "paid": total_paid,
            "balance": balance
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()



# ═══════════════════════════════════════════
# BILLING / PAYMENT ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/bookings/{booking_id}/bill")
def get_bill_api(booking_id: int):
    """Get bill details for a booking."""
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        nights = (booking.check_out - booking.check_in).days
        total_paid = sum(p.amount for p in booking.payments if p.status == "completed")

        return {
            "booking_id": booking.id,
            "guest": booking.customer.name,
            "room": booking.room.room_number,
            "room_type": booking.room.room_type,
            "check_in": str(booking.check_in),
            "check_out": str(booking.check_out),
            "nights": nights,
            "price_per_night": booking.room.price_per_night,
            "room_charges": nights * booking.room.price_per_night,
            "total": booking.total_amount,
            "paid": total_paid,
            "balance": booking.total_amount - total_paid,
            "status": booking.status
        }
    finally:
        session.close()


@router.post("/payments", response_model=PaymentResponse)
def make_payment(data: PaymentRequest):
    """Process a payment for a booking."""
    session = SessionLocal()
    try:
        if data.method.lower() not in ("cash", "card", "upi"):
            raise HTTPException(status_code=400, detail="Method must be cash, card, or upi")

        booking = session.query(Booking).filter(Booking.id == data.booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        total_paid = sum(p.amount for p in booking.payments if p.status == "completed")
        balance = booking.total_amount - total_paid

        if balance <= 0:
            raise HTTPException(status_code=400, detail="Booking is already fully paid")
        if data.amount > balance:
            raise HTTPException(
                status_code=400,
                detail=f"Amount ${data.amount} exceeds balance ${balance:.2f}"
            )

        payment = Payment(
            booking_id=data.booking_id,
            amount=data.amount,
            method=data.method.lower(),
            status="completed"
        )
        session.add(payment)
        session.commit()
        session.refresh(payment)
        return payment
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ═══════════════════════════════════════════
# DASHBOARD / STATS
# ═══════════════════════════════════════════

@router.get("/stats")
def get_stats():
    """Get hotel dashboard statistics."""
    session = SessionLocal()
    try:
        total_customers = session.query(Customer).count()
        total_rooms = session.query(Room).count()
        available_rooms = session.query(Room).filter(Room.status == "available").count()
        occupied_rooms = session.query(Room).filter(Room.status == "occupied").count()
        active_bookings = session.query(Booking).filter(
            Booking.status.in_(["confirmed", "checked_in"])
        ).count()
        total_revenue = sum(
            p.amount for p in session.query(Payment).filter(Payment.status == "completed").all()
        )

        return {
            "customers": total_customers,
            "rooms": {"total": total_rooms, "available": available_rooms, "occupied": occupied_rooms},
            "active_bookings": active_bookings,
            "total_revenue": round(total_revenue, 2),
            "occupancy_rate": round(occupied_rooms / max(total_rooms, 1) * 100, 1)
        }
    finally:
        session.close()

