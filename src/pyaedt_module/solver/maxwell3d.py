from ansys.aedt.core import Maxwell3d as AEDTMaxwell3d
import pandas as pd
import numpy as np
import time
import re
import os


class Maxwell3d(AEDTMaxwell3d) :

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)

        self.design = None
        self.report_list = {}


    def set_power_ferrite(self, cm=3, x=1.5, y=2.5, per=1000) :
        
        power_ferrite = self.design.materials.duplicate_material("ferrite","power_ferrite")
        time.sleep(1)
        power_ferrite.set_power_ferrite_coreloss(cm=cm, x=x, y=y)
        power_ferrite.permeability = per

        return power_ferrite

    def get_magnetic_parameter(self, dir=None, parameters=[], mod="write", import_report=None, report_name="magnetic_report") :
        """
        example :
        parameters1 = []
        parameters1.append(["Matrix1.L(LV,LV)","Lrx","uH"])
        # ... (rest of example)
        """
        if mod == "write" :
            result_expressions = [matrix for matrix, _, _ in parameters]
            report = self._create_report(report_name = report_name, result_expressions = result_expressions, category = None)
        elif mod == "read" :
            report = import_report

        # Assuming the report object is stored if mod != "write"
        # This part might need adjustment if report is not persisted.
        if 'report' not in locals() and hasattr(self, 'report_list') and 'magnetic_report' in self.report_list:
            report = self.report_list['magnetic_report']
        elif 'report' not in locals():
            # Handle case where report is not created and not found
            return pd.DataFrame()

        export_path = os.path.join(dir, f"{report.plot_name}.csv")
        self.post.export_report_to_csv(project_dir=dir, plot_name=report.plot_name)
        data = pd.read_csv(export_path)
        
        # Create a mapping from the expression in the report to the desired new name
        rename_mapping = {}
        # Create a mapping for unit conversion
        unit_mapping = {}

        for expression, new_name, unit in parameters:
            # Find the actual column name in the DataFrame, which might include units
            for col in data.columns:
                if expression in col:
                    rename_mapping[col] = new_name
                    unit_mapping[new_name] = unit
                    break
        
        # Select and rename the desired columns
        output_df = data[list(rename_mapping.keys())].rename(columns=rename_mapping)

        # Unit conversion
        # Invert mapping to retrieve original column names for unit parsing
        inverted_rename_mapping = {v: k for k, v in rename_mapping.items()}
        
        # Define unit conversion factors relative to the base unit (e.g., H for inductance)
        unit_factors = {"pH": 1e-12, "nH": 1e-9, "uH": 1e-6, "mH": 1e-3, "H": 1.0}

        for new_col_name, target_unit in unit_mapping.items():
            if new_col_name not in output_df.columns:
                continue

            original_col_name = inverted_rename_mapping.get(new_col_name, "")
            
            # Extract source unit from the original column name (e.g., 'uH' from 'L(V1,V1) [uH]')
            match = re.search(r'\[(.*?)\]', original_col_name)
            source_unit = match.group(1) if match else "" # Defaults to unitless if no [] found

            # Get conversion factors for source and target units
            source_factor = unit_factors.get(source_unit, 1.0)
            target_factor = unit_factors.get(target_unit, 1.0)

            # Calculate the multiplier to convert from source to target unit
            # Example: from mH (1e-3) to uH (1e-6) -> multiplier is 1e-3 / 1e-6 = 1000
            if target_unit == "" or target_unit is None : # Handle unitless parameters like 'k'
                conversion_multiplier = 1.0
            elif target_factor != 0:
                conversion_multiplier = source_factor / target_factor
            else:
                conversion_multiplier = 1.0
            
            # Apply the conversion to the column
            output_df[new_col_name] = pd.to_numeric(output_df[new_col_name], errors='coerce').abs() * conversion_multiplier

        output_df.dropna(inplace=True)

        #output_df.to_csv("maxwell_magnetic.csv")
        
        return report, output_df


    def get_calculator_parameter(self, dir=None, parameters=[], mod="write", import_report=None, report_name="calculator_report") :
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
        elif mod == "read" :
            report = import_report
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

        export_path = os.path.join(dir, f"{report.plot_name}.csv")
        self.post.export_report_to_csv(project_dir=dir, plot_name=report.plot_name)
        data = pd.read_csv(export_path)

        # Create a mapping from the actual column names in the CSV to the desired names
        rename_mapping = {}
        for expr, desired_name in zip(result_expressions, name_list):
            for col in data.columns:
                if expr in col:
                    rename_mapping[col] = desired_name
                    break
        
        # Rename columns and select only the ones we need, in the correct order.
        output_df = data.rename(columns=rename_mapping)
        
        # Ensure all desired columns exist, adding missing ones with NaN
        for name in name_list:
            if name not in output_df.columns:
                output_df[name] = np.nan
        
        output_df = output_df[name_list]

        output_df.dropna(inplace=True)

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
    

