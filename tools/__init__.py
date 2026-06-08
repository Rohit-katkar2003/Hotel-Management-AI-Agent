from .customer_tool import (
    add_customer, get_customer, update_customer,
    delete_customer, list_customers
)
from .room_tools import (
    search_available_rooms, get_room_details,
    update_room_price, list_rooms
)
from .booking_tools import (
    create_booking, cancel_booking, get_booking,
    list_bookings, check_in_guest, check_out_guest
)
from .billing_tool import generate_bill, process_payment

ALL_TOOLS = [
    # Customer tools
    add_customer, get_customer, update_customer, delete_customer, list_customers,
    # Room tools
    search_available_rooms, get_room_details, update_room_price, list_rooms,
    # Booking tools
    create_booking, cancel_booking, get_booking, list_bookings,
    check_in_guest, check_out_guest,
    # Billing tools
    generate_bill, process_payment,
]