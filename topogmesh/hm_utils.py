import numpy as np
from yirgacheffe.layers import RasterLayer, VectorLayer
import yirgacheffe.operators as yo

def compress(height_map: np.ndarray, scale: float) -> np.ndarray:
    """
    Downsample a height map by a given scale factor using area averaging.

    Parameters
    ----------
    height_map : np.ndarray
        2D float array containing the heights of each vertex. `np.nan` values
        are used to mark invalid areas.
    scale : float
        Factor to scale the dimensions by. For example, 0.5 halves the number
        of pixels in each dimension, 2.0 doubles it.

    Returns
    -------
    np.ndarray
        The resampled height map after applying the scale factor.
    """
    if scale == 1.0:
        return height_map

    x_size = max(1, int(round(height_map.shape[0] * scale)))
    y_size = max(1, int(round(height_map.shape[1] * scale)))

    compressed_height_map = np.ndarray((x_size, y_size))

    scale_x = height_map.shape[0] / x_size
    scale_y = height_map.shape[1] / y_size

    for x in range(x_size):
        start_x = int(x * scale_x)
        end_x = int((x + 1) * scale_x)
        for y in range(y_size):
            start_y = int(y * scale_y)
            end_y = int((y + 1) * scale_y)
            area = height_map[start_x:end_x, start_y:end_y]
            avg_height = np.nanmean(area) if not np.all(np.isnan(area)) else np.nan
            compressed_height_map[x, y] = avg_height

    return compressed_height_map


def read_full_layer(raster: RasterLayer, dtype: type = float) -> RasterLayer:
    """
    Return the entire contents of a RasterLayer based on the specifications 
    of its window.

    Parameters
    ----------
    raster : RasterLayer
        A yirgacheffe raster layer
    dtype : type
        The typing of the contents of the array e.g. float or bool

    Returns
    -------
    np.ndarray
        The entire contents of the RasterLayer within its window.
    """
    array = raster.read_array(
        raster.window.xoff,
        raster.window.yoff,
        raster.window.xsize,
        raster.window.ysize
    ).astype(dtype)
    return array

def normalise(height_map: np.ndarray, base_height: float, max_height: float):
    zeroed_height_map = height_map + base_height - np.nanmin(height_map)
    normalised_height_map = zeroed_height_map / np.nanmax(zeroed_height_map) * max_height
    return normalised_height_map

def apply_mask(raster: RasterLayer, mask: VectorLayer, mask_with_nans: bool = True) -> RasterLayer:
    if mask_with_nans:
        mask = yo.where(mask == 0, np.nan, mask)

    mask_operation = raster * mask
    masked_raster = RasterLayer.empty_raster_layer_like(mask)
    mask_operation.save(masked_raster)

    return masked_raster