import pyaedt
from pyaedt import Desktop
import os
import shutil

from pyaedt import Maxwell3d

class Variable :

    def __init__(self, design, desktop):
        self.design = design
        self.desktop = desktop
        self.var = {}



    def set_variable(self, variables) :
        
        for name, value in variables :
            
            self.design[name] = value
            self.var[name] = value

    def _get_params_list(self):
        # format

        # [
        # 		"NAME:Params",
        # 		"coil_width:="		, "5mm",
        # 		"core_h1:="		, "50mm",
        # 		"core_l1_leg:="		, "15mm",
        # 		"core_l1_top:="		, "20mm",
        # 		"core_l2:="		, "50mm",
        # 		"core_w1:="		, "100mm",
        # 		"space_x:="		, "5mm",
        # 		"space_y:="		, "5mm",
        # 		"space_z:="		, "1mm"
        # ],

        params_list = [
            "NAME:Params"
        ]

        for name, value in self.var.items():
            params_list.append(f"{name}:=")
            params_list.append(f"{value}")

        return params_list
    

    def zero_temp(self) :

        oProject = self.desktop.odesktop.SetActiveProject(self.desktop.project_list()[0])
        oDesign = oProject.SetActiveDesign(self.design.design_name)

        oDesign.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:Icepak",
                    [
                        "NAME:PropServers", 
                        "Design Settings"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:Ambients/Temperature",
                            "Value:="		, "0cel"
                        ]
                    ]
                ]
            ])
        oDesign.ChangeProperty(
            [
                "NAME:AllTabs",
                [
                    "NAME:Icepak",
                    [
                        "NAME:PropServers", 
                        "Design Settings"
                    ],
                    [
                        "NAME:ChangedProps",
                        [
                            "NAME:Ambients/Rad. Temperature",
                            "Value:="		, "0cel"
                        ]
                    ]
                ]
            ])


