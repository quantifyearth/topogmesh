import numpy as np
from yirgacheffe.layers import RasterLayer, VectorLayer
import yirgacheffe.operators as yo


def read_full_layer(raster: RasterLayer, dtype: type = float) -> np.ndarray:
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


def apply_mask(raster: RasterLayer, mask: VectorLayer, mask_with_nans: bool = True) -> RasterLayer:
    """
    Apply a yirgacheffe VectorLayer as a mask to a RasterLayer and returns
    the result as a new RasterLayer.

    Parameters
    ----------
    raster : RasterLayer
        The layer which the mask is applied to.
    mask : VectorLayer
        The mask being applied to the raster.
    mask_with_nans : bool
        Sets values outside the polygon to NaN if True, otherwise to 0.

    Returns
    -------
    RaterLayer
        The resultant masked RasterLayer
    """
    if mask_with_nans:
        mask = yo.where(mask == 0, np.nan, mask)

    mask_operation = raster * mask
    masked_raster = RasterLayer.empty_raster_layer_like(mask_operation)
    mask_operation.save(masked_raster)

    return masked_raster