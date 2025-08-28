from shapely.geometry import box
import osmnx as ox
from osmnx._errors import InsufficientResponseError
from yirgacheffe.layers import RasterLayer, VectorLayer, GroupLayer
import yirgacheffe as yg
from pyproj import Transformer
import tempfile
import requests
import zipfile
from io import BytesIO
import geopandas as gpd
from pathlib import Path

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

def get_lidar_layer(base_url: str, output_path: str) -> None:
    print(f"Downloading {base_url}")
    KEY = "?subscription-key=public"
    url = f"{base_url}{KEY}"
    data = requests.get(url)
    data.raise_for_status()
    with zipfile.ZipFile(BytesIO(data.content)) as z:
        tif_name = next(name for name in z.namelist() if name.lower().endswith(".tif"))
        with z.open(tif_name) as tif_data:
            with open(output_path, "wb") as tif:
                tif.write(tif_data.read())

def get_uk_tiles(shape_path: str, output_dir: Path) -> None:
    URL = "https://environment.data.gov.uk/backend/catalog/api/tiles/collections/survey/search"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        shapefile_path = tmpdir / "output.shp"

        gdf = gpd.read_file(shape_path)
        gdf = gdf.to_crs("EPSG:27700")
        gdf.to_file(shapefile_path, driver="ESRI Shapefile")

        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp_zip:
            with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as z:
                for file in tmpdir.iterdir():
                    if file.suffix in {".shp", ".shx", ".dbf", ".prj"}:
                        z.write(file, arcname=file.name)
            tmp_zip.flush()
            tmp_zip.seek(0)
            data = tmp_zip.read()

    headers = {"Content-Type": "application/zipped-shapefile"}
    r = requests.post(URL, headers=headers, data=data)
    r.raise_for_status()
    json_data = r.json()

    wanted_ids = [
        'national_lidar_programme_first_return_dsm',
        'national_lidar_programme_dtm',
    ]
    selected_data = {}
    for product in json_data['results']:
        if product['product']['id'] in wanted_ids:
            composite_key = (product['product']['id'], product['tile']['id'])
            year = int(product['year']['id'])
            uri = product['uri']
            if composite_key not in selected_data:
                selected_data[composite_key] = (year, uri)
            elif year > selected_data[composite_key][0]:
                selected_data[composite_key] = (year, uri)

    get_uris_for_layer = lambda layer_type: [selected_data[(layer, tile)][1] for layer, tile in selected_data if layer == layer_type]
    for layer_type in wanted_ids:
        layer_dir = Path(f"{output_dir}/{layer_type}")
        layer_dir.mkdir(parents=True, exist_ok=True)
        for uri in get_uris_for_layer(layer_type):
            tile_name = Path(uri).name
            output_path = layer_dir / tile_name
            get_lidar_layer(uri, output_path)

if __name__ == "__main__":
    get_uk_tiles("tests/buckingham.geojson", "tests")