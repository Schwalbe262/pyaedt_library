from ansys.aedt.core import Hfss as AEDTHfss

class HFSS(AEDTHfss) :

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)

        self.design = None


    def assign_terminal(self, name="terminal", edges=None, resistance=50) :

        # edges : list (edge.id)

        designs = self.design.project.SetActiveDesign(self.design.name)
        oModule = designs.GetModule("BoundarySetup")

        oModule.AssignTerminal(
            [
                f"NAME:{name}",
                "Edges:="		, edges,
                "ParentBndID:="		, "1",
                "TerminalResistance:="	, f"{resistance}ohm"
            ])
        
