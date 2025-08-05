from .mesh import Mesh, Vertex, Triangle
from .mesh_generator import create_mesh, mesh_from_shape_file, mesh_from_tif
from .export import export_mesh_to_3mf
from .hm_utils import compress, get_bounding_box, get_area, get_shape, tiles_needed
from .file_reader import read_polygon

__version__ = "0.1.0"