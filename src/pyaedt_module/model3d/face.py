import math

class Face:

    def __init__(self, design) :

        self.design = design
        a = 1
        
    
    def __getattr__(self, name):

        return getattr(self.design, name)
    

    def get_minmax_face(self, faces, axis="x", min_max="min") :
        
        # faces : face array

        if axis.lower() == "x" :
            axis_num = 0
        elif axis.lower() == "y" :
            axis_num = 1
        elif axis.lower() == "z" :
            axis_num = 2

        if min_max == "min" :
            value = min(face.center[axis_num] for face in faces)
        elif min_max == "max" :
            value = max(face.center[axis_num] for face in faces)

        target_faces = [face for face in faces if math.isclose(face.center[axis_num], value, rel_tol=1e-6)]

        return target_faces


    def sort_face(self, faces, axis="x", ascending="True"):
        # ascending이 문자열로 들어올 경우 boolean으로 변환
        if isinstance(ascending, str):
            ascending = ascending.lower() == "true"

        # 정렬 기준 축 지정
        if axis.lower() == "x":
            axis_num = 0
        elif axis.lower() == "y":
            axis_num = 1
        elif axis.lower() == "z":
            axis_num = 2
        else:
            raise ValueError("axis must be 'x', 'y', or 'z'")

        # face.center의 해당 축 값을 기준으로 정렬 (reverse는 오름차순일 경우 False, 내림차순일 경우 True)
        sorted_faces = sorted(faces, key=lambda face: face.center[axis_num], reverse=not ascending)
        return sorted_faces
