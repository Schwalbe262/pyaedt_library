import os
import psutil
from typing import Optional

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
        self.pid = self.aedt_process_id  # get session pid number


    def create_folder(self, folder_name: str) -> str:
        """
        Creates a folder with the given name in the current directory.
        
        Args:
            folder_name: Name of the folder to create.
            
        Returns:
            str: Path to the created folder.
        """
        current_dir = os.getcwd()
        folder_path = os.path.join(current_dir, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        return folder_path


    def kill_process(self) -> bool:
        """
        Kills the AEDT process associated with this desktop session.
        
        Returns:
            bool: True if the process was successfully killed, False otherwise.
        """
        try:
            proc = psutil.Process(self.pid)
            proc.kill()
            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            print(f"Error killing process: {e}")
            return False


    def create_project(self, path: Optional[str] = None, name: Optional[str] = None) -> pyProject:
        project = pyProject(self, path=path, name=name)
        return project

    def load_project(self, path: Optional[str] = None, name: Optional[str] = None) -> pyProject:
        project = pyProject(self, path=path, name=name, forced_load=True)
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
        Uses the projects property internally to avoid code duplication.
        
        Returns:
            dict[str, pyProject]: Dictionary with project names as keys and pyProject objects as values.
            
        Example:
            >>> projects = desktop.get_project_list()
            >>> my_project = projects["MyProject"]  # 이름으로 객체 찾기
        """
        projects_dict = {}
        for project in self.projects:  # projects property 활용
            projects_dict[project.GetName()] = project
            
        return projects_dict



    @property
    def projects(self) -> list[pyProject]:
        """
        Returns a list of pyProject objects for all open projects.
        Automatically updates each time it's accessed.
        
        Returns:
            list[pyProject]: List of pyProject objects for all open projects.
        """
        projects = []
        project_names = self.project_list

        for project_name in project_names:
            project = pyProject(self, name=project_name, load=True)
            projects.append(project)
            
        return projects




