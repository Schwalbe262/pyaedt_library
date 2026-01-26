import os
import psutil
from typing import Optional
import time
from typing import Any

from ansys.aedt.core import Desktop as AEDTDesktop

from .pyproject import pyProject, ProjectList

import socket # for grpc



class pyDesktop(AEDTDesktop) :

    # 일부 Linux 환경에서 Desktop context manager의 __exit__가 블로킹되는 케이스가 있음.
    # (loop 0 성공 출력 후 다음 loop로 못 넘어가는 증상)
    # 이 클래스는 simulation_script.py의 finally에서 kill_process로 프로세스를 확실히 정리하므로,
    # context manager exit에서는 아무것도 하지 않도록 오버라이드한다.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # 예외는 숨기지 않음 (False)
        return False

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
        # PyAEDT는 프로세스 내 전역으로 Desktop 세션 캐시(_desktop_sessions)를 유지한다.
        # 반복 실행/강제 kill 이후 이 캐시가 "죽은 세션"을 가리키면, 다음 Desktop 생성 시
        # odesktop이 None인 상태로 반환되는 케이스가 생긴다.
        # (참고: ansys.aedt.core.desktop 에서 _desktop_sessions 사용)
        # 반복 실행에서 'PID None' 같은 깨진 세션 엔트리가 남아있으면 다음 Desktop이 그걸 재사용하려고 함.
        # new_desktop=True로 새 세션을 원할 때는 캐시를 강하게 비우는게 안전하다.
        self._purge_dead_pyaedt_sessions(clear_all=bool(new_desktop))

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

        # PyAEDT가 "started" 로그를 찍고도 odesktop이 잠깐 None인 채로 반환되는 케이스가 있음.
        # (특히 loop로 Desktop을 반복 생성/종료할 때) 이 상태에서 EnableAutoSave를 호출하면
        # AttributeError로 바로 터지므로, odesktop이 준비될 때까지 잠깐 대기한다.
        self._wait_for_odesktop(timeout_sec=30.0)
        self.disable_autosave()


    def _wait_for_odesktop(self, timeout_sec: float = 30.0, poll_sec: float = 0.2) -> None:
        """Wait until `self.odesktop` is available or raise RuntimeError."""
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if getattr(self, "odesktop", None) is not None:
                return
            time.sleep(poll_sec)
        raise RuntimeError("Desktop initialization failed: odesktop is None after timeout.")

    @staticmethod
    def _purge_dead_pyaedt_sessions(clear_all: bool = False) -> None:
        """
        PyAEDT 전역 세션 캐시에서 '죽은 PID'를 가진 항목을 제거합니다.
        구현은 버전에 따라 달라질 수 있어, 안전하게 best-effort로 수행합니다.

        관련 코드: https://github.com/ansys/pyaedt/blob/main/src/ansys/aedt/core/desktop.py
        """
        try:
            from ansys.aedt.core.internal.desktop_sessions import _desktop_sessions  # type: ignore
        except Exception:
            return

        # _desktop_sessions가 dict-like이거나, 커스텀 매니저일 수 있음
        def extract_pid(v: Any) -> Optional[int]:
            for key in ("aedt_process_id", "pid", "process_id"):
                try:
                    pid = getattr(v, key, None)
                    if isinstance(pid, int) and pid > 0:
                        return pid
                except Exception:
                    pass
                try:
                    if isinstance(v, dict):
                        pid = v.get(key)
                        if isinstance(pid, int) and pid > 0:
                            return pid
                except Exception:
                    pass
            return None

        # 강제 clear 요청이면 무조건 비운다 (new_desktop 반복 실행 안정화 목적)
        if clear_all:
            try:
                _desktop_sessions.clear()  # type: ignore[attr-defined]
            except Exception:
                pass
            return

        # dict이면 항목별로 prune
        try:
            items = list(_desktop_sessions.items())  # type: ignore[attr-defined]
            for k, v in items:
                pid = extract_pid(v)
                # pid가 없거나 죽어있으면 다음 init에서 재사용하면 안 됨 -> 제거
                if pid is None or not psutil.pid_exists(pid):
                    try:
                        del _desktop_sessions[k]  # type: ignore[index]
                    except Exception:
                        pass
            return
        except Exception:
            pass

        # 그 외엔 clear 시도
        try:
            _desktop_sessions.clear()  # type: ignore[attr-defined]
        except Exception:
            pass



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
            # AEDT는 자식 프로세스를 여러 개 띄울 수 있어, 부모만 죽이면 리소스(UDS/lock)가 남을 수 있음.
            # 가능한 한 프로세스 트리를 먼저 정리한다.
            try:
                children = proc.children(recursive=True)
                for c in children:
                    try:
                        c.kill()
                    except Exception:
                        pass
                for c in children:
                    try:
                        c.wait(timeout=5)
                    except Exception:
                        pass
            except Exception:
                pass
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



