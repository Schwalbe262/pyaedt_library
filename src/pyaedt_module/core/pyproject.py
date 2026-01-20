import pyaedt
import os
import shutil
import stat
import time
from typing import Optional

from .pydesign import pyDesign, DesignList




class ProjectList(list):
    """
    커스텀 리스트 클래스: 이름으로 project에 접근할 수 있게 함
    """
    def __getitem__(self, key):
        # 문자열이면 이름으로 검색
        if isinstance(key, str):
            for project in self:
                if project.name == key:
                    return project
            raise KeyError(f"Project '{key}' not found")
        # 정수면 일반 리스트처럼 인덱스로 접근
        return super().__getitem__(key)


class pyProject:

    def __init__(self, desktop, path: Optional[str] = None, name: Optional[str] = None, forced_load: bool = True) -> None:


        self.desktop = desktop

        # project 객체를 가져와서 저장 (이 객체의 모든 메서드/속성을 pyProject가 위임받음)
        self.project = self._get_project(path=path, name=name, forced_load=forced_load)
        
        # underlying AEDT project object (for __getattr__ forwarding)
        # self.proj는 self.project와 동일하지만, 명시적으로 유지
        self.proj = self.project

        self.solver_instance = None



    def _get_project(self, path: Optional[str] = None, name: Optional[str] = None, forced_load: bool = True):

        #가능한 입력 케이스

        # path를 None으로 둠
            # name을 None으로 둠 => 작동 확인
            # name을 임의의 이름으로 둠 => 작동 확인
        # path를 ~~/~~/~~/simulation.aedt 형태로 입력
            # name을 None으로 둠 => 작동 확인
            # name을 simulation으로 둠 => 작동 확인
            # name을 simulation.aedt로 둠 => 작동 확인
        # path를 ~~/~~/~~/simulation 형태로 입력
            # name을 None으로 둠 => 작동하나 simulation은 경로로 인식함
            # name을 simulation으로 둠 => ~~/~~/~~/simulation.aedt 형태로 생성
        # path를 ~~~/~~/~~ 형태로 입력

        # 이미 project도 열려있고 해당 파일도 있는데 또 요청하는 경우 무시 필요

        # name 기본값 설정
        if name is None:
            name = pyaedt.generate_unique_project_name() # 해당 값의 포맷 예시 : 'C:\\Users\\peets\\AppData\\Local\\Temp\\pyaedt_prj_COM\\Project_QWI.aedt'
            name = os.path.splitext(os.path.basename(name))[0]
        # name이 .aedt로 끝나면 확장자를 떼어낸다
        if name.endswith('.aedt'):
            name = os.path.splitext(name)[0]
        # path 처리: .aedt 확장자가 있으면 그대로 사용, 없으면 path/name.aedt 형태로 만들기
        if path is None:
            path = os.getcwd()


        if path.endswith('.aedt'):
            # if path format : ~~/~~/~~/simulation.aedt
            name = os.path.splitext(os.path.basename(path))[0]
        elif path.endswith(name):
            # if path format : ~~/~~/~~/simulation
            path = path + ".aedt"
        elif not path.endswith('.aedt'):
            # if path format : ~~/~~/~~
            path = os.path.join(path, name + ".aedt")
        else:
            pass

        # 이 시점에서는 path의 format은 ~~/~~/~~/simulation.aedt 형태로 맞춰짐

        # path의 디렉토리가 없으면 생성
        project_dir = os.path.dirname(path)
        if project_dir and not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)

        if os.path.isfile(path):
            # 해당하는 파일이 이미 있다면 aedt 파일 load 동작
            if name in self.desktop.project_list: # 이미 열려있는 객체를 또 불러오는 경우
                project = self.desktop.odesktop.SetActiveProject(name)
                return project
            if forced_load is True:
                lockfile = path + ".lock"
                if os.path.exists(lockfile):
                    try: 
                        os.remove(lockfile)
                    except: 
                        try: 
                            os.chmod(lockfile, stat.S_IWRITE)
                            os.remove(lockfile)
                        except: 
                            pass
            project = self.desktop.odesktop.OpenProject(path)
        else:
            if name not in self.desktop.project_list: 
                # 해당 project가 desktop 세션 안에 없는경우 -> 새 프로젝트 생성
                project = self.desktop.odesktop.NewProject(path)
                project.SaveAs(path, True)
            else:
                # 해당 project가 desktop 세션 안에 이미 있는 경우 -> 객체만 받아옴
                project = self.desktop.odesktop.SetActiveProject(name)

        return project


    def __getattr__(self, name):
        # project class 상속
        return getattr(self.proj, name)
    
    def __dir__(self):
        default_dir = super().__dir__()
        if self.solver_instance is not None:
            return list(set(default_dir + dir(self.proj)))
        return default_dir


    def _get_project_attribute(self) -> None:
        """
        Updates project attributes (name, path, aedt_path) from the underlying project object.
        """
        # name과 path는 property이므로 private 변수에 저장
        self._name = self.GetName()
        self._path = self.GetPath()
        self.aedt_path = os.path.join(self._path, self._name + ".aedt")

    
    def save_project(self, path: Optional[str] = None) -> None:
        """
        Saves the project to the specified path.
        
        Args:
            path: Path where to save the project. If None, saves to current directory.
        """
        if path is None:
            path = os.path.join(os.getcwd(), self.name + ".aedt")
        else:
            path = os.path.normpath(os.path.abspath(path))  # OS compatibility

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


    def delete_project(self) -> None:
        """
        Deletes the project files (.aedt, .aedt.lock, .aedtresults folder).
        """
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


    def _remove_readonly(self, func, path: str, excinfo) -> None:
        """
        Helper function to remove readonly attribute from files during deletion.
        
        Args:
            func: Function to retry after removing readonly attribute.
            path: Path to the file/directory.
            excinfo: Exception information.
        """
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def delete_project_folder(self, path: Optional[str] = None, retries: int = 10, delay: float = 1.0) -> bool:
        """
        Deletes the project folder with retry mechanism.
        
        Args:
            path: Path to the project folder. If None, uses the project's current path.
            retries: Number of retry attempts.
            delay: Delay between retries in seconds.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
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


    def create_design(self, name: str, solver: str, solution: Optional[str] = None) -> pyDesign:
        """
        Creates a new design in this project.
        
        Args:
            name: Name of the design.
            solver: Solver type (e.g., "HFSS", "Maxwell 3D").
            solution: Solution name. If None, a default solution is used.
            
        Returns:
            pyDesign: The created design object.
        """
        # design = pyDesign.create_design(self, name=name, solver=solver, solution=solution)
        design = pyDesign(self, name=name, solver=solver, solution=solution)
        return design





    @property
    def designs(self) -> DesignList:
        """
        Returns a list of pyDesign objects for all designs in this project.
        Automatically updates each time it's accessed.
        
        Returns:
            DesignList: Custom list of pyDesign objects. Can be accessed by name or index.
            
        Example:
            >>> designs = project.designs
            >>> design = project.designs["HFSS_design1"]  # 이름으로 접근
            >>> design = project.designs[0]  # 인덱스로 접근
        """
        designs = DesignList()

        try:
            for design in self.project.GetDesigns():
                try:
                    design_name = design.GetName()
                    solver_type = design.GetDesignType()
                    # pyDesign은 name과 solver만 필요 (기존 design을 로드)
                    designs.append(pyDesign(self, name=design_name, solver=solver_type))
                except Exception as e:
                    # 개별 design 생성 실패 시 건너뛰기
                    print(f"Warning: Failed to create pyDesign for design: {e}")
                    continue
        except Exception as e:
            print(f"Error getting designs: {e}")
            
        return designs


    @property
    def name(self) -> str:
        """
        Returns the name of the project.
        Automatically updates each time it's accessed.
        """
        return self.project.GetName()

    
    @property
    def path(self) -> str:
        """
        Returns the path of the project.
        Automatically updates each time it's accessed.
        """
        return self.project.GetPath()
    
    @property
    def aedt_path(self) -> str:
        """
        Returns the full path to the .aedt file.
        Automatically updates each time it's accessed.
        """
        return os.path.join(self.path, self.name + ".aedt")

