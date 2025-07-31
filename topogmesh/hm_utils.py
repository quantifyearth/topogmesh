import numpy as np
from yirgacheffe.layers import GroupLayer
from yirgacheffe.window import Area
import math

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


def get_bounding_box(indexes: np.ndarray[tuple[int, int]]) -> tuple[int, int, int, int]:
    """
    Compute the bounding box for a set of pixel indexes.

    Parameters
    ----------
    indexes : np.ndarray of shape (N, 2)
        Array of (x, y) pixel coordinates.

    Returns
    -------
    tuple of int
        (min_x, min_y, width, height) of the bounding box in pixel units.
    """
    xs = indexes[:, 0]
    ys = indexes[:, 1]
    width = xs.max() - xs.min() + 1
    height = ys.max() - ys.min() + 1
    return xs.min(), ys.min(), width, height


def get_shape(group: GroupLayer):
    """
    Get the pixel dimensions of a group layer.

    Parameters
    ----------
    group : GroupLayer
        A group of raster layers.

    Returns
    -------
    tuple of int
        (x_size, y_size) pixel dimensions of the group layer.
    """
    bottom = group.area.bottom
    right = group.area.right
    return group.pixel_for_latlng(bottom, right)


def get_area(polygon: np.ndarray[tuple[float, float]]) -> Area:
    """
    Compute the geographic area covered by a polygon.

    Parameters
    ----------
    polygon : np.ndarray of shape (N, 2)
        Array of (x, y) coordinates defining the polygon vertices.

    Returns
    -------
    Area
        An Area object with left, top, right, and bottom boundaries in the
        same coordinate reference system as the polygon.
    """
    left = polygon[:, 0].min().item()
    right = polygon[:, 0].max().item()
    bottom = polygon[:, 1].min().item()
    top = polygon[:, 1].max().item()
    return Area(left, top, right, bottom)


def tiles_needed(polygon: np.ndarray[tuple[int, int]]) -> list[str]:
    """
    Get the names of the tiles (latitude/longitude) required to construct a mesh for the given polygon.

    Parameters
    ----------
    polygon : np.ndarray of shape (N, 2)
        Array of (x, y) coordinates defining the polygon vertices.

    list of str
        A list of tile names covering the polygon's bounding box.
    """
    lons = [lon for lon, lat in polygon]
    lats = [lat for lon, lat in polygon]
    min_lon, max_lon = math.floor(min(lons)), math.ceil(max(lons))
    min_lat, max_lat = math.floor(min(lats)), math.ceil(max(lats))

    def get_tile_name(lon: int, lat: int) -> str:
        ns = 'N' if lat >= 0 else 'S'
        ew = 'E' if lon >= 0 else 'W'
        return f'{ns}{abs(int(lat)):02}{ew}{abs(int(lon)):03}'

    tiles = []
    for lon in range(min_lon, max_lon + 1):
        for lat in range(min_lat, max_lat + 1):
            tiles.append(get_tile_name(lon, lat))
    return tiles