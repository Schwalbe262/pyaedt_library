from ansys.aedt.core import Hfss as AEDTHfss

class HFSS(AEDTHfss) :

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)