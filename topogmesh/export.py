import lib3mf
from lib3mf import get_wrapper
from .mesh import Mesh

def export_mesh_to_3mf(mesh: Mesh, output_path: str) -> None:
    """
    Export a Mesh object to a 3MF file.

    Creates a 3MF model using lib3mf, adds the mesh vertices and triangles,
    and writes the file to disk.

    Parameters
    ----------
    mesh : Mesh
        The mesh to export.
    output_path : str
        Path to the output .3mf file.

    Returns
    -------
    None
    """
    wrapper = get_wrapper()
    model = wrapper.CreateModel()
    mesh_obj = model.AddMeshObject()
    mesh_obj.SetName("MeshModel")

    # Add vertices
    for vert in mesh.vertices:
        pos = lib3mf.Position()
        pos.Coordinates[0], pos.Coordinates[1], pos.Coordinates[2] = vert.x, vert.y, vert.z
        mesh_obj.AddVertex(pos)

    # Add triangles
    for tri in mesh.triangles:
        t = lib3mf.Triangle()
        t.Indices[0], t.Indices[1], t.Indices[2] = (tri.v1, tri.v2, tri.v3)
        mesh_obj.AddTriangle(t)

    # Create build item
    model.AddBuildItem(mesh_obj, wrapper.GetIdentityTransform())

    # Write to file
    writer = model.QueryWriter("3mf")
    writer.WriteToFile(output_path)
    print("file saved")