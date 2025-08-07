import numpy as np
from yirgacheffe.layers import TiledGroupLayer, RasterLayer, VectorLayer
import yirgacheffe.operators as yo

def read_geojson(path, reference_raster) -> np.ndarray[tuple[float, float]]:
    polygon_layer = VectorLayer.layer_from_file_like(path, other_layer=reference_raster)
    polygon_layer = yo.where(polygon_layer == 0, np.nan, polygon_layer)
    return polygon_layer

def read_tifs(tif_paths: list[str]) -> TiledGroupLayer:
    rasters = []
    for path in tif_paths:
        raster = read_tif(path)
        rasters.append(raster)
    group_rasters = TiledGroupLayer(rasters)
    return group_rasters

def read_tif(tif_path: str) -> RasterLayer:
    raster = RasterLayer.layer_from_file(tif_path)
    return raster