from .core import Core
from .winding import Winding
from .face import Face

class Model3d :

    def __init__(self, design) :
        self.core = Core(design)
        self.winding = Winding(design)
        self.face = Face(design)

        self.design = design


    def unite(self, assignment) :

        name = self.design.modeler.unite(assignment=assignment)
        object = self.design.modeler.get_object_from_name(name)

        return object