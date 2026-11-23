# Rename your image files to these clean names first (see §9).
ROOM_IMAGES = {
    "single": "/static/images/3d-rendering-luxury-bedroom-suite-resort-hotel-with-twin-bed-living.jpg",
    "double": "/static/images/double sharing.jpg",
    "suite":  "/static/images/suite.jpg",
    "deluxe": "/static/images/deluxe.jpg",
}
def image_for(room_type: str) -> str:
    return ROOM_IMAGES.get(room_type.lower(), ROOM_IMAGES["double"])