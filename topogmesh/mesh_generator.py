import numpy as np
from .hm_utils import compress, normalise, read_full_layer, apply_mask
from .geo_utils import raster_to_utm, shape_to_utm, shape_to_epsg27700
from .mesh import Mesh, Vertex, Triangle
from .webscraper import mask_from_osm_tags
import yirgacheffe as yg
import yirgacheffe.operators as yo


def create_mesh(height_map: np.ndarray, scale: float = 1, base_map: np.ndarray | None = None) -> Mesh:
    """
    Generate a 3D mesh from a 2D height map.

    Parameters
    ----------
    height_map : np.ndarray
        2D array of height values. Use `np.nan` to mark areas outside the model.
    base_map : np.ndarray optional
        2D array of the height of the base of the mesh. Default is np.zeros.
    scale : float, optional
        Distance between adjacent vertices in model units. Default is 1.

    Returns
    -------
    Mesh
        A mesh object containing vertices and triangles representing the terrain,
        including a base and side walls.
    """
    if base_map is None:
        base_map = np.zeros_like(height_map)

    valid = ~np.isnan(height_map)
    x_size, y_size = height_map.shape

    vert_idx = np.full((x_size, y_size), -1, dtype=int)
    verts = []
    # surface vertices
    for i in range(x_size):
        for j in range(y_size):
            if valid[i, j]:
                vert_idx[i, j] = len(verts)
                verts.append(Vertex(i * scale, j * scale, height_map[i, j]))

    base_offset = len(verts)
    # base vertices
    for i in range(x_size):
        for j in range(y_size):
            if valid[i, j]:
                verts.append(Vertex(i * scale, j * scale, base_map[i, j]))


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


def mesh_from_shape_file(shp_path: str, 
                         tif_paths: list[str], 
                         max_height: float, 
                         max_length: float, 
                         base_height: float = 1, 
                         compression_factor: float = 1) -> Mesh:
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
    utm_rasters = raster_to_utm(group_rasters)

    polygon_layer = shape_to_utm(utm_rasters, shp_path)
    masked_rasters = apply_mask(utm_rasters, polygon_layer)

    height_map = read_full_layer(masked_rasters)

    normalised_height_map = normalise(height_map, base_height, max_height)
    compressed_height_map = compress(normalised_height_map, compression_factor)
    
    scale = max_length / max(compressed_height_map.shape)

    return create_mesh(compressed_height_map, scale)


def mesh_from_uk_shape(shp_path: str, 
                       fr_dsm_paths: list[str], 
                       dtm_paths: list[str],
                       max_length: float,
                       osm_tags: list[dict],
                       base_height: float = 1) -> list[Mesh]:
    """
    Generate a composite 3D mesh from UK terrain and OSM data.

    Uses a Digital Terrain Model (DTM) as the base and adds layers based
    on OpenStreetMap (OSM) tags to create detailed meshes representing
    terrain and mapped features.

    Parameters
    ----------
    shp_path : str
        Path to the polygon shapefile defining the area of interest.
    fr_dsm_paths : list[str]
        Paths to the DSM (Digital Surface Model) raster files.
    dtm_paths : list[str]
        Paths to the DTM (Digital Terrain Model) raster files.
    max_length : float
        Maximum length (in units) to scale the mesh to.
    osm_tags : list[dict]
        List of OSM tag dictionaries to extract feature layers (e.g., buildings, vegetation).
    base_height : float, optional
        Baseline height to offset the terrain minimum. Defaults to 1.

    Returns
    -------
    list[Mesh]
        A list of Mesh objects representing the base terrain and additional
        layers corresponding to OSM features.

    Notes
    -----
    - The DTM is normalized and scaled so that its largest dimension fits
      within `max_length`.
    - Each OSM tag layer is applied on top of the base terrain, masking
      areas not matching the tag.
    - NaN values in input rasters are treated as zero.
    """
    dsm_layer = yg.read_rasters(fr_dsm_paths)
    dtm_layer = yg.read_rasters(dtm_paths)
    polygon_layer = shape_to_epsg27700(dsm_layer, shp_path)

    # Remove NODATA holes
    dsm_layer = yo.where(dsm_layer.isnan(), 0, dsm_layer)
    dtm_layer = yo.where(dtm_layer.isnan(), 0, dtm_layer)

    #Ensure dsm_layer is above dtm
    LAMINAR_HEIGHT = 1
    dsm_layer = yo.where(dsm_layer < dtm_layer + LAMINAR_HEIGHT, dtm_layer + LAMINAR_HEIGHT, dsm_layer)

    masked_dsm = apply_mask(dsm_layer, polygon_layer)
    masked_dtm = apply_mask(dtm_layer, polygon_layer)

    dtm = read_full_layer(masked_dtm)

    Z_OFF = base_height - np.nanmin(dtm)
    SCALE = max_length / max(dtm.shape)

    normalised_dtm = (dtm + Z_OFF) * SCALE

    composite_mesh = [create_mesh(normalised_dtm, scale=SCALE)]

    unassigned_layer_mask = np.ones(dtm.shape, dtype=float)
    for tags in osm_tags:
        mask = mask_from_osm_tags(masked_dsm, tags)
        if mask is not None:
            next_layer = apply_mask(masked_dsm, mask)
            next_layer.set_window_for_union(masked_dtm.area)

            # Change once yirgacheffe pads with no data instead of 0
            next_layer = yo.where(next_layer == 0, np.nan, next_layer)
            next_layer = apply_mask(next_layer, polygon_layer)

            height_map = read_full_layer(next_layer)

            filtered_height_map = height_map * unassigned_layer_mask
            unassigned_layer_mask = np.where(np.isnan(height_map), unassigned_layer_mask, np.nan)

            normalised_height_map = (filtered_height_map + Z_OFF) * SCALE
            composite_mesh.append(create_mesh(normalised_height_map, base_map=normalised_dtm, scale=SCALE))

    return composite_mesh


def mesh_from_tif(tif_path: str, max_height: float, max_length: float, base_height: float = 1, compression_factor: float = 1) -> Mesh:
    raster = yg.read_raster(tif_path)

    height_map = read_full_layer(raster)

    normalised_height_map = normalise(height_map, base_height, max_height)
    compressed_height_map = compress(normalised_height_map, compression_factor)

    scale = max_length / max(compressed_height_map.shape)

    return create_mesh(compressed_height_map, scale)
