import math

class Core :

    def __init__(self, design) :

        self.design = design
        a = 1
        
    
    def __getattr__(self, name):

        return getattr(self.design, name)
    

    def create_winding(self, name="winding", **kwargs):

        
    

    def create_winding(self, name="Tx", **kwargs):
        """
        Creates a winding structure with configurable parameters.
        """
        # 기본 변수 설정
        center_length = kwargs.get("center_length", "50mm")
        center_width = kwargs.get("center_width", "40mm")
        min_lw = kwargs.get("min_lw", "5mm")
        layer_gap_Tx = kwargs.get("layer_gap_Tx", "2mm")
        N_Tx = kwargs.get("N_Tx", 3)
        coil_width = kwargs.get("coil_width", "Tx_width")
        coil_height = kwargs.get("coil_height", "Tx_height")
        
        # 초기 포인트 설정
        temp = [[f'{center_length}/2', f'{center_width}/(2+{math.sqrt(2)})', 0]]
        
        # Winding 생성
        for i in range(N_Tx):
            for j in range(8):
                if j == 0:
                    temp.append([f'{center_length}/2+{i}*{layer_gap_Tx}',
                                f'-{center_width}/(2+{math.sqrt(2)})-{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}', 0])
                elif j == 1:
                    temp.append([f'{center_length}/2-{min_lw}/(2+{math.sqrt(2)})+{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}',
                                f'-{center_width}/2-{i}*{layer_gap_Tx}', 0])
                elif j == 2:
                    temp.append([f'-{center_length}/2+{min_lw}/(2+{math.sqrt(2)})-{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}',
                                f'-{center_width}/2-{i}*{layer_gap_Tx}', 0])
                elif j == 3:
                    temp.append([f'-{center_length}/2-{i}*{layer_gap_Tx}',
                                f'-{center_width}/(2+{math.sqrt(2)})-{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}', 0])
                elif j == 4:
                    temp.append([f'-{center_length}/2-{i}*{layer_gap_Tx}',
                                f'{center_width}/(2+{math.sqrt(2)})+{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}', 0])
                elif j == 5:
                    temp.append([f'-{center_length}/2+{min_lw}/(2+{math.sqrt(2)})-{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}',
                                f'{center_width}/2+{i}*{layer_gap_Tx}', 0])
                elif j == 6:
                    temp.append([f'{center_length}/2-{min_lw}/(2+{math.sqrt(2)})+{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}+{layer_gap_Tx}*{math.sqrt(2)}',
                                f'{center_width}/2+{i}*{layer_gap_Tx}', 0])
                elif j == 7:
                    temp.append([f'{center_length}/2+{(i+1)}*{layer_gap_Tx}',
                                f'{center_width}/(2+{math.sqrt(2)})+{(i+1)}*{layer_gap_Tx}*{math.tan(math.pi/8)}', 0])

            if i == N_Tx - 1:
                temp.append([f'{center_length}/2+{(i+1)}*{layer_gap_Tx}',
                            f'{center_width}/(2+{math.sqrt(2)})+{(i+1)}*{layer_gap_Tx}*{math.tan(math.pi/8)}-0.2mm', 0])
        
        # 폴리라인 생성
        sorted_edges_Tx = self._create_polyline(points=temp, name=name, coil_width=coil_width, coil_height=coil_height)
        
        # winding 객체 색상 변경
        winding_obj = self.M3D.modeler.get_object_from_name(objname=name)
        winding_obj.color = (255, 0, 0)
        
        return winding_obj
