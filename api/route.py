from fastapi import APIRouter , Query , HTTPException 
from schemas import  (ChatRequest , ChatResponse ,
                     CustomerResponse  , CustomerCreate ,
                     CustomerUpdate , RoomResponse)
from graph import graph 
from database import SessionLocal , Customer  , Room , Booking
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


