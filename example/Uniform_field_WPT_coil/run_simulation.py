import sys
import os
import platform
import shutil
import logging
from datetime import datetime

os_name = platform.system()
if os_name == "Windows":
    sys.path.insert(0, r"Y:/git/insulation_amp/pyaedt_library/src/")
    sys.path.insert(0, r"C:/Users/NEC_5950X1/Desktop/git/pyaedt_library/src/")
else :
    # 두 가지 가능한 경로 패턴
    possible_paths = [
        "/gpfs/home1/r1jae262/jupyter/git/pyaedt_library/src/",
        "/gpfs/home2/wjddn5916/Ansys_NEC/git/pyaedt_library/src/"
    ]
    
    # 존재하는 경로만 sys.path에 추가
    for path in possible_paths:
        if os.path.exists(path):
            sys.path.insert(0, path)

import pyaedt_module
from pyaedt_module.core import pyDesktop

import time
from datetime import datetime

import math
import copy

import pandas as pd

import csv
from filelock import FileLock
import traceback

from module.input_parameter import create_input_parameter, set_design_variables
from module.modeling import (
    create_one_turn
)
from module.report import (
    get_input_parameter, get_maxwell_magnetic_parameter,
    get_maxwell_calculator_parameter, get_convergence_report, get_icepak_calculator_parameter
)


def save_error_log(project_name, error_info):
    current_dir = os.getcwd()
    error_folder = os.path.join(current_dir, "simulation", project_name, "error")
    os.makedirs(error_folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = os.path.join(error_folder, f"error_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        filename=error_file,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Log the error
    logging.error(error_info)


class Simulation() :

    def __init__(self) :
        # Set up logging
        current_dir = os.getcwd()
        self.NUM_CORE = 4
        self.NUM_TASK = 1

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

        # Set up logging for this simulation
        folder_path = os.path.join(current_dir, "simulation", self.PROJECT_NAME)
        os.makedirs(folder_path, exist_ok=True)
        log_file = os.path.join(folder_path, "simulation.log")
        
        # Configure logging to write to both file and console
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        logging.info(f"==========simulation{content}==========")

        os_name = platform.system()
        if os_name == "Windows":
            GUI = False
        else :
            GUI = True

        self.desktop = pyDesktop(version=None, non_graphical=GUI)


    def create_design(self, name) :
        self.project = self.desktop.create_project()
        self.maxwell_design = self.project.create_design(name=name, solver="Maxwell3d", solution=None)
        return self.maxwell_design

    
    def create_input_parameter(self, param_list=None) :
        input_parameter = create_input_parameter(self.maxwell_design, param_list)
        logging.info(f"input_parameter : {input_parameter}")
        logging.info("input_parameter : " + ",".join(str(float(v)) for v in input_parameter.values()))
        return input_parameter


    def set_variable(self, input_parameter) :
        # 1. Simulation 클래스 인스턴스에 속성으로 값을 설정합니다 (예: self.N1 = 10).
        for key, value in input_parameter.items():
            setattr(self.maxwell_design, key, value)
        
        self.input_df = pd.DataFrame([input_parameter])
        
        # 2. input_parameter.py의 함수를 호출하여 Ansys 디자인에 변수를 설정합니다.
        set_design_variables(self.maxwell_design, input_parameter)

    def set_maxwell_analysis(self) :
        self.maxwell_design.setup = self.maxwell_design.create_setup(name = "Setup1")
        self.maxwell_design.setup.properties["Max. Number of Passes"] = 12 # 10
        self.maxwell_design.setup.properties["Min. Number of Passes"] = 1
        self.maxwell_design.setup.properties["Min. Converged Passes"] = 3
        self.maxwell_design.setup.properties["Percent Error"] = 2.5 # 2.5
        self.maxwell_design.setup.properties["Frequency Setup"] = f"{self.maxwell_design.frequency}kHz"


    def create_one_turn(self):
        winding_object = []
        for i in range(self.maxwell_design.N):
            a, b = create_one_turn(self.maxwell_design, i, self.maxwell_design.N)
            if a is not None:
                winding_object.append(a)
            if b is not None:
                winding_object.append(b)
        if len(winding_object) > 0:
            self.maxwell_design.winding = self.maxwell_design.modeler.unite(winding_object)



    def create_core(self):
        # self.maxwell_design.set_power_ferrite(cm=0.2435*1e-3, x=2.2, y=2.299)
        self.maxwell_design.set_power_ferrite(cm=2.315, x=1.4472, y=2.4769)
        self.maxwell_design.core = create_core_model(self.maxwell_design)


    def create_core(self):
        # self.maxwell_design.set_power_ferrite(cm=0.2435*1e-3, x=2.2, y=2.299)
        self.maxwell_design.set_power_ferrite(cm=2.315, x=1.4472, y=2.4769)
        self.maxwell_design.core = create_core_model(self.maxwell_design)


    def create_face(self, design_obj):
        create_face(design_obj)


    def create_windings(self):
        """Creates both primary and secondary windings."""
        self.maxwell_design.winding1, self.maxwell_design.winding2, self.maxwell_design.winding3 = create_all_windings(self.maxwell_design)


    def create_mold(self):
        self.maxwell_design.mold = create_mold(self.maxwell_design)
        self.maxwell_design.modeler.subtract(
						blank_list = [self.maxwell_design.mold],
						tool_list = [self.maxwell_design.core, self.maxwell_design.winding1, self.maxwell_design.winding2, self.maxwell_design.winding3],
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
        self.maxwell_design.Tx_winding, self.maxwell_design.Rx_winding1, self.maxwell_design.Rx_winding2 = assign_excitations(self.maxwell_design, self.maxwell_design.winding1, self.maxwell_design.winding2, self.maxwell_design.winding3)

    def analyze_maxwell(self, design):
        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, "simulation", f"{self.PROJECT_NAME}")
        os.makedirs(folder_path, exist_ok=True)  # 폴더가 없으면 생성
        file_path = os.path.join(folder_path, f"{self.PROJECT_NAME}.aedt")
        self.project.save_project(path=file_path)
        
        start_time = time.time()
        logging.info("Maxwell analysis started...")
        design.analyze()
        end_time = time.time()
        logging.info(f"Maxwell analysis finished. Duration: {end_time - start_time:.2f} seconds.")

    def get_simulation_results(self, design=None, input=True, step=1):
        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, "simulation", f"{self.PROJECT_NAME}")
        if input:
            input_df = get_input_parameter(self.maxwell_design)
            result_df = pd.concat([input_df], axis=1)
        else:
            result_df = self.results_df # Use existing df for second run

        
        if step == 1:
            design.magnetic_report, magnetic_df = get_maxwell_magnetic_parameter(design, dir=folder_path, mod="write", import_report=None, report_name="magnetic_report", file_name="magnetic_report1")
            design.calculator_report, calculator_df = get_maxwell_calculator_parameter(design, dir=folder_path, mod="write", import_report=None, report_name="calculator_report", file_name="calculator_report1")
        else:
            design.magnetic_report, magnetic_df = get_maxwell_magnetic_parameter(design, dir=folder_path, mod="read", import_report=self.maxwell_design.magnetic_report, report_name="magnetic_report", file_name="magnetic_report2")
            design.calculator_report, calculator_df = get_maxwell_calculator_parameter(design, dir=folder_path, mod="read", import_report=self.maxwell_design.calculator_report, report_name="calculator_report", file_name="calculator_report2")
        analysis_df = get_convergence_report(design)

        results_df = pd.concat([result_df, magnetic_df, calculator_df, analysis_df], axis=1)
        self.results_df = results_df

        return results_df

    def save_results_to_csv(self, results_df, filename="simulation_results.csv"):
        """Saves the DataFrame to a CSV file in a process-safe way."""
        lock_path = filename + ".lock"
        with FileLock(lock_path):
            file_exists = os.path.isfile(filename)
            results_df.to_csv(filename, mode='a', header=not file_exists, index=False)
        logging.info(f"Results saved to {filename}")


    def second_simulation(self):

        time.sleep(5)

        oProject = self.desktop.odesktop.SetActiveProject(self.project.name)
        oProject.CopyDesign(self.maxwell_design.name)
        oProject.Paste()

        self.maxwell_design2 = self.maxwell_design.get_active_design()

        oProject = self.desktop.odesktop.SetActiveProject(self.project.name)
        oDesign = oProject.SetActiveDesign(self.maxwell_design2.design_name)

        # Map cold plate objects from Maxwell to Maxwell2
        self.maxwell_design2.winding1 = self.maxwell_design2.model3d.find_object(self.maxwell_design.winding1)
        self.maxwell_design2.winding2 = self.maxwell_design2.model3d.find_object(self.maxwell_design.winding2)
        self.maxwell_design2.winding3 = self.maxwell_design2.model3d.find_object(self.maxwell_design.winding3)
        self.maxwell_design2.core = self.maxwell_design2.model3d.find_object(self.maxwell_design.core)  
        self.maxwell_design2.leg_left = self.maxwell_design2.model3d.find_object(self.maxwell_design.leg_left)
        self.maxwell_design2.leg_right = self.maxwell_design2.model3d.find_object(self.maxwell_design.leg_right)
        self.maxwell_design2.leg_center = self.maxwell_design2.model3d.find_object(self.maxwell_design.leg_center)
        self.maxwell_design2.leg_top_left = self.maxwell_design2.model3d.find_object(self.maxwell_design.leg_top_left)
        self.maxwell_design2.leg_top_right = self.maxwell_design2.model3d.find_object(self.maxwell_design.leg_top_right)
        self.maxwell_design2.leg_bottom_left = self.maxwell_design2.model3d.find_object(self.maxwell_design.leg_bottom_left)
        self.maxwell_design2.leg_bottom_right = self.maxwell_design2.model3d.find_object(self.maxwell_design.leg_bottom_right)

        self.maxwell_design2.delete_mesh(self.maxwell_design.skin_depth_mesh)
        
        V = 750
        Im = V/2/3.141592/self.maxwell_design.frequency/1e3/(float(self.results_df["Lmt1"])*1e-6)

        # re excitation
        excitation_list=[self.maxwell_design.Tx_winding.name, self.maxwell_design.Rx_winding1.name, self.maxwell_design.Rx_winding2.name]
        [self.maxwell_design2.Tx_winding, self.maxwell_design2.Rx_winding1, self.maxwell_design2.Rx_winding2] = self.maxwell_design2.get_excitation(excitation_name=excitation_list)

        self.maxwell_design2.Tx_winding["Current"] = f'{Im} * sqrt(2)A'
        self.maxwell_design2.Rx_winding1["Current"] = '0 * sqrt(2)A'
        self.maxwell_design2.Rx_winding2["Current"] = '0 * sqrt(2)A'

        self.maxwell_design2.setup = self.maxwell_design2.get_setup(name="Setup1")
        self.maxwell_design2.setup.properties["Max. Number of Passes"] = 12 # 10
        self.maxwell_design2.setup.properties["Min. Converged Passes"] = 3
        self.maxwell_design2.setup.properties["Percent Error"] = 1 # 2.5


        self.analyze_maxwell(self.maxwell_design2)
        self.get_simulation_results(design=self.maxwell_design2, input=False, step=2)

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

        self.icepak_design.set_ambient_temp(temp=30)

        # Recreate non-model sheet objects in Icepak for result evaluation
        create_face(self.icepak_design)


        # Delete default EM loss boundary that is automatically created        oProject = self.desktop.odesktop.SetActiveProject(self.project.name)
        oDesign = self.icepak_design.odesign
        oModule = oDesign.GetModule("BoundarySetup")
        oModule.DeleteBoundaries(["EMLoss1"])

        # Assign EM Loss from Maxwell analysis to Icepak thermal simulation
        self.icepak_design.assign_EM_loss(name="Coreloss", objects=[self.maxwell_design.core], design=self.maxwell_design2, frequency=self.maxwell_design.frequency*1e+3, loss_mul=self.maxwell_design.core_thermal_ratio)
        self.icepak_design.assign_EM_loss(name="Windingloss", objects=[self.maxwell_design.winding1, self.maxwell_design.winding2, self.maxwell_design.winding3], 
                                          design=self.maxwell_design, frequency=self.maxwell_design.frequency*1e+3, loss_mul=self.maxwell_design.winding_thermal_ratio)
        # self.icepak_design.assign_EM_loss(name="Windingloss", objects=[self.maxwell_design.winding1, self.maxwell_design.winding2], design=self.maxwell_design, frequency=self.freq, loss_mul=1)

        # boundary setup
        self.icepak_design.boundaries[1].properties["X Velocity"] = f"{self.maxwell_design.wind_speed}m_per_sec"

        # Configure Icepak analysis setup
        self.icepak_design.icepak_cetup = self.icepak_design.get_setup(name="Setup1")
        self.icepak_design.icepak_cetup.props["Flow Regime"] = "Turbulent"
        self.icepak_design.icepak_cetup.props["Include Gravity"] = True
        self.icepak_design.icepak_cetup.props["Solution Initialization - Z Velocity"] = "0.1m_per_sec"

        # Map cold plate objects from Maxwell to Icepak
        self.icepak_design.winding1 = self.icepak_design.model3d.find_object(self.maxwell_design.winding1)
        self.icepak_design.winding2 = self.icepak_design.model3d.find_object(self.maxwell_design.winding2)
        self.icepak_design.winding3 = self.icepak_design.model3d.find_object(self.maxwell_design.winding3)
        self.icepak_design.core = self.icepak_design.model3d.find_object(self.maxwell_design.core)  
        self.icepak_design.leg_left = self.icepak_design.model3d.find_object(self.maxwell_design.leg_left)
        self.icepak_design.leg_right = self.icepak_design.model3d.find_object(self.maxwell_design.leg_right)
        self.icepak_design.leg_center = self.icepak_design.model3d.find_object(self.maxwell_design.leg_center)
        self.icepak_design.leg_top_left = self.icepak_design.model3d.find_object(self.maxwell_design.leg_top_left)
        self.icepak_design.leg_top_right = self.icepak_design.model3d.find_object(self.maxwell_design.leg_top_right)
        self.icepak_design.leg_bottom_left = self.icepak_design.model3d.find_object(self.maxwell_design.leg_bottom_left)
        self.icepak_design.leg_bottom_right = self.icepak_design.model3d.find_object(self.maxwell_design.leg_bottom_right)

        

        # Assign fixed temperature boundary condition to the cold plates
        # self.icepak_design.assign_icepak_source(
        #     assignment=[self.icepak_design.cold_plate_top, self.icepak_design.cold_plate_bottom], 
        #     thermal_condition="Fixed Temperature", 
        #     assignment_value="AmbientTemp", 
        #     boundary_name="cold_plate"
        # )

    def analyze_icepak(self):
        """Runs the Icepak analysis."""
        start_time = time.time()
        logging.info("Icepak analysis started...")
        self.icepak_design.analyze()
        end_time = time.time()
        logging.info(f"Icepak analysis finished. Duration: {end_time - start_time:.2f} seconds.")

    def get_icepak_results(self):
        """Retrieves and processes results from the Icepak simulation."""
        

        # Define the temperature parameters to be extracted
        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, "simulation", f"{self.PROJECT_NAME}")
        
        # Get results using the calculator
        self.icepak_design.calculator_report, icepak_results_df = get_icepak_calculator_parameter(
            self.icepak_design, dir=folder_path, mod="write", report_name="thermal_report", file_name="thermal_report1"
        )
        
        # Concatenate Icepak results with the main results DataFrame
        self.results_df = pd.concat([self.results_df, icepak_results_df], axis=1)


    def close_project(self):
        self.maxwell_design.cleanup_solution()
        self.icepak_design.cleanup_solution()

        self.maxwell_design.close_project()

        self.desktop.release_desktop(close_projects=True, close_on_exit=True)

    def delete_project_folder(self):
        time.sleep(10)
        try:
            project_folder = os.path.join(os.getcwd(), "simulation", self.PROJECT_NAME)
            if os.path.isdir(project_folder):
                shutil.rmtree(project_folder)
                logging.info(f"Successfully deleted project folder: {project_folder}")
        except Exception as e:
            logging.error(f"Error deleting project folder {project_folder}: {e}")


def main(test=False):
    for i in range(5000):
        try:
            simulation_runner = Simulation()

            if test == True :
                simulation_runner.test = True
            else :
                simulation_runner.test = False

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
            # simulation_runner.create_mold()
            # simulation_runner.create_cold_plate()
            simulation_runner.create_air()

            # 7. 메쉬 및 경계조건 설정
            simulation_runner.assign_meshing()
            simulation_runner.assign_excitations()

            # 8. 해석 설정 및 실행
            simulation_runner.analyze_maxwell(simulation_runner.maxwell_design)

            # 9. 결과 리포팅
            simulation_runner.get_simulation_results(design=simulation_runner.maxwell_design, input=True)

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

            if test == True :
                break

            simulation_runner.close_project()
            simulation_runner.delete_project_folder()

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
            
            logging.error(f"{simulation_runner.PROJECT_NAME} : {i} simulation Failed")

            if test == True :
                break
            
            simulation_runner.desktop.release_desktop(close_projects=True, close_on_exit=True)
            # simulation_runner.delete_project_folder()

            time.sleep(10)

if __name__ == '__main__':
    main()

