import argparse
import topogmesh
import json

def main():
    """
    Command line interface for TopogMesh.

    Provides three subcommands to generate 3D meshes:
    
    1. mesh_from_tif:
        Generate a mesh from a single TIF file.
    2. mesh_from_shape_file:
        Generate a mesh from a shapefile and one or more TIF files.
    3. mesh_from_uk_shape_file:
        Generate a mesh from a shapefile and multiple DSM/DTM TIFs,
        adding layers based on OSM tags.
    4. download_tiles_for_uk_shape:
        Scrapes the dsm and dtm tiles off https://environment.data.gov.uk/survey
        which are required to cover the provided geojson file.
    """
    parser = argparse.ArgumentParser(prog="topogmesh", description="Generate 3MF terrain meshes")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: mesh_from_tif
    tif_parser = subparsers.add_parser("mesh_from_tif", help="Generate mesh from a single TIF")
    tif_parser.add_argument("--tif", required=True, help="Path to .tif file")
    tif_parser.add_argument("--output", required=True, help="Output .3mf file path")
    tif_parser.add_argument("--max-length", required=True, type=float)
    tif_parser.add_argument("--max-height", required=True, type=float)
    tif_parser.add_argument("--base-height", type=float, default=1)
    tif_parser.add_argument("--compression-factor", type=float, default=1)

    # Command: mesh_from_shape_file
    shape_parser = subparsers.add_parser("mesh_from_shape_file", help="Generate mesh from a geojson file and multiple TIFs")
    shape_parser.add_argument("--shape", required=True, help="Path to shape file (.geojson)")
    shape_parser.add_argument("--tifs", required=True, nargs='+', help="List of .tif files")
    shape_parser.add_argument("--output", required=True, help="Output .3mf file path")
    shape_parser.add_argument("--max-length", required=True, type=float)
    shape_parser.add_argument("--max-height", required=True, type=float)
    shape_parser.add_argument("--base-height", type=float, default=1)
    shape_parser.add_argument("--compression-factor", type=float, default=1)

    # Command: mesh_from_uk_shape
    uk_shape_parser = subparsers.add_parser(
        "mesh_from_uk_shape_file", 
        help="Generate mesh from a shapefile and multiple DSM/DTM TIFs"
    )
    uk_shape_parser.add_argument("--shape", required=True, help="Path to polygon shapefile (.geojson or .shp)")
    uk_shape_parser.add_argument("--dsms", required=True, nargs='+', help="List of DSM .tif files")
    uk_shape_parser.add_argument("--dtms", required=True, nargs='+', help="List of DTM .tif files")
    uk_shape_parser.add_argument("--output", required=True, help="Output .3mf file path")
    uk_shape_parser.add_argument("--max-length", required=True, type=float)
    uk_shape_parser.add_argument("--base-height", type=float, default=1)
    uk_shape_parser.add_argument("--osm-tags", required=True, nargs='+', help="List of OSM tag dictionaries in JSON format")

    # Command: download_tiles_for_uk_shape
    download_tiles_parser = subparsers.add_parser(
        "download_tiles_for_uk_shape", 
        help="Scrapes the dsm and dtm tiles off https://environment.data.gov.uk/survey for a given geojson file."
    )
    download_tiles_parser.add_argument("--geojson", required=True, help="Path to the input GeoJSON file defining the area of interest.")
    download_tiles_parser.add_argument("--output-dir", required=True, help="Directory where downloaded tiles will be saved.")

    args = parser.parse_args()

    if args.command == "mesh_from_tif":
        mesh = topogmesh.mesh_from_tif(
            tif_path=args.tif,
            base_height=args.base_height,
            max_length=args.max_length,
            max_height=args.max_height,
            compression_factor=args.compression_factor
        )
        topogmesh.export_mesh_to_3mf(mesh, args.output)
        print(f"Mesh saved to {args.output}")

    elif args.command == "mesh_from_shape_file":
        mesh = topogmesh.mesh_from_shape_file(
            shp_path=args.shape,
            tif_paths=args.tifs,
            max_length=args.max_length,
            max_height=args.max_height,
            base_height=args.base_height,
            compression_factor=args.compression_factor
        )
        topogmesh.export_mesh_to_3mf(mesh, args.output)
        print(f"Mesh saved to {args.output}")

    elif args.command == "mesh_from_uk_shape_file":
        osm_tags = [json.loads(tag) for tag in args.osm_tags]
        meshes = topogmesh.mesh_from_uk_shape(
            shp_path=args.shape,
            fr_dsm_paths=args.dsms,
            dtm_paths=args.dtms,
            max_length=args.max_length,
            osm_tags=osm_tags,
            base_height=args.base_height
        )
        topogmesh.export_mesh_to_3mf(meshes, args.output)
        print(f"Mesh saved to {args.output}")

    elif  args.command == "download_tiles_for_uk_shape":
        topogmesh.get_uk_tiles(
            args.geojson, 
            args.output_dir
        )


if __name__ == "__main__":
    main()
