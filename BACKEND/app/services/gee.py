import ee

# Initialize Earth Engine (pakai credential hasil earthengine authenticate)
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

def get_sentinel_composite(
    geometry: dict,
    year: int,
    months: list[int],
    cloud: int
):
    """
    Ambil Sentinel-2 composite + NDVI
    """

    # Build date range
    start_date = f"{year}-{min(months):02d}-01"
    end_date   = f"{year}-{max(months):02d}-28"

    # Area of interest
    aoi = ee.Geometry(geometry)

    # Sentinel-2 Surface Reflectance
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud))
    )

    # Median composite
    composite = collection.median().clip(aoi)

    # NDVI
    ndvi = composite.normalizedDifference(["B8", "B4"]).rename("NDVI")

    return composite, ndvi
