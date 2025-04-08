import math

class Face:

    def __init__(self, design) :
        self.design = design
    
    def __getattr__(self, name):
        return getattr(self.design, name)
    

    def get_minmax_face(self, faces, axis="x", min_max="min") :
        """
        주어진 면들 중에서 특정 축에 대해 최소 또는 최대 값을 가진 면들을 반환합니다.
        
        Parameters:
            faces (list): 면 객체들의 리스트
            axis (str): 기준 축 ("x", "y", "z")
            min_max (str): 최소 또는 최대 값 선택 ("min" 또는 "max")
            
        Returns:
            list: 선택된 면들의 리스트
        """
        if axis.lower() not in ["x", "y", "z"]:
            raise ValueError("axis must be 'x', 'y', or 'z'")

        if axis.lower() == "x":
            axis_num = 0
        elif axis.lower() == "y":
            axis_num = 1
        elif axis.lower() == "z":
            axis_num = 2

        if min_max == "min":
            value = min(face.center[axis_num] for face in faces)
        elif min_max == "max":
            value = max(face.center[axis_num] for face in faces)
        else:
            raise ValueError("min_max must be 'min' or 'max'")

        target_faces = [face for face in faces if math.isclose(face.center[axis_num], value, rel_tol=1e-6)]

        return target_faces


    def sort_face(self, faces, axis="x", ascending=True):
        """
        주어진 면들을 특정 축을 기준으로 정렬합니다.
        
        Parameters:
            faces (list): 면 객체들의 리스트
            axis (str): 기준 축 ("x", "y", "z")
            ascending (bool): 오름차순 정렬 여부
            
        Returns:
            list: 정렬된 면들의 리스트
        """
        if axis.lower() not in ["x", "y", "z"]:
            raise ValueError("axis must be 'x', 'y', or 'z'")

        if axis.lower() == "x":
            axis_num = 0
        elif axis.lower() == "y":
            axis_num = 1
        elif axis.lower() == "z":
            axis_num = 2

        sorted_faces = sorted(faces, key=lambda face: face.center[axis_num], reverse=not ascending)
        return sorted_faces
