from .connection import engine , SessionLocal 
from .models import Base , Room 
from datetime import datetime 


def init_database(): 
    Base.metadata.create_all(bind=engine) 

    session = SessionLocal() 

    try:
        # Seed rooms only if table is empty
        room_count = session.query(Room).count()
        if room_count == 0:
            seed_rooms = [
                Room(room_number="101", room_type="single",  price_per_night=80,  capacity=1, status="available"),
                Room(room_number="102", room_type="single",  price_per_night=80,  capacity=1, status="available"),
                Room(room_number="103", room_type="single",  price_per_night=90,  capacity=1, status="available"),
                Room(room_number="201", room_type="double",  price_per_night=130, capacity=2, status="available"),
                Room(room_number="202", room_type="double",  price_per_night=130, capacity=2, status="available"),
                Room(room_number="203", room_type="double",  price_per_night=140, capacity=3, status="available"),
                Room(room_number="301", room_type="suite",   price_per_night=250, capacity=2, status="available"),
                Room(room_number="302", room_type="suite",   price_per_night=280, capacity=3, status="available"),
                Room(room_number="401", room_type="deluxe",  price_per_night=400, capacity=2, status="available"),
                Room(room_number="402", room_type="deluxe",  price_per_night=450, capacity=4, status="available"),
            ]
            session.add_all(seed_rooms)
            session.commit()
            print("✅ Seeded 10 rooms")
        else:
            print(f"✅ Database already has {room_count} rooms")
    except Exception as e:
        session.rollback()
        print(f"❌ Seed error: {e}")
    finally:
        session.close()