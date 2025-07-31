from mesh_generator import create_square_mesh
from export import export_mesh_to_3mf
from hm_utils import get_shape, compress
from yirgacheffe.layers import TiledGroupLayer, RasterLayer

tiles = ["N27E086",  "N28E086", "N29E086"]
rasters = []
for tile in tiles:
    rasters.append(RasterLayer.layer_from_file(f'{tile}.tif'))
group_rasters = TiledGroupLayer(rasters)

width, height = get_shape(group_rasters)
x_min = 86.85
y_min = 27.95
x_max = 86.95
y_max = 28.05
corner_one = group_rasters.pixel_for_latlng(y_min, x_min)
corner_two = group_rasters.pixel_for_latlng(y_max, x_max)
everest = group_rasters.read_array(0, 0, width, height)
everest_mesh = create_square_mesh(compress(everest, 1000))

export_mesh_to_3mf(everest_mesh)