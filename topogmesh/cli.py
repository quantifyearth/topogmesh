import argparse
import topogmesh

def main():
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

if __name__ == "__main__":
    main()
