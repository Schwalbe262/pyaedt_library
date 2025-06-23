from .core import Core
from .winding import Winding
from .transformer_winding import Transformer_winding
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
    

    def find_object(self, obj_list) :

        """
        
        다른 design에 있는 model객체 불러오기
        
        """

        """
        example :
        i_cold_plate_top = self.icepak_design.model3d.find_object(self.maxwell_design.cold_plate_top)

        """

        is_list_input = isinstance(obj_list, list)
        processing_list = obj_list if is_list_input else [obj_list]

        new_obj_list = []

        for obj in processing_list :

            obj_name = obj if isinstance(obj, str) else obj.name # convert object to name
            new_obj = self.design.modeler.get_object_from_name(obj_name) # get object from name
            if new_obj:
                new_obj_list.append(new_obj)

        if not is_list_input:
            return new_obj_list[0] if new_obj_list else None

        return new_obj_list