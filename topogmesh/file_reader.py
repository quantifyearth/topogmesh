from osgeo import ogr
import numpy as np
from yirgacheffe.layers import TiledGroupLayer, RasterLayer

def read_polygon(path) -> np.ndarray[tuple[float, float]]:
    """
    Read the outer boundary coordinates from a shapefile polygon or multipolygon.

    Opens the specified shapefile, extracts the first ring of each polygon or
    multipolygon, and returns the coordinates as a NumPy array of (x, y) pairs.

    Parameters
    ----------
    path : str
        Path to the input shapefile (.shp).

    Returns
    -------
    np.ndarray of shape (N, 2)
        Array of polygon coordinates as floats in (x, y) order.
    """
    ds = ogr.Open(path)
    layer = ds.GetLayer()
    coords = []

    for feature in layer:
        geom = feature.GetGeometryRef()

        if geom.GetGeometryType() == ogr.wkbPolygon:
            ring = geom.GetGeometryRef(0)
            for pt in ring.GetPoints():
                coords.append([float(pt[0]), float(pt[1])])

        elif geom.GetGeometryType() == ogr.wkbMultiPolygon:
            for i in range(geom.GetGeometryCount()):
                poly = geom.GetGeometryRef(i)
                ring = poly.GetGeometryRef(0)
                for pt in ring.GetPoints():
                    coords.append([float(pt[0]), float(pt[1])])
    
    return np.array(coords)

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