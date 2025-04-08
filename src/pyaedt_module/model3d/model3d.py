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
        """
        주어진 객체들을 하나로 합칩니다.
        
        Parameters:
            assignment (list): 합칠 객체들의 이름 리스트
            
        Returns:
            obj: 합쳐진 객체
        """
        name = self.design.modeler.unite(assignment=assignment)
        obj = self.design.modeler.get_object_from_name(name)

        return obj