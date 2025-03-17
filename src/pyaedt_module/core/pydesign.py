from pyaedt_module.solver.hfss import HFSS
from pyaedt_module.model3d import Model3d

class pyDesign:
    def __init__(self, project, name=None, solver=None, solution=None):
        self.project = project
        self.NUM_CORE = 4
        self.name = name
        self.solver = solver.lower() if solver is not None else None
        self.solution = solution

        self.solver_instance = None 

        self._store = {}

    
    def __getattr__(self, name):
        return getattr(self.solver_instance, name)

    def __dir__(self):
        default_dir = super().__dir__()
        if self.solver_instance is not None:
            return list(set(default_dir + dir(self.solver_instance)))
        return default_dir
    
    def __getitem__(self, key):
        """변수 조회 - HFSS에 저장된 변수 또는 _store에서 가져오기"""
        if self.solver_instance and key in self.solver_instance.variable_manager.independent_variables:
            return self.solver_instance.variable_manager.independent_variables[key].value
        return self._store.get(key, None)  # HFSS가 없으면 _store에서 반환

    def __setitem__(self, key, value):
        """변수 저장 - HFSS에 직접 반영 또는 _store에 저장"""
        if self.solver_instance:
            self.solver_instance.variable_manager[key] = value  # HFSS 변수 시스템에 저장
        else:
            self._store[key] = value  # HFSS가 없으면 _store에 저장

    def __delitem__(self, key):
        """변수 삭제 - HFSS에서 삭제 또는 _store에서 삭제"""
        if self.solver_instance:
            if key in self.solver_instance.variable_manager.independent_variables:
                del self.solver_instance.variable_manager[key]
        elif key in self._store:
            del self._store[key]

    def __iter__(self):
        """변수 목록을 반환 (HFSS 또는 _store)"""
        if self.solver_instance:
            return iter(self.solver_instance.variable_manager.independent_variables)
        return iter(self._store)

    def __len__(self):
        """저장된 변수 개수 반환"""
        if self.solver_instance:
            return len(self.solver_instance.variable_manager.independent_variables)
        return len(self._store)

    def __repr__(self):
        return f"pyDesign(name={self.name}, solver={self.solver}, solution={self.solution}, store={self._store})"


    @classmethod
    def create_design(cls, project, name=None, solver=None, solution=None):
        design = cls(project, name=name, solver=solver, solution=solution)

        solver = solver.lower()
        if solver == "hfss":
            design._setup_hfss()
        
        return design

    def _setup_hfss(self):
        if self.solution is None:
            self.solution = "HFSS Terminal Network"
        # self.project.InsertDesign("HFSS", self.name, self.solution, "")
        # self.solver_instance = self.project.SetActiveDesign(self.name)

        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        self.solver_instance = HFSS(project=None, design=self.name, solution_type=self.solution)

        self._get_module()
        

    def _get_module(self):
        self.model3d = Model3d(self)

