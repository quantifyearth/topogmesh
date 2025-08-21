import tempfile
from osgeo import gdal, osr, ogr
from yirgacheffe.layers import RasterLayer, VectorLayer
import yirgacheffe as yg
import os

def raster_to_utm(input_raster: RasterLayer) -> RasterLayer:
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=True) as tmpfile:
        input_raster.to_geotiff(tmpfile.name)
        ds = gdal.Open(tmpfile.name)
    gt = ds.GetGeoTransform()
    x_center = gt[0] + (ds.RasterXSize * gt[1]) / 2
    y_center = gt[3] + (ds.RasterYSize * gt[5]) / 2

    src_srs = osr.SpatialReference()
    src_srs.ImportFromWkt(ds.GetProjection())

    if not src_srs.IsGeographic():
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)  # WGS84
        ct = osr.CoordinateTransformation(src_srs, target_srs)
        x_center, y_center, _ = ct.TransformPoint(x_center, y_center)

    utm_zone = int((x_center + 180) / 6) + 1
    hemisphere = 'north' if y_center >= 0 else 'south'

    srs = osr.SpatialReference()
    srs.SetUTM(utm_zone, hemisphere == 'north')
    srs.SetWellKnownGeogCS("WGS84")

    dst_wkt = srs.ExportToWkt()

    with tempfile.NamedTemporaryFile(suffix='.tif', delete=True) as tmpfile:
        gdal.Warp(
            tmpfile.name,
            ds,
            dstSRS=dst_wkt,
            format="GTiff"
        )

        warped_raster = yg.read_raster(tmpfile.name)

    return warped_raster

def shape_to_utm(raster: RasterLayer, input_shp: str):
    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromWkt(raster.map_projection.name)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = os.path.join(tmpdir, "out.geojson")
        
        gdal.VectorTranslate(
            tmp_path,
            input_shp,
            dstSRS=raster_srs.ExportToWkt()
        )

        return yg.read_shape_like(tmp_path, like=raster)

