from .core import Core
from .winding import Winding

class Model3d :

    def __init__(self, design) :
        self.core = Core(design)
        self.winding = Winding(design)