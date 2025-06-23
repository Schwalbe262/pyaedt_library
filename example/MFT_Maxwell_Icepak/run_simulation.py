import sys
import os

os_name = platform.system()
if os_name == "Windows":
    sys.path.insert(0, r"Y:/git/insulation_amp/pyaedt_library/src/") 
else :
    sys.path.insert(0, r"/gpfs/home1/r1jae262/jupyter/git/pyaedt_library/src/")

import pyaedt_module
from pyaedt_module.core import pyDesktop

import time
from datetime import datetime

import math
import copy

import pandas as pd

import platform
import csv
from filelock import FileLock
import traceback
import logging

from input_parameter import create_input_parameter, calculate_coil_parameter, calculate_coil_offset, set_design_variables
from modeling import (
    create_core_model, create_all_windings, create_cold_plate, create_air,
    assign_meshing, assign_excitations, create_face, create_mold
)
from report import (
    get_input_parameter, get_maxwell_magnetic_parameter,
    get_maxwell_calculator_parameter, get_convergence_report, get_icepak_calculator_parameter
)


def save_error_log(project_name, error_info):
    error_folder = "error"
    os.makedirs(error_folder, exist_ok=True)
    error_file = os.path.join(error_folder, f"{project_name}_error.txt")
    with open(error_file, "w", encoding="utf-8") as f:
        f.write(error_info)


class Simulation() :

    def __init__(self) :

        self.NUM_CORE = 1
        self.NUM_TASK = 1
        self.freq = 30e3

        
        os_name = platform.system()
        if os_name == "Windows":
            GUI = False
        else :
            GUI = True

        self.desktop = pyDesktop(version=None, non_graphical=GUI)

        file_path = "simulation_num.txt"

        # 파일이 존재하지 않으면 생성
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("1")

        # 읽기/쓰기 모드로 파일 열기
        with open(file_path, "r+", encoding="utf-8") as file:

            # 파일에서 값 읽기
            content = int(file.read().strip())
            self.num = content
            self.PROJECT_NAME = f"simulation{content}"
            content += 1

            # 파일 포인터를 처음으로 되돌리고, 파일 내용 초기화 후 새 값 쓰기
            file.seek(0)
            file.truncate()
            file.write(str(content))

            # 파일은 with 블록 종료 시 자동으로 닫히며, 잠금도 해제됨


    def create_design(self, name) :
        self.project = self.desktop.create_project()
        self.maxwell_design = self.project.create_design(name=name, solver="Maxwell3d", solution=None)
        return self.maxwell_design

    
    def create_input_parameter(self) :
        return create_input_parameter(self.maxwell_design)


    def set_variable(self, input_parameter) :
        # 1. Simulation 클래스 인스턴스에 속성으로 값을 설정합니다 (예: self.N1 = 10).
        for key, value in input_parameter.items():
            setattr(self.maxwell_design, key, value)
        
        self.input_df = pd.DataFrame([input_parameter])
        
        # 2. input_parameter.py의 함수를 호출하여 Ansys 디자인에 변수를 설정합니다.
        set_design_variables(self.maxwell_design, input_parameter)

    def set_maxwell_analysis(self) :
        self.setup = self.maxwell_design.create_setup(name = "Setup1")
        self.setup.props["MaximumPasses"] = 10
        self.setup.props["MinimumPasses"] = 1
        self.setup.props["PercentError"] = 2.5
        self.setup.props["Frequency"] = "30kHz"
        self.maxwell_design.freq = 30e+3

    def create_core(self):
        self.maxwell_design.set_power_ferrite(cm=0.2435*1e-3, x=2.2, y=2.299)
        self.maxwell_design.core = create_core_model(self.maxwell_design)

    def create_face(self, design_obj):
        create_face(design_obj)

    def create_windings(self):
        """Creates both primary and secondary windings."""
        self.maxwell_design.winding1, self.maxwell_design.winding2 = create_all_windings(self.maxwell_design)

    def create_mold(self):
        self.maxwell_design.mold = create_mold(self.maxwell_design)
        self.maxwell_design.modeler.subtract(
						blank_list = [self.maxwell_design.mold],
						tool_list = [self.maxwell_design.core, self.maxwell_design.winding1, self.maxwell_design.winding2],
						keep_originals = True
					)

    def create_cold_plate(self):
        """Creates the cold plates."""
        self.maxwell_design.cold_plate_top, self.maxwell_design.cold_plate_bottom = create_cold_plate(self.maxwell_design)

    def create_air(self):
        """Creates the air region."""
        self.maxwell_design.air_region = create_air(self.maxwell_design)

    def assign_meshing(self):
        """Assigns mesh operations."""
        self.maxwell_design.length_mesh, self.maxwell_design.skin_depth_mesh = assign_meshing(self.maxwell_design)

    def assign_excitations(self):
        """Identifies terminals and assigns all excitations."""
        self.maxwell_design.Tx_winding, self.maxwell_design.Rx_winding = assign_excitations(self.maxwell_design, self.maxwell_design.winding1, self.maxwell_design.winding2)

    def analyze_maxwell(self):
        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, "simulation", f"{self.PROJECT_NAME}")
        os.makedirs(folder_path, exist_ok=True)  # 폴더가 없으면 생성
        file_path = os.path.join(folder_path, f"{self.PROJECT_NAME}.aedt")
        self.project.save_project(path=file_path)
        self.maxwell_design.analyze()

    def get_simulation_results(self, input=True, step=1):
        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, "simulation", f"{self.PROJECT_NAME}")
        if input:
            input_df = get_input_parameter(self.maxwell_design)
            result_df = pd.concat([input_df], axis=1)
        else:
            result_df = self.results_df # Use existing df for second run

        
        if step == 1:
            self.maxwell_design.magnetic_report, magnetic_df = get_maxwell_magnetic_parameter(self.maxwell_design, dir=folder_path, mod="write", import_report=None)
            self.maxwell_design.calculator_report, calculator_df = get_maxwell_calculator_parameter(self.maxwell_design, dir=folder_path, mod="write", import_report=None)
        else:
            self.maxwell_design.magnetic_report, magnetic_df = get_maxwell_magnetic_parameter(self.maxwell_design, dir=folder_path, mod="read", import_report=self.maxwell_design.magnetic_report)
            self.maxwell_design.calculator_report, calculator_df = get_maxwell_calculator_parameter(self.maxwell_design, dir=folder_path, mod="read", import_report=self.maxwell_design.calculator_report)
        analysis_df = get_convergence_report(self.maxwell_design)

        results_df = pd.concat([result_df, magnetic_df, calculator_df, analysis_df], axis=1)
        self.results_df = results_df

        return results_df

    def save_results_to_csv(self, results_df, filename="simulation_results.csv"):
        """Saves the DataFrame to a CSV file in a process-safe way."""
        lock_path = filename + ".lock"
        with FileLock(lock_path):
            file_exists = os.path.isfile(filename)
            results_df.to_csv(filename, mode='a', header=not file_exists, index=False)
        print(f"Results saved to {filename}")


    def second_simulation(self):
        self.maxwell_design.skin_depth_mesh.delete()
        V = 1000
        Im = V/2/3.141592/30e+3/(float(self.results_df["Lmt"])*1e-6)

        # re excitation
        self.maxwell_design.Tx_winding["Current"] = f'{Im} * sqrt(2)A'
        self.maxwell_design.Rx_winding["Current"] = '0 * sqrt(2)A'

        self.setup.props["MaximumPasses"] = 10 # 10
        self.setup.props["PercentError"] = 1

        self.analyze_maxwell()
        self.get_simulation_results(input=False, step=2)

    def create_icepak(self):

        oProject = self.desktop.odesktop.SetActiveProject(self.project.name)
        oDesign = oProject.SetActiveDesign(self.maxwell_design.design_name)
        oDesign.CreateEMLossTarget("Icepak", "Setup1 : LastAdaptive", 
            [
                "NAME:DesignSetup",
                "Sim Type:="		, "Forced"
            ])
        self.icepak_design = self.maxwell_design.get_active_design()

        return self.icepak_design

    def setup_icepak_analysis(self):
        """Sets up the Icepak analysis, including loss mapping and boundary conditions."""

        self.icepak_design.set_ambient_temp(temp=50)

        # Recreate non-model sheet objects in Icepak for result evaluation
        create_face(self.icepak_design)


        # Delete default EM loss boundary that is automatically created        oProject = self.desktop.odesktop.SetActiveProject(self.project.name)
        oDesign = self.icepak_design.odesign
        oModule = oDesign.GetModule("BoundarySetup")
        oModule.DeleteBoundaries(["EMLoss1"])

        # Assign EM Loss from Maxwell analysis to Icepak thermal simulation
        self.icepak_design.assign_EM_loss(name="Coreloss", objects=[self.maxwell_design.core], design=self.maxwell_design, frequency=self.freq, loss_mul=1)
        # self.icepak_design.assign_EM_loss(name="Windingloss", objects=[self.maxwell_design.winding1, self.maxwell_design.winding2], design=self.maxwell_design, frequency=self.freq, loss_mul=1)


        # Configure Icepak analysis setup
        icepak_setup = self.icepak_design.get_setup(name="Setup1")
        icepak_setup.props["Flow Regime"] = "Turbulent"
        icepak_setup.props["Include Gravity"] = True
        icepak_setup.props["Solution Initialization - Z Velocity"] = "0.1m_per_sec"

        # Map cold plate objects from Maxwell to Icepak
        self.icepak_design.cold_plate_top = self.icepak_design.model3d.find_object(self.maxwell_design.cold_plate_top)
        self.icepak_design.cold_plate_bottom = self.icepak_design.model3d.find_object(self.maxwell_design.cold_plate_bottom)
        self.icepak_design.winding1 = self.icepak_design.model3d.find_object(self.maxwell_design.winding1)
        self.icepak_design.winding2 = self.icepak_design.model3d.find_object(self.maxwell_design.winding2)
        self.icepak_design.core = self.icepak_design.model3d.find_object(self.maxwell_design.core)  
        self.icepak_design.leg_left = self.icepak_design.model3d.find_object(self.maxwell_design.leg_left)
        self.icepak_design.leg_right = self.icepak_design.model3d.find_object(self.maxwell_design.leg_right)
        self.icepak_design.leg_top = self.icepak_design.model3d.find_object(self.maxwell_design.leg_top)
        self.icepak_design.leg_bottom = self.icepak_design.model3d.find_object(self.maxwell_design.leg_bottom)

        # Assign fixed temperature boundary condition to the cold plates
        self.icepak_design.assign_icepak_source(
            assignment=[self.icepak_design.cold_plate_top, self.icepak_design.cold_plate_bottom], 
            thermal_condition="Fixed Temperature", 
            assignment_value="AmbientTemp", 
            boundary_name="cold_plate"
        )
        self.icepak_design.assign_icepak_source(
            assignment=[self.icepak_design.winding1, self.icepak_design.winding2], 
            thermal_condition="Fixed Temperature", 
            assignment_value="AmbientTemp", 
            boundary_name="winding"
        )

    def analyze_icepak(self):
        """Runs the Icepak analysis."""
        self.icepak_design.analyze()

    def get_icepak_results(self):
        """Retrieves and processes results from the Icepak simulation."""
        

        # Define the temperature parameters to be extracted
        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, "simulation", f"{self.PROJECT_NAME}")
        
        # Get results using the calculator
        self.icepak_design.calculator_report, icepak_results_df = get_icepak_calculator_parameter(
            self.icepak_design, dir=folder_path
        )
        
        # Concatenate Icepak results with the main results DataFrame
        self.results_df = pd.concat([self.results_df, icepak_results_df], axis=1)


    def close_project(self):
        self.maxwell_design.cleanup_solution()
        self.icepak_design.cleanup_solution()

        self.maxwell_design.close_project()

        self.desktop.release_desktop(close_projects=True, close_on_exit=True)


if __name__ == '__main__':
    simulation_runner = Simulation()
    for i in range(5000):
        try:
            # 2. create_design 메서드를 호출하여 프로젝트와 디자인을 초기화합니다.
            simulation_runner.create_design("SST_MFT")

            # 3. 이제 입력 매개변수를 생성할 수 있습니다.
            input_parameters = simulation_runner.create_input_parameter()
            
            # 4. 생성된 파라미터를 Simulation 객체와 Ansys 디자인에 설정합니다.
            simulation_runner.set_variable(input_parameters)

            # 5. 해석 설정 및 실행
            simulation_runner.set_maxwell_analysis()

            # 6. 모델을 생성합니다.
            simulation_runner.create_core()
            simulation_runner.create_face(simulation_runner.maxwell_design)
            simulation_runner.create_windings()
            simulation_runner.create_mold()
            simulation_runner.create_cold_plate()
            simulation_runner.create_air()

            # 7. 메쉬 및 경계조건 설정
            simulation_runner.assign_meshing()
            simulation_runner.assign_excitations()

            # 8. 해석 설정 및 실행
            simulation_runner.analyze_maxwell()

            # 9. 결과 리포팅
            simulation_runner.get_simulation_results(input=True)

            # 10. 두 번째 해석 실행
            simulation_runner.second_simulation()

            # 11. Icepak 디자인 생성
            simulation_runner.create_icepak()       

            # 12. Icepak 해석 설정
            simulation_runner.setup_icepak_analysis()

            # 13. Icepak 해석 실행
            simulation_runner.analyze_icepak()

            # 14. Icepak 결과 리포팅
            simulation_runner.get_icepak_results()

            # 15. 결과 저장
            simulation_runner.save_results_to_csv(simulation_runner.results_df)

            simulation_runner.close_project()

        except Exception as e:
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            
            err_info = f"error : {simulation_runner.PROJECT_NAME}\n"
            try:
                err_info += f"input : {simulation_runner.input_df.to_string()}\n"
            except AttributeError:
                err_info += "input : Not available\n"
            
            err_info += f"{str(e)}\n"
            err_info += traceback.format_exc()

            print(err_info, file=sys.stderr)
            sys.stderr.flush()
            
            logging.error(err_info, exc_info=True)
            
            save_error_log(simulation_runner.PROJECT_NAME, err_info)
            
            print(f"{simulation_runner.PROJECT_NAME} : {i} simulation Failed")
            
            simulation_runner.desktop.release_desktop(close_projects=True, close_on_exit=True)
            
            # Re-initialize for the next run
            simulation_runner = Simulation()
            time.sleep(1)
        

        
