import pyaedt
from pyaedt import Desktop
import os
import shutil
import math
import pandas as pd

from pyaedt import Maxwell3d



class Result :

    def __init__(self, design, project_dir):
        self.design = design
        self.dir = project_dir
        self.report_list = {}



    def get_magnetic_parameter(self, name=None, parameters=[], mod="write") :

        # parameter format
        # ["Matrix1.L(Tx,Tx)", "Ltx", "uH"]

        # first operation (create report)
        if mod == "write" :

            result_expressions = []

            for matrix, expression, unit in parameters:
                result_expressions.append(matrix)

            report = self._create_report(report_name = "magnetic_report", result_expressions = result_expressions, category = None)
            self.report_list[name] = report # add to report data stack


        export_data = self.design.post.export_report_to_csv(project_dir=self.dir, plot_name=self.report_list[name].plot_name)
        data = pd.read_csv(export_data)
        

        for itr, column_name in enumerate(data.columns):
            data[column_name] = abs(data[column_name])

            if itr == 0:  # delete "Freq [kHz]" columns
                data = data.drop(columns=column_name)
                continue
            
            # identify each parameter unit scale
            unit = 0
            if parameters[itr-1][2] == "nH":
                unit = 1e+9
            elif parameters[itr-1][2] == "uH":
                unit = 1e+6
            elif parameters[itr-1][2] == "mH":
                unit = 1e+3

            # unit scaling
            if unit != 0:
                if "[pH]" in column_name:  # consider error case
                    return False
                elif "[nH]" in column_name:
                    data[column_name] = data[column_name] * 1e-9 * unit
                elif "[uH]" in column_name:
                    data[column_name] = data[column_name] * 1e-6 * unit
                elif "[mH]" in column_name:
                    data[column_name] = data[column_name] * 1e-3 * unit
                elif "[H]" in column_name:  # consider error case
                    return False

        data.columns = [item[1] for item in parameters]

        return data



    def get_calculator_parameter(self, name=None, parameters=[], mod="write") :

        # parameter format
        # [object, loss, name]
        
        
        name_list = [item[2] for item in parameters]

        # first operation (create report)
        if mod == "write" :
            result_expressions = self._add_calculator_expression(parameters=parameters)
            report = self._create_report(report_name = "calculator_report", result_expressions = result_expressions, category = "Fields")
            self.report_list[name] = report # add to report data stack
        
        export_data = self.design.post.export_report_to_csv(project_dir=self.dir, plot_name=self.report_list[name].plot_name)
        data = pd.read_csv(export_data)

        # unwanted column filtering
        columns_to_keep = []
        for column_name in data.columns:
            if any(column_name.startswith(prefix) for prefix in name_list):
                columns_to_keep.append(column_name)

        data = data[columns_to_keep]  # filtered data

        data.columns = name_list # new column name
            

        return data
    

    # for maxwell 3D
    def get_convergence_report(self, setup_name="Setup1") :
        

        report = self.design.export_convergence(setup_name=setup_name, variation_string="", file_path=None)
        filename = report
        result = self._extract_data_from_last_line(filename)
        
        return result



    def _extract_data_from_last_line(self, filename):
    
        with open(filename, 'r') as file:
            lines = file.readlines()

        # 공백이 아닌 마지막 줄을 찾기
        for line in reversed(lines):
            if line.strip():  # 줄이 공백이 아닐 경우
                last_data_line = line
                break

        parts = last_data_line.split('|')
        pass_number = parts[0].strip()
        tetrahedra = parts[1].strip()
        total_energy = parts[2].strip()
        energy_error = parts[3].strip()
        delta_energy = parts[4].strip()

        data = {
            'Pass Number': [pass_number],
            'Tetrahedra': [tetrahedra],
            'Total Energy': [total_energy],
            'Energy Error': [energy_error],
            'Delta Energy': [delta_energy]
        }

        df = pd.DataFrame(data)

        return df


    
    def _create_report(self, report_name = "report", result_expressions=[], category=None) :

        report = self.design.post.create_report(expressions=result_expressions, setup_sweep_name=None, domain='Sweep', 
                    variations=None, primary_sweep_variable=None, secondary_sweep_variable=None, 
                    report_category=category, plot_type='Data Table', context=None, subdesign_id=None, polyline_points=1001, plotname=report_name)

        return report




    def _add_calculator_expression(self, parameters) :

        result_expressions = []
        name_list = []

        for obj, expression, name in parameters:
            if expression == "B_mean" :
                result_expressions.append(self._get_mean_Bfield(obj))

            elif expression == "Temp_max" :
                result_expressions.append(self._get_temp(obj=obj, mod="max"))

            elif expression == "Temp_mean" :
                result_expressions.append(self._get_temp(obj=obj, mod="mean"))

            else :
                result_expressions.append(self._get_calculator_loss(obj, expression)) # field calculator

            name_list.append(name)

        return result_expressions, name_list





    def _get_calculator_loss(self, obj, loss) :

        # === loss ===
        # OhmicLoss
        # CoreLoss
        # EMLoss

        assignment = obj if isinstance(obj, str) else obj.name
        
        oModule = self.design.ofieldsreporter
        oModule.CalcStack("clear")
        oModule.EnterQty(loss)
        oModule.EnterVol(assignment)
        oModule.CalcOp("Integrate")
        name = "P_{}".format(assignment)  # Need to check for uniqueness !
        oModule.AddNamedExpression(name, "Fields")

        return name
    


    def _get_mean_Bfield(self, obj) :

        assignment = obj.name

        oModule = self.design.ofieldsreporter
        oModule.CalcStack("clear")
        oModule.CopyNamedExprToStack("Mag_B")
        oModule.EnterVol(assignment)
        oModule.CalcOp("Mean")
        name = "B_mean_{}".format(assignment)  # Need to check for uniqueness !
        oModule.AddNamedExpression(name, "Fields")

        return name



    def _get_temp(self, obj, mod) :

        assignment = obj.name
        name = None

        oModule = self.design.ofieldsreporter
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

