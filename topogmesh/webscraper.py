from shapely.geometry import box
import osmnx as ox
from osmnx._errors import InsufficientResponseError
from yirgacheffe.layers import RasterLayer, VectorLayer
import yirgacheffe as yg
from pyproj import Transformer
import tempfile

ox.settings.use_cache = False

def mask_from_osm_tags(reference_layer: RasterLayer, tags: dict) -> VectorLayer:
    x_min = reference_layer.area.left
    x_max = reference_layer.area.right
    y_min = reference_layer.area.bottom
    y_max = reference_layer.area.top

    transformer = Transformer.from_crs(27700, 4326, always_xy=True)
    lon_min, lat_min = transformer.transform(x_min, y_min)
    lon_max, lat_max = transformer.transform(x_max, y_max)

    poly_xy = box(x_min, y_min, x_max, y_max)
    poly_latlon = box(lon_min, lat_min, lon_max, lat_max)

    try:
        gdf = ox.features_from_polygon(poly_latlon, tags=tags)
    except InsufficientResponseError:
        return None

    projected_gdf = gdf.to_crs(epsg=27700)
    clipped_gdf = projected_gdf.clip(poly_xy)
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=True) as tmp:
        temp_geojson_path = tmp.name
        clipped_gdf.to_file(temp_geojson_path, driver="GeoJSON")
        osm_tags_layer = yg.read_shape_like(temp_geojson_path, like=reference_layer)
    return osm_tags_layer