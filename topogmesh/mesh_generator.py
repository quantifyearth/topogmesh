import numpy as np
from .hm_utils import compress
from .mesh import Mesh, Vertex, Triangle
import yirgacheffe as yg
import yirgacheffe.operators as yo
from yirgacheffe.layers import RasterLayer


def create_mesh(height_map: np.ndarray, scale: float = 1) -> Mesh:
    """
    Generate a 3D mesh from a 2D height map.

    Parameters
    ----------
    height_map : np.ndarray of shape (H, W)
        2D array of height values. Use `np.nan` to mark areas outside the model.
    scale : float, optional
        Distance between adjacent vertices in model units. Default is 1.

    Returns
    -------
    Mesh
        A mesh object containing vertices and triangles representing the terrain,
        including a base and side walls.
    """
    valid = ~np.isnan(height_map)
    x_size, y_size = height_map.shape

    vert_idx = np.full((x_size, y_size), -1, dtype=int)
    verts = []
    # surface vertices
    for i in range(x_size):
        for j in range(y_size):
            if valid[i, j]:
                vert_idx[i, j] = len(verts)
                verts.append(Vertex(i * scale, j * scale, height_map[i, j] * scale))

    base_offset = len(verts)
    # base vertices
    for i in range(x_size):
        for j in range(y_size):
            if valid[i, j]:
                verts.append(Vertex(i * scale, j * scale, 0))


    tris = []
    # surface triangles
    for i in range(x_size-1):
        for j in range(y_size-1):
            a = vert_idx[i  , j]
            b = vert_idx[i+1, j]
            c = vert_idx[i  , j+1]
            d = vert_idx[i+1, j+1]
            if min(a, b, c, d) > 0:
                tris.append(Triangle(a, b, c))
                tris.append(Triangle(b, d, c))

    # base triangles
    for i in range(x_size-1):
        for j in range(y_size-1):
            a = vert_idx[i  , j]
            b = vert_idx[i+1, j]
            c = vert_idx[i  , j+1]
            d = vert_idx[i+1, j+1]
            if min(a, b, c, d) >= 0:
                tris.append(Triangle(base_offset + a, base_offset + c, base_offset + b))
                tris.append(Triangle(base_offset + b, base_offset + c, base_offset + d))

    #Side triangles
    for i in range(x_size):
        for j in range(y_size):
            if not valid[i, j]:
                continue

            curr_top = vert_idx[i, j]
            curr_bot = base_offset + curr_top

            # Check each direction for boundary walls
            # Right edge
            if i < x_size-1 and valid[i+1, j]:
                # Check if we need a wall between these cells
                need_wall = False
                if j == 0 or not valid[i, j-1] or not valid[i+1, j-1]:
                    need_wall = True
                elif j == y_size-1 or not valid[i, j+1] or not valid[i+1, j+1]:
                    need_wall = True

                if need_wall:
                    right_top = vert_idx[i+1, j]
                    right_bot = base_offset + right_top
                    # Create wall facing outward from invalid region
                    if j == 0 or (j > 0 and (not valid[i, j-1] or not valid[i+1, j-1])):
                        # Wall faces toward negative j (up)
                        tris.append(Triangle(curr_top, curr_bot, right_top))
                        tris.append(Triangle(right_top, curr_bot, right_bot))
                    else:
                        # Wall faces toward positive j (down)
                        tris.append(Triangle(curr_top, right_top, curr_bot))
                        tris.append(Triangle(right_top, right_bot, curr_bot))

            # Down edge
            if j < y_size-1 and valid[i, j+1]:
                # Check if we need a wall between these cells
                need_wall = False
                if i == 0 or not valid[i-1, j] or not valid[i-1, j+1]:
                    need_wall = True
                elif i == x_size-1 or not valid[i+1, j] or not valid[i+1, j+1]:
                    need_wall = True

                if need_wall:
                    down_top = vert_idx[i, j+1]
                    down_bot = base_offset + down_top
                    # Create wall facing outward from invalid region
                    if i == 0 or (i > 0 and (not valid[i-1, j] or not valid[i-1, j+1])):
                        # Wall faces toward negative i (left)
                        tris.append(Triangle(curr_top, down_top, curr_bot))
                        tris.append(Triangle(down_top, down_bot, curr_bot))
                    else:
                        # Wall faces toward positive i (right)
                        tris.append(Triangle(curr_top, curr_bot, down_top))
                        tris.append(Triangle(down_top, curr_bot, down_bot))

    return Mesh(verts, tris)


def mesh_from_shape_file(shp_path: str, tif_paths: list[str], base_height: float = 1, scale: float = 1, compression_factor: float = 1) -> Mesh:
    """
    Generate a 3D terrain mesh from a shapefile and one or more raster tiles.

    The shapefile defines the polygon region to extract, and the raster tiles
    provide the elevation data. The resulting mesh includes a flat base at the
    specified base height and side walls around the polygon mask.

    Parameters
    ----------
    shp_path : str
        Path to the input shapefile (.geojson) containing the polygon boundary.
    tif_paths : list of str
        List of paths to GeoTIFF (.tif) raster files containing elevation data.
    base_height : float
        The base level of the mesh in mm. The lowest elevation in the
        polygon will be shifted so that its minimum is at this value.
    scale : float, optional
        Distance between adjacent vertices in model units. Default is 1.
    compression_factor : float, optional
        Factor to scale the number of vertices. For example, 0.5 halves the number
        of pixels in each dimension.

    Returns
    -------
    Mesh
        A Mesh object representing the extracted terrain.
    """

    group_rasters = yg.read_rasters(tif_paths)
    raw_polygon_layer = yg.read_shape_like(shp_path, group_rasters)
    polygon_layer = yo.where(raw_polygon_layer == 0, np.nan, raw_polygon_layer)

    mask_operation = polygon_layer * group_rasters
    masked_rasters = RasterLayer.empty_raster_layer_like(polygon_layer)
    mask_operation.save(masked_rasters)

    height_map = masked_rasters.read_array(
        masked_rasters.window.xoff,
        masked_rasters.window.yoff,
        masked_rasters.window.xsize,
        masked_rasters.window.ysize
    ).astype(float)

    HEIGHT_SCALE = 111_111 * np.mean(np.abs(group_rasters.pixel_scale))

    height_map /= HEIGHT_SCALE
    height_map += base_height - np.nanmin(height_map)
    compressed_height_map = compress(height_map, compression_factor)

    return create_mesh(compressed_height_map, scale)

def mesh_from_tif(tif_path: str, base_height: float = 1, scale: float = 1, compression_factor: float = 1) -> Mesh:
    raster = yg.read_raster(tif_path)

    height_map = raster.read_array(
        raster.window.xoff,
        raster.window.yoff,
        raster.window.xsize,
        raster.window.ysize
    ).astype(float)

    PIXEL_SCALE = 111_111 * np.mean(np.abs(raster.pixel_scale))
    height_map /= PIXEL_SCALE
    height_map += base_height - np.nanmin(height_map)

    compressed_height_map = compress(height_map, compression_factor)

    return create_mesh(compressed_height_map, scale)
