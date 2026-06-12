from ansys.aedt.core import Maxwell3d as AEDTMaxwell3d
import pandas as pd
import numpy as np
import time

from ._reports import export_report_to_dataframe, select_report_columns


class Maxwell3d(AEDTMaxwell3d) :

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)

        self.design = None
        self.report_list = {}

    def assign_matrix(self, args=None, matrix_name=None, assignment=None, **kwargs):
        """Assign a Maxwell matrix while preserving the legacy helper API.

        PyAEDT 1.0.1 expects a structured matrix schema. Older examples in this
        repository call ``assign_matrix(matrix_name=..., assignment=[...])``.
        When that legacy shape is used, convert it to ``MatrixACMagnetic``.
        Structured arguments are forwarded unchanged.
        """
        if args is not None:
            return super().assign_matrix(args)

        if assignment is None:
            assignment = kwargs.pop("assignment", None)
        if assignment is None:
            assignment = kwargs.pop("sources", None)
        if matrix_name is None:
            matrix_name = kwargs.pop("matrix_name", "Matrix")

        if assignment is None:
            return super().assign_matrix(**kwargs)

        from ansys.aedt.core.modules.boundary.maxwell_boundary import MatrixACMagnetic

        sources = assignment
        if not isinstance(sources, dict):
            sources = [item.name if hasattr(item, "name") else item for item in sources]

        return super().assign_matrix(MatrixACMagnetic(sources=sources, matrix_name=matrix_name))


    def set_power_ferrite(self, cm=3, x=1.5, y=2.5, per=1000) :
        
        power_ferrite = self.design.materials.duplicate_material("ferrite","power_ferrite")
        time.sleep(1)
        power_ferrite.set_power_ferrite_coreloss(cm=cm, x=x, y=y)
        power_ferrite.permeability = per

        return power_ferrite

    def get_magnetic_parameter(self, dir=None, parameters=[], mod="write", import_report=None, report_name="magnetic_report", file_name="magnetic_report") :
        """
        example :
        parameters1 = []
        parameters1.append(["Matrix1.L(LV,LV)","Lrx","uH"])
        # ... (rest of example)
        """
        if mod == "write" :
            result_expressions = [matrix for matrix, _, _ in parameters]
            report = self._create_report(report_name = report_name, result_expressions = result_expressions, category = None)
            self.report_list[report_name] = report
        elif mod == "read" :
            report = import_report

        # Assuming the report object is stored if mod != "write"
        # This part might need adjustment if report is not persisted.
        if 'report' not in locals() and hasattr(self, 'report_list') and report_name in self.report_list:
            report = self.report_list[report_name]
        elif 'report' not in locals():
            # Handle case where report is not created and not found
            return None, pd.DataFrame()
        

        data = export_report_to_dataframe(self, dir, report_name, file_name)
        expressions = [expression for expression, _, _ in parameters]
        names = [new_name for _, new_name, _ in parameters]
        units = [unit for _, _, unit in parameters]
        output_df = select_report_columns(data, expressions, names, units)

        #output_df.to_csv("maxwell_magnetic.csv")
        
        return report, output_df


    def get_calculator_parameter(self, dir=None, parameters=[], mod="write", import_report=None, report_name="calculator_report", file_name="calculator_report") :
        """
        example :
        parameters2 = []
        parameters2.append([winding1, "P_LV", "EMLoss"])
        # ... (rest of example)
        """
        # Note: In "read" mode, this function re-adds expressions. For it to be truly read-only,
        # the logic would need to change to not call _add_calculator_expression.
        # Given the current usage, we proceed assuming "write" is the primary path.
        
        if mod == "write" :
            result_expressions, name_list = self._add_calculator_expression(parameters=parameters)
            report = self._create_report(report_name = report_name, result_expressions = result_expressions, category = "Fields")
            self.report_list[report_name] = report
        elif mod == "read" :
            report = import_report or self.report_list.get(report_name)
            # In "read" mode, we must reconstruct the expression and name lists
            # that would have been created in "write" mode, without modifying the AEDT project.
            name_list = []
            result_expressions = []
            for obj, name, expression_type in parameters:
                name_list.append(name)
                obj_name = obj.name if hasattr(obj, 'name') else obj
                
                if expression_type == "B_mean":
                    expr_name = f"B_mean_{obj_name}"
                else: # Handles "EMLoss", "CoreLoss" by mimicking _get_calculator_loss
                    expr_name = f"P_{obj_name}"
                result_expressions.append(expr_name)
        
        if not report:
             # This can happen in read mode if no report is imported.
             # Return an empty DataFrame with the expected column names.
             return None, pd.DataFrame(columns=name_list)

        data = export_report_to_dataframe(self, dir, report_name, file_name)
        output_df = select_report_columns(data, result_expressions, name_list, add_missing=True)

        #output_df.to_csv("maxwell_calculator.csv")

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
            if expression == "B_mean" :
                result_expressions.append(self._get_mean_Bfield(obj))
            else :
                result_expressions.append(self._get_calculator_loss(obj, expression))
            name_list.append(name)
        return result_expressions, name_list

    def _get_calculator_loss(self, obj, loss) :
        assignment = obj if isinstance(obj, str) else obj.name
        oModule = self.ofieldsreporter
        oModule.CalcStack("clear")
        oModule.EnterQty(loss)
        oModule.EnterVol(assignment)
        oModule.CalcOp("Integrate")
        name = f"P_{assignment}"
        oModule.AddNamedExpression(name, "Fields")
        return name
    
    def _get_mean_Bfield(self, obj) :
        assignment = obj.name
        oModule = self.ofieldsreporter
        oModule.CalcStack("clear")
        oModule.CopyNamedExprToStack("Mag_B")
        oModule.EnterVol(assignment) if obj.is3d else oModule.EnterSurf(assignment)
        oModule.CalcOp("Mean")
        name = f"B_mean_{assignment}"
        oModule.AddNamedExpression(name, "Fields")
        return name
    

