from ansys.aedt.core import Circuit as AEDTCircuit

class Circuit(AEDTCircuit) :

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)

        self.design = None

