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
def get_customer(customer_id :int = None , email:str=None) -> str: 
    """retreive customer through cusotmer id or email. provide at least one.
    Args: 
        customer_id: customer ID number 
        email: customer email address."""

    session = SessionLocal() 
    try: 
        if customer_id:
            customer = session.query(Customer).filter(Customer.id==customer_id).first()
        elif email: 
            customer = session.query(Customer).filter(Customer.email==email).first()
        else: 
            return "❌ Provide either customer_id or email to search."

        if not customer:
            return "❌ Customer not found."
        
        return  (
            f"👤 Customer Found:\n"
            f"   ID: {customer.id}\n"
            f"   Name: {customer.name}\n"
            f"   Email: {customer.email}\n"
            f"   Phone: {customer.phone}\n"
            f"   Address: {customer.address or 'N/A'}\n"
            f"   Joined: {customer.created_at.strftime('%Y-%m-%d')}"
        )
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        session.close()


