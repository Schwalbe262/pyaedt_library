from ansys.aedt.core import Icepak as AEDTIcepak
import pandas as pd

from ._reports import export_report_to_dataframe, select_report_columns

class Icepak(AEDTIcepak) :

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)
    

    def get_calculator_parameter(self, dir=None, parameters=[], mod="write", import_report=None, report_name="thermal_report", file_name="thermal_report") :
        """
        example :
        parameters2 = []
        parameters2.append([winding1, "P_LV", "EMLoss"])
        # ... (rest of example)
        """
        name_list = []
        result_expressions = []
        report = None

        
        if mod == "write" :
            result_expressions, name_list = self._add_calculator_expression(parameters=parameters)
            report = self._create_report(report_name = report_name, result_expressions = result_expressions, category = "Fields")
            if not hasattr(self, "report_list"):
                self.report_list = {}
            self.report_list[report_name] = report
        elif mod == "read" :
            if not hasattr(self, "report_list"):
                self.report_list = {}
            report = import_report or self.report_list.get(report_name)
            # In "read" mode, reconstruct the expression and name lists for column mapping
            for obj, name, expression_type in parameters:
                name_list.append(name)
                obj_name = obj.name if hasattr(obj, 'name') else obj
                
                if expression_type == "Temp_max":
                    expr_name = f"Temp_max_{obj_name}"
                elif expression_type == "Temp_mean":
                    expr_name = f"Temp_mean_{obj_name}"
                elif expression_type == "B_mean":
                    expr_name = f"B_mean_{obj_name}"
                else: 
                    expr_name = f"P_{obj_name}"
                result_expressions.append(expr_name)
        
        if not report:
             return None, pd.DataFrame(columns=[p[1] for p in parameters])

        data = export_report_to_dataframe(self, dir, report_name, file_name)
        output_df = select_report_columns(data, result_expressions, name_list, add_missing=True)

        #output_df.to_csv("icepak_calculator.csv")
        
        return report, output_df


    def _create_report(self, report_name = "report", result_expressions=[], category=None) :
        return self.post.create_report(
            expressions=result_expressions, setup_sweep_name=None, domain='Sweep', 
            variations=None, primary_sweep_variable=None, secondary_sweep_variable=None, 
            report_category=category, plot_type='Data Table', context=None, 
            subdesign_id=None, polyline_points=1001, plot_name=report_name
        )

    def _add_calculator_expression(self, parameters) :
        result_expressions = []
        name_list = []
        for obj, name, expression in parameters:
            # Icepak can only calculate thermal quantities.
            if expression == "Temp_max" :
                result_expressions.append(self._get_temp(obj=obj, mod="max"))
            elif expression == "Temp_mean" :
                result_expressions.append(self._get_temp(obj=obj, mod="mean"))
            # Silently ignore other expression types like B_mean for Icepak.
            
            # We still add the name to the list to maintain column structure,
            # it will be filled with NaN later if no result is found.
            name_list.append(name)
        return result_expressions, name_list



    def _get_temp(self, obj, mod) :

        assignment = obj.name
        name = None

        oModule = self.ofieldsreporter
        oModule.CalcStack("clear")
        oModule.EnterQty("Temp")

        assignment = obj if isinstance(obj, str) else obj.name
        oModule.EnterVol(assignment) if obj.is3d else oModule.EnterSurf(assignment)

        if mod == "max" : 
            oModule.CalcOp("Maximum")
            name = "Temp_max_{}".format(assignment)  # Need to check for uniqueness !

        elif mod == "mean" : 
            oModule.CalcOp("Mean")
            name = "Temp_mean_{}".format(assignment)  # Need to check for uniqueness !

        if name != None : 
            oModule.AddNamedExpression(name, "Fields")
            return name
        
        return False


    # EM loss excitation for icepak
    def assign_EM_loss(self, name="EMLoss", objects=None, design=None, frequency=None, loss_mul=1, **kwargs) :

        oProject = self.odesktop.SetActiveProject(self.project_name)
        oDesign = oProject.SetActiveDesign(self.design_name)
        oModule = oDesign.GetModule("BoundarySetup")

        object_name = [item.name for item in objects]
        setup_name = kwargs.get("setup_name", self.get_setups()[0])
        
        # We need the variable list from the pyDesign object, which is 'design' here.
        # params = design.variable._get_params_list()

        oModule.AssignEMLoss(
            [
                f'NAME:{name}',
                "Objects:=", object_name,
                "Project:=", "This Project*",
                "Product:=", "ElectronicsDesktop",
                "Design:=", f'{design.design_name}',
                "Soln:=", f"{setup_name} : LastAdaptive",
                "ForceSourceToSolve:=", False,
                "PreservePartnerSoln:=", False,
                "PathRelativeTo:=", "TargetProject",
                "Intrinsics:=", [f"{frequency}Hz"],
                "SurfaceOnly:=", [],
                "LossMultiplier:=", loss_mul
            ])



    def assign_icepak_source(self, assignment=[], thermal_condition=None, assignment_value=None, boundary_name=None) :
        
        # === parameter ===

        # assignment : object name or face number (didn't work) (list compatible)
        # thermal condition : "Total Power", "Surface Flux", "Fixed Temperature"
        # assignment_value : (example) "10W", "AmbientTemp", "30cel"
        # boundary name : assignment name

        # code example : icepak.excitation.assign_icepak_source(assignment=[i_LV_winding.name, i_HV_winding.name], thermal_condition="Fixed Temperature", assignment_value = "AmbientTemp", boundary_name = "cold_plate")
        """
        example :

        self.assign_source(
            assignment=[i_cold_plate_top, i_cold_plate_bottom], 
            thermal_condition="Fixed Temperature", 
            assignment_value="AmbientTemp", 
            boundary_name="cold_plate"
        )
        """

        # ==================
        
        if self.design_type != "Icepak" : return False # verify Icepak or not

        object_name = [obj if isinstance(obj, str) else obj.name for obj in assignment]

        supported = {"Fixed Temperature", "Total Power", "Surface Flux"}
        if thermal_condition not in supported:
            raise ValueError(f"thermal_condition must be one of {sorted(supported)}")

        return self.assign_source(
            assignment=object_name,
            thermal_condition=thermal_condition,
            assignment_value=assignment_value,
            boundary_name=boundary_name,
        )
    


    def set_ambient_temp(self, temp=0) :

        oDesign = self.odesign

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
                            "Value:="		, f"{temp}cel"
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
                            "Value:="		, f"{temp}cel"
                        ]
                    ]
                ]
            ])
        

  
