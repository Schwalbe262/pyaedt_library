from ansys.aedt.core import Hfss as AEDTHfss

class HFSS(AEDTHfss) :

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)

        self.design = None


    def assign_terminal(self, name="terminal", edges=None, resistance=50) :
        """
        터미널을 할당합니다.
        
        Parameters:
            name (str): 터미널의 이름
            edges (list): 터미널을 할당할 엣지들의 ID 리스트
            resistance (float): 터미널의 저항값 (옴)
        """
        designs = self.design.project.SetActiveDesign(self.design.name)
        oModule = designs.GetModule("BoundarySetup")

        oModule.AssignTerminal(
            [
                f"NAME:{name}",
                "Edges:="		, edges,
                "ParentBndID:="		, "1",
                "TerminalResistance:="	, f"{resistance}ohm"
            ])
        

    def get_report_data(self, setup="Setup1") :
        """
        시뮬레이션 리포트 데이터를 가져옵니다.
        
        Parameters:
            setup (str): 시뮬레이션 설정 이름
            
        Returns:
            tuple: (패스 번호, 테트라헤드라 수, 델타 S 값)
        """
        report = self.design.export_convergence(setup=setup, variations="", output_file=None)
    
        with open(report, 'r') as file:
            lines = file.readlines()

        # 공백이 아닌 마지막 줄을 찾기
        for line in reversed(lines):
            if line.strip():  # 줄이 공백이 아닐 경우
                last_data_line = line
                break

        parts = last_data_line.split('|')
        pass_number = parts[0].strip()
        tetrahedra = parts[1].strip()
        delta_S = parts[2].strip()

        return pass_number, tetrahedra, delta_S
