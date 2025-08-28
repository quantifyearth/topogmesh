from .mesh import Mesh, Vertex, Triangle
from .mesh_generator import create_mesh, mesh_from_shape_file, mesh_from_tif, mesh_from_uk_shape
from .export import export_mesh_to_3mf
from .webscraper import get_uk_tiles

__version__ = "0.1.5"
