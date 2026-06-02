from database.connection import SessionLocal 
from database.models import Customer 
from langchain_core.tools import tool 



@tool 
def create_customer(name:str , email:str , phone:str , address:str = "not provided") -> str:   
    """add the customer to hotel system.
    Args: 
     name: name of customer. 
     email: email address(must be unique and valid). 
     phone: phone number. 
     address: Residential address(optional) 

    """ 
    session = SessionLocal() 
    try: 
        existing = session.query(Customer).filter(Customer.email==email.lower()).first() 
        if existing: 
            return f"❌ Customer with email '{email}' already exists (ID: {existing.id})" 

        customer = Customer(name=name , email=email.lower() , phone=phone , address=address) 
        session.add(customer) 
        session.commit() 

        return (
            f"✅ Customer added successfully!\n"
            f"   ID: {customer.id}\n"
            f"   Name: {customer.name}\n"
            f"   Email: {customer.email}\n"
            f"   Phone: {customer.phone}"
        ) 
    
    except Exception as e: 
        session.rollback() 
        return f" Error adding customer: {e}" 
    finally: 
        session.close() 


@tool 
def 