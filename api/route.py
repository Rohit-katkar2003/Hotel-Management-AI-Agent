from fastapi import APIRouter , Query , HTTPException 
from schemas import  (ChatRequest , ChatResponse ,
                     CustomerResponse  , CustomerCreate ,
                     CustomerUpdate)
from graph import graph 
from database import SessionLocal , Customer 
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
