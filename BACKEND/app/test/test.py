import ee
from app.services.gee import get_sentinel_composite

geometry = {
    "type": "Polygon",
    "coordinates": [[[110.1,-7.1],[110.2,-7.1],[110.2,-7.2],[110.1,-7.2],[110.1,-7.1]]]
}

composite, ndvi = get_sentinel_composite(
    geometry=geometry,
    year=2024,
    months=[6,7,8],
    cloud=20
)

print(composite)
print(ndvi)
