class Triangle:
    """
    Represents a triangle in a mesh by storing the indices of its vertices.

    Attributes
    ----------
    v1 : int
        Index of the first vertex.
    v2 : int
        Index of the second vertex.
    v3 : int
        Index of the third vertex.
    """
    def __init__(self, v1: int, v2: int, v3: int):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    def __repr__(self):
        return f"Triangle(v1: {self.v1}, v2: {self.v2}, v3: {self.v3})"
    

class Vertex:
    """
    Represents a 3D point or vertex with x, y, z coordinates.

    Attributes
    ----------
    x : float
        The x-coordinate of the vertex.
    y : float
        The y-coordinate of the vertex.
    z : float
        The z-coordinate of the vertex.
    """
    def __init__(self, x: float, y: float, z :float):
        self.x = x
        self.y = y
        self.z = z
    
    def __repr__(self):
        return f"Vertex(v1: {self.x}, v2: {self.y}, v3: {self.z})"
    
    def scale(self, factor: float):
        """
        Scale the vertex coordinates by a given factor.

        Parameters
        ----------
        factor : float
            The scaling factor to multiply each coordinate by.
        """
        self.x *= factor
        self.y *= factor
        self.z *= factor
    
class Mesh:
    """
    Represents a 3D mesh composed of vertices and triangles with spatial dimensions.

    Attributes
    ----------
    _vertices : list of Vertex
        Internal list of vertices defining the mesh geometry.
    _triangles : list of Triangle
        Internal list of triangles referencing vertex indices to form mesh faces.
    _dimensions : tuple of float
        The (width, height) dimensions of the mesh in model units.

    Properties
    ----------
    vertices : list of Vertex
        Read-only property to access the list of vertices.
    triangles : list of Triangle
        Read-only property to access the list of triangles.

    Methods
    -------
    scale_height(factor: float)
        Scale the height (z-coordinate) of all vertices by the given factor.
    scale(factor: float)
        Scale all vertex coordinates and update mesh dimensions by the factor.
    """
    def __init__(self, vertices: list[Vertex], triangles: list[Triangle], dimensions):
        self._vertices = vertices
        self._triangles = triangles
        self._dimensions = dimensions

    def __repr__(self):
        return f"Mesh(Vertices: {self._vertices}, Triangles: {self._triangles}, Dimensions: {self._dimensions})"
    
    def scale_height(self, factor: float):
        for vertex in self._vertices:
            vertex.z *= factor

    def scale(self, factor: float):
        for vertex in self._vertices:
            vertex.scale(factor)
        width, height = self._dimensions
        self._dimensions = (width * factor, height * factor)

    @property
    def vertices(self):
        return self._vertices
    
    @property
    def triangles(self):
        return self._triangles