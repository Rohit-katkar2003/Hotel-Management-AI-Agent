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


@tool 
def update_customer(customer_id:int , name:str , email:str , address: str , phone:str)-> str: 
    """update customer details. 
    Args: 
        customer id: customer id of customer (required) 
        name: customer name of customer (optional) 
        email: email address of customer (optional) 
        address: address of customer (optional) 
        phone: phone number of customer
        """
    
    session = SessionLocal()  

    try: 
        customer = session.query(Customer).filter(Customer.id==customer_id).first() 
        if not customer: 
            return f"No customer found with id : {customer}"

        changes = [] 
        if name: 
            customer.name = name 
            changes.append(f"customer {customer.name} -> {name}") 
        
        if email: 
            # checking the email uniqueness  
            dup = session.query(Customer).filter(Customer.email==email.lower() , Customer.id != customer_id) 
            if dup: 
                return f"email {email} already exists in db please enter different address."
            customer.email = email 
            changes.append(f"email {customer.email} -> {email}") 

        if phone: 
            customer.phone = phone 
            changes.append(f"phone {customer.phone} -> {phone}") 

        if address: 
            customer.address = address  
            changes.append(f"address {customer.address} -> {address}") 

        session.commit()
        return f"✅ Customer {customer_id} updated: {', '.join(changes)}" 

    except Exception as e: 
        return f"Got error : {e}"
    finally: 
        session.close() 


@tool 
def delete_customer(customer_id:int=None , confirmed:bool=False)->str: 
    """delete the customer from the system. this action is irreversible. 
    set confirmed=True to actually delete. 
    Args: 
        customer_id : id of customer to delete 
        confirmed : must be True if confirm deletion.""" 

    session = SessionLocal() 
    try: 
        customer = session.query(Customer).filter(Customer.id ==  customer_id).first() 
        if not customer: 
            return f"Customer id : {customer_id} Not found." 
        if not confirmed: 
            return (
                f"⚠️ DELETION CONFIRMATION REQUIRED\n"
                f"   You are about to delete: {customer.name} (ID: {customer_id}, Email: {customer.email})\n"
                f"   This action CANNOT be undone.\n"
                f"   Ask the user to confirm, then call delete_customer with confirmed=True."
            ) 
        
        active_booking = [b for b in customer.bookings if b.status in ("confirmed" , "checked_in")] 
        if active_booking: 
            return (
                f"❌ Cannot delete — customer has {len(active_booking)} active booking(s). "
                f"Cancel or check-out bookings first."
            )
        
        name = customer.name 
        session.delete(customer) 
        session.commit() 
        return f"cusotmer id : {customer_id} | name : {name} removed successfully!"

    except Exception as e: 
        return f"got error - delete customer : {delete_customer}" 
    finally: 
        session.close() 


@tool 
def list_customer(search:str)->str: 
    """list all the customer or search name/email
    args: 
        search : Optional search term to filter by name or email.""" 
    session = SessionLocal() 
    try: 
        query = session.query(Customer)
        if search: 
            query = query.filter(
                (Customer.name.ilike(f"%{search}%")) | 
                (Customer.email.ilike(f"%{search}%"))
            )
        customers = query.order_by(Customer.id).all() 
        if not customers: 
            return "No cusotmers found." 
        
        lines = [f"📋 Customers ({len(customers)} found):\n"] 
        for c in customers: 
            lines.append(f" ID: {c.id} | {c.name} | {c.email} | {c.phone}") 
        
        return "\n".join(lines) 
    
    except Exception as e: 
        return f"Got error - list_customer : {e}" 
    finally: 
        session.close()