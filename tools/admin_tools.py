from tools.customer_tool import (add_customer, get_customer, update_customer,
                                  delete_customer, list_customers)
from tools.room_tools import (search_available_rooms as _admin_search,
                              get_room_details, update_room_price, list_rooms)
from tools.booking_tools import (create_booking, cancel_booking, get_booking,
                                 list_bookings, check_in_guest, check_out_guest)
from tools.billing_tool import generate_bill, process_payment
from tools.user_tools import search_available_rooms

ADMIN_TOOLS = [
    add_customer, get_customer, update_customer, delete_customer, list_customers,
    search_available_rooms, get_room_details, update_room_price, list_rooms,
    create_booking, cancel_booking, get_booking, list_bookings,
    check_in_guest, check_out_guest,
    generate_bill, process_payment,
]