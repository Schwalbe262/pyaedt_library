import pyaedt
import os
import shutil
import stat
import time

from .pydesign import pyDesign

class pyProject:

    def __init__(self, desktop, path=None, name=None, load=False) :

        self.desktop = desktop

        self.designs = []

        if load is False:
            if path is None:
                path = pyaedt.generate_unique_project_name()
                self.project = self.desktop.odesktop.NewProject(path)
            else:
                self.project = self.desktop.odesktop.NewProject(path)
                self.project.SaveAs(path, True)
        else:
            self.project = self.desktop.odesktop.SetActiveProject(name)

        # underlying AEDT project object (for __getattr__ forwarding)
        self.proj = self.project

        # project attributes
        self._get_project_attribute()

        # designs (loaded project에서만 채움)
        if load is True:
            self._get_designs()

        self.solver_instance = None


    def __getattr__(self, name):
        return getattr(self.proj, name)
    
    def __dir__(self):
        default_dir = super().__dir__()
        if self.solver_instance is not None:
            return list(set(default_dir + dir(self.proj)))
        return default_dir


    def _get_project_attribute(self) :

        self.name = self.GetName()
        self.path = self.GetPath()
        self.aedt_path = os.path.join(self.path, self.name + ".aedt")

    
    def save_project(self, path=None) :

        if path == None :
            path = os.path.join(os.getcwd(), self.name + ".aedt")
        else :
            path = os.path.normpath(os.path.abspath(path)) # OS compatibility

        # make dir
        save_dir = os.path.dirname(path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        self.desktop.save_project(self.name, path)

        norm_path = os.path.normpath(self.path)
        basename = os.path.basename(norm_path)

        # delete Temp folder
        if os.path.exists(norm_path) and "Temp" in norm_path and basename.startswith("pyaedt_prj_"):
            shutil.rmtree(norm_path)

        self._get_project_attribute()


    def delete_project(self) :

        base_name = os.path.splitext(os.path.basename(self.aedt_path))[0]

        file_aedt = os.path.join(self.path, base_name + ".aedt")
        file_lock = os.path.join(self.path, base_name + ".aedt.lock")
        folder_results = os.path.join(self.path, base_name + ".aedtresults")

        if os.path.exists(file_aedt):
            os.remove(file_aedt)
        if os.path.exists(file_lock):
            os.remove(file_lock)
        if os.path.exists(folder_results):
            shutil.rmtree(folder_results)


    def _remove_readonly(self, func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)


    def delete_project_folder(self, path=None, retries=10, delay=1):
        if path is None:
            path = self.GetPath()
        
        if os.path.exists(path) and os.path.isdir(path):
            for attempt in range(retries):
                try:
                    shutil.rmtree(path, onerror=self._remove_readonly)
                    return True
                except Exception as e:
                    time.sleep(delay)
            return False
        else:
            return False


    def create_design(self, name, solver, solution=None):
        design = pyDesign.create_design(self, name=name, solver=solver, solution=solution)
        self.designs.append(design)
        return design


    def _get_designs(self) :
        self.designs = []
        for design in self.project.GetDesigns():
            self.designs.append(pyDesign(self, design=design))
        return self.designs
