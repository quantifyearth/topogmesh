import lib3mf
from lib3mf import get_wrapper
from .mesh import Mesh

def export_mesh_to_3mf(mesh: list[Mesh] | Mesh, output_path: str) -> None:
    """
    Export a Mesh or list of Mesh objects to a 3MF file.

    Creates a 3MF model using lib3mf, adds the mesh vertices and triangles,
    and writes the file to disk.

    Parameters
    ----------
    mesh : list[Mesh] | Mesh
        The mesh or meshes to export.
    output_path : str
        Path to the output .3mf file.

    Returns
    -------
    None
    """

    if isinstance(mesh, Mesh):
        meshes = [mesh]
    else:
        meshes = mesh

    wrapper = get_wrapper()
    model = wrapper.CreateModel()

    comp_obj = model.AddComponentsObject()
    comp_obj.SetName("CompositeObject")

    for i, mesh in enumerate(meshes):
        mesh_obj = model.AddMeshObject()
        mesh_obj.SetName(f"MeshModel_{i}")

        for vert in mesh.vertices:
            pos = lib3mf.Position()
            pos.Coordinates[:] = vert.x, vert.y, vert.z
            mesh_obj.AddVertex(pos)

        for tri in mesh.triangles:
            t = lib3mf.Triangle()
            t.Indices[:] = tri.v1, tri.v2, tri.v3
            mesh_obj.AddTriangle(t)

        comp_obj.AddComponent(mesh_obj, wrapper.GetIdentityTransform())

    model.AddBuildItem(comp_obj, wrapper.GetIdentityTransform())

    writer = model.QueryWriter("3mf")
    writer.WriteToFile(output_path)
