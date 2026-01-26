import os
import psutil
from typing import Optional

from ansys.aedt.core import Desktop as AEDTDesktop

from .pyproject import pyProject, ProjectList

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
            pid = self.pid
            # 잘못된 PID(또는 파이썬 자기 PID)를 죽이면 로그가 flush 되기 전에 프로세스가 종료될 수 있음
            if pid is None or not isinstance(pid, int) or pid <= 0:
                return False
            if pid == os.getpid():
                print("Warning: desktop.pid equals current Python PID. Skip killing to avoid self-termination.")
                return False

            proc = psutil.Process(pid)
            proc.kill()
            try:
                proc.wait(timeout=15)
            except Exception:
                pass
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


    # desktop 상에 열려있는 모든 프로젝트를 종료 후 제거
    def delete(self) -> None :
        [project.delete() for project in self.projects]

    def close(self) -> None :
        return self.close_desktop()



    @property
    def projects(self) -> ProjectList:
        """
        Returns a list of pyProject objects for all open projects.
        Automatically updates each time it's accessed.
        
        Returns:
            ProjectList: List of pyProject objects. Can be accessed by name or index.
            
        Example:
            >>> projects = desktop.projects
            >>> project = desktop.projects["simulation2"]  # 이름으로 접근
            >>> project = desktop.projects[0]  # 인덱스로 접근
        """
        projects = ProjectList()
        project_names = self.project_list

        for project_name in project_names:
            project = pyProject(self, name=project_name)
            projects.append(project)
            
        return projects

    @property
    def pid(self) -> int:
        return self.aedt_process_id



