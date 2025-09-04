# Topogmesh: 3D printing the planet

## Overview
Topogmesh generates `.3mf` files suitable for 3D printing from terrain `.tif` files. It can also use `.geojson` files to define custom areas of terrain to include in the model. It also supports generating detailed meshes for cities based off LIDAR data and uses OSM data to add seperate layers to the model.

## Installation
Topogmesh is available on PyPI and can be installed with pip:
```bash
pip install topogmesh
```

## How to use

### Creating a mesh for single Raster

To create a rectangular 3D-printable model from a TIF file, use `topogmesh.mesh_from_tif`. 

You need to provide:

- `tif_path`: The path to the raster you want to print.
- `max_length`: The maximum horizontal size of the model in millimetres (the longest side of the rectangle).
- `max_height`: The total height of the 3D model in millimetres. The tallest point of the raster will be scaled to this height, and all other points are scaled proportionally.

Optional Parameters:

- `base_height`: This controls the gap between base of the model and the lowest point of the raster. If not specified, base_height defaults to 1 mm.

```python
import topogmesh

london_mesh = topogmesh.mesh_from_tif(
    tif_path='london.tif',
    max_length=100,
    max_height=30,
    base_height=5,
)

topogmesh.export_mesh_to_3mf(london_mesh, 'london.3mf')
```

This can also be done using the command line with the following equivalent command.
```bash
topogmesh mesh_from_tif \
--tif london.tif \
--output london.3mf \
--max-length 100 \
--max-height 30 \
--base-height 5
```

### Custom Shaped Models

This function allows you to create models with custom shapes and select a specific region from a group of rasters. It also supports the use of OSM tags to seperate the model into different layers.

You need to provide:

- `shp_path`: The path to the geojson file
- `tif_paths`: The paths to the relevant raster data (make sure you have the right data to cover the entire shape file)
- `max_length`: The maximum horizontal size of the model in millimetres (the longest side of the rectangle).
- `max_height`: The total height of the 3D model in millimetres. The tallest point of the raster will be scaled to this height, and all other points are scaled proportionally.

Optional Parameters:

- `base_height`: This controls the gap between base of the model and the lowest point of the raster. If not specified, base_height defaults to 1 mm.
- `osm_tags`: A list of OpenStreetMap tag dictionaries (in JSON format) used to overlay features such as rivers, roads, or buildings on the mesh. NOTE, if a feature contains two or more of the tags provided it will default to being part of the first layer which it contains the tag for.

```python
import topogmesh

everest_mesh = topogmesh.mesh_from_shape_file(
    shp_path='everest.geojson',
    tif_paths=['N27E086.tif', 'N28E086.tif', 'N29E086.tif'],
    max_length=200,
    max_height=60,
    base_height=5,
    osm_tags=[{'natural': 'water'}]
)

topogmesh.export_mesh_to_3mf(everest_mesh, 'everest.3mf')
```

Alternatively, you can use the command line.

```bash
topogmesh mesh_from_shape_file \
--shape everest.geojson \
--tifs N27E086.tif N28E086.tif N29E086.tif \
--output everest.3mf \
--base-height 3 \
--max-length 200 \
--max-height 60 \
--osm-tags '{"natural": "water"}'
```

### Creating a mesh from a shapefile and LIDAR data

To generate a 3D-printable model from a polygon shapefile (e.g. a boundary) and corresponding DSM/DTM TIF tiles, use `topogmesh.mesh_from_uk_shape_file`. This function creates a model for the underlying terrain using the DTM data provided, and then uses the DSM files to add different layers based on OSM data. For example using the tag '{'building' : 'yes'}' will add a component to the model which contains models for all the buildings within the chosen area. This is useful if you want to pick out individual features to include or if you want to change the colour of a specific feature to make it stand out. To find out which tags you need for the features you want, visit the [OSM website](https://www.openstreetmap.org).

You need to provide:

- `shape`: Path to a polygon shapefile (either `.geojson` or `.shp`) defining the region of interest.  
- `dsms`: A list of Digital Surface Model (DSM) `.tif` files covering the region.  
- `dtms`: A list of Digital Terrain Model (DTM) `.tif` files covering the region.  
- `output`: Path where the generated `.3mf` file should be saved.  
- `max_length`: The maximum horizontal size of the model in millimetres (the longest side of the bounding box).  

Optional parameters:

- `base_height`: Adds a gap between the print bed and the lowest point of the terrain (default: 1 mm).  
- `osm_tags`: A list of OpenStreetMap tag dictionaries (in JSON format) used to overlay features such as rivers, roads, or buildings on the mesh. NOTE, if a feature contains two or more of the tags provided it will default to being part of the first layer which it contains the tag for.

```python
import topogmesh

uk_mesh = topogmesh.mesh_from_uk_shape_file(
    shape="buckingham_palace.geojson",
    dsms=["dsm_tile1.tif", "dsm_tile2.tif"],
    dtms=["dtm_tile1.tif", "dtm_tile2.tif"],
    output="palace.3mf",
    max_length=200,
    base_height=2,
    osm_tags=[{"building": ["yes", "palace"]}, {"natural": "water"}],
)
```

The equivalent command is:

```bash
topogmesh mesh_from_uk_shape_file \
--shape buckingham_palace.geojson \
--dsms dsm_TQ2575 dsm_TQ2580 \
--dtms dtm_TQ2575 dtm_TQ2580 \
--output palace.3mf \
--max-length 200 \
--base-height 2 \
--osm-tags '{"building": ["yes", "palace"]}' '{"natural": "water"}'
```

### Downloading UK LIDAR data
To get the right DTM's and DSM's for a particular region of the uk, you can either download them manually from the [UK Government Website](https://environment.data.gov.uk/survey), or use the topogmesh command which automatically downloads the tiles needed for a given geojson file.

You need to provide:
- `geojson`: The path to the geojson file you want the tiles for.
- `output_dir`: The destination folder you want the LIDAR tiles to be saved to.

```bash
topogmesh download_tiles_for_uk_shape \
--geojson clare_college.geojson
--output-dir lidar_data
```

## Thanks
Thank you to Dr Michael Winston Dales for supervising this project; providing very useful insights and creating [Yirgacheffe](https://github.com/quantifyearth/yirgacheffe) which is integral to this library working. 
Also thank you to Professor Anil Madhavapeddy for overseeing this UROP and giving me this opportunity.