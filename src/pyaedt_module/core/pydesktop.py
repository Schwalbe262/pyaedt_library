import os
import psutil

from ansys.aedt.core import Desktop as AEDTDesktop

from .pyproject import pyProject

import socket # for grpc


class pyDesktop(AEDTDesktop) :

    def __init__(
        self,
        version=None,
        non_graphical=True if os.name != "nt" else False,
        new_desktop=True,
        close_on_exit=True,
        student_version=False,
        machine="",
        port=0,
        aedt_process_id=None,
        *args,
        **kwargs
    ):
        

        super().__init__(
            version=version,
            non_graphical=non_graphical,
            new_desktop=new_desktop,
            close_on_exit=close_on_exit,
            student_version=student_version,
            machine=machine,
            port=port,
            aedt_process_id=aedt_process_id,
            *args,
            **kwargs
        )

        self.disable_autosave()
        self.pid = self.aedt_process_id # get session pid number

        self.projects = []


    def create_folder(self, folder_name):
        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        return folder_path


    def kill_process(self):
        try:
            proc = psutil.Process(self.pid)
            proc.kill()
            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            print(f"Error killing process: {e}")
            return False


    def create_project(self, path=os.getcwd(), name=None) :

        project = pyProject(self, path=path)
        self.projects.append(project)
        return project


    def load_project(self, path: str):
        """
        Load an existing AEDT project file and return pyProject wrapper.
        """
        # AEDTDesktop에는 load_project(path)가 있는 버전도 있지만,
        # 여기서는 현재 세션의 odesktop API로 명시적으로 로드한다.
        # OpenProject는 성공 시 프로젝트 이름을 반환하거나 active project를 변경한다.
        self.odesktop.OpenProject(path)
        name = self.odesktop.GetActiveProject().GetName()
        project = pyProject(self, name=name, load=True)
        self.projects.append(project)
        return project

    # legacy code
    # def get_project_list(self) :
        
    #     project_list = []
    #     for project_name in self.project_list:
    #         project = pyProject(self, name=project_name, load=True)
    #         project_list.append(project)

    #     return project_list


    # desktop 객체에 열려있는 project를 이름-객체 쌍의 딕셔너리 형태로 반환
    def get_project_list(self) -> dict[str, pyProject]:
        """
        Returns a dictionary mapping project names to pyProject objects.
        
        Returns:
            dict[str, pyProject]: Dictionary with project names as keys and pyProject objects as values.
            
        Example:
            >>> projects = desktop.get_project_list()
            >>> my_project = projects["MyProject"]  # 이름으로 객체 찾기
        """
        projects = {}
        project_names = self.project_list

        for project_name in project_names:
            project = pyProject(self, name=project_name, load=True)
            projects[project_name] = project
            
        return projects


    def debug2(self) :
        print("debug mode")




