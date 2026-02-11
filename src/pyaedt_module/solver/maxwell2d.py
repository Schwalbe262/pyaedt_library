from ansys.aedt.core import Maxwell2d as AEDTMaxwell2d
import pandas as pd
import numpy as np
import time
import re
import os


class Maxwell2d(AEDTMaxwell2d) :

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)

        self.design = None
        self.report_list = {}


