import os
import psutil

from ansys.aedt.core import Desktop as AEDTDesktop

from .pyproject import pyProject


class pyDesktop(AEDTDesktop) :

    def __init__(
        self,
        version=None,
        non_graphical=False,
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


    def create_project(self) :

        project = pyProject(self)
        self.projects.append(project)
        return project

