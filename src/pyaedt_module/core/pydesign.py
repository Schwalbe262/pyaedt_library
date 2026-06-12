import inspect
import re

import numpy as np

from pyaedt_module.model3d import Model3d
from pyaedt_module.solver._compat import (
    build_solver_kwargs,
    default_solution_name,
    normalize_solver_name,
)
from pyaedt_module.solver.circuit import Circuit
from pyaedt_module.solver.hfss import HFSS
from pyaedt_module.solver.icepak import Icepak
from pyaedt_module.solver.maxwell2d import Maxwell2d
from pyaedt_module.solver.maxwell3d import Maxwell3d

from .post_processing import PostProcessing


class VariableWrapper(str):
    """String variable value with a helper for extracting its numeric prefix."""

    def value(self):
        match = re.match(r"^([-\d\.eE+]+)", self.strip())
        if not match:
            return self
        try:
            return float(match.group(1))
        except Exception:
            return self


class DesignList(list):
    """List that also supports lookup by design name."""

    def _get_design_name(self, design):
        if hasattr(design, "solver_instance") and design.solver_instance:
            design_name = getattr(design.solver_instance, "design_name", None)
            if design_name:
                return design_name
        return getattr(design, "name", None)

    def __getitem__(self, key):
        if isinstance(key, str):
            for design in self:
                if self._get_design_name(design) == key:
                    return design
            raise KeyError(f"Design '{key}' not found")
        return super().__getitem__(key)


SETUP_PROPERTY_ALIASES = {
    "Max. Number of Passes": ("MaximumPasses", "Max. Number of Passes"),
    "Min. Number of Passes": ("MinimumPasses", "Min. Number of Passes"),
    "Min. Converged Passes": ("MinimumConvergedPasses", "Min. Converged Passes"),
    "Percent Error": ("PercentError", "Percent Error"),
    "Frequency Setup": ("Frequency", "Frequency Setup"),
}


class pyDesign:
    def __init__(self, project, name=None, solver=None, solution=None):
        self.project = project
        self.NUM_CORE = 4
        self._store = {}

        self.solver_instance = self._pydesign(project, name, solver, solution)
        if self.solver_instance is None:
            raise RuntimeError(
                f"Failed to create solver instance for design '{name}' with solver '{solver}'. "
                "Please check if the solver type is valid and the project is initialized."
            )

        if not hasattr(self.solver_instance, "_py_design"):
            self.solver_instance._py_design = self

        self._get_module()

    @classmethod
    def create_design(cls, project, name=None, solver=None, solution=None):
        return cls(project, name=name, solver=solver, solution=solution)

    def _pydesign(self, project, name, solver, solution):
        solver = self._solver_name(solver)
        solution = self._solution_name(solver, solution)

        if solver == "HFSS":
            return self._setup_hfss(name, solution)
        if solver == "Maxwell 3D":
            return self._setup_maxwell3d(name, solution)
        if solver == "Maxwell 2D":
            return self._setup_maxwell2d(name, solution)
        if solver == "Icepak":
            return self._setup_icepak(name, solution)
        if solver == "Circuit Design":
            return self._setup_circuit(name, solution)
        raise ValueError(f"Invalid solver: {solver}")

    def _solver_name(self, solver):
        return normalize_solver_name(solver)

    def _solution_name(self, solver, solution):
        return default_solution_name(solver, solution)

    def _set_active_project(self):
        self.project.desktop.odesktop.SetActiveProject(self.project.name)

    def _setup_maxwell3d(self, name, solution):
        self._set_active_project()
        solver_instance = self._instantiate_solver(Maxwell3d, design_name=name, solution_type=solution)
        solver_instance.design = self
        return solver_instance

    def _setup_maxwell(self, name, solution):
        return self._setup_maxwell3d(name, solution)

    def _setup_maxwell2d(self, name, solution):
        self._set_active_project()
        solver_instance = self._instantiate_solver(Maxwell2d, design_name=name, solution_type=solution)
        solver_instance.design = self
        return solver_instance

    def _setup_hfss(self, name, solution):
        self._set_active_project()
        solver_instance = self._instantiate_solver(HFSS, design_name=name, solution_type=solution)
        solver_instance.design = self
        return solver_instance

    def _setup_circuit(self, name, solution):
        self._set_active_project()
        solver_instance = self._instantiate_solver(Circuit, design_name=name, solution_type=solution)
        solver_instance.design = self
        return solver_instance

    def _setup_icepak(self, name, solution):
        self._set_active_project()
        solver_instance = self._instantiate_solver(Icepak, design_name=name, solution_type=solution)
        solver_instance.design = self
        return solver_instance

    def _instantiate_solver(self, solver_cls, design_name: str, solution_type=None):
        desktop = self.project.desktop
        try:
            project_name = self.project.project.GetName()
        except Exception:
            project_name = getattr(self.project, "name", None)

        base_init = None
        for cls in solver_cls.__mro__:
            if cls is solver_cls:
                continue
            if "__init__" in cls.__dict__:
                base_init = cls.__init__
                break
        if base_init is None:
            base_init = solver_cls.__init__

        try:
            params = set(inspect.signature(base_init).parameters.keys())
        except Exception:
            params = set()

        kwargs = build_solver_kwargs(
            params,
            desktop=desktop,
            project_name=project_name,
            design_name=design_name,
            solution_type=solution_type,
        )
        return solver_cls(**kwargs)

    def _get_module(self):
        self.model3d = Model3d(self)
        self.post_processing = PostProcessing(self)

    def __getattr__(self, name):
        if self.solver_instance:
            try:
                return getattr(self.solver_instance, name)
            except AttributeError:
                try:
                    odesign = getattr(self.solver_instance, "odesign", None)
                    if odesign:
                        return getattr(odesign, name)
                except (AttributeError, TypeError):
                    pass

        value = self[name]
        if value is not None:
            return value
        raise AttributeError(f"'pyDesign' object and its solver have no attribute or variable '{name}'")

    def __dir__(self):
        default_dir = super().__dir__()
        if self.solver_instance is not None:
            return list(set(default_dir + dir(self.solver_instance)))
        return default_dir

    def _variable_manager(self):
        if not self.solver_instance:
            return None
        return getattr(self.solver_instance, "variable_manager", None)

    def __getitem__(self, key):
        variable_manager = self._variable_manager()
        if variable_manager is not None:
            independent_variables = getattr(variable_manager, "independent_variables", {})
            if key in independent_variables:
                variable = independent_variables[key]
                for attr in ("value", "expression"):
                    if hasattr(variable, attr):
                        return getattr(variable, attr)
                return str(variable)
        return self._store.get(key)

    def __setitem__(self, key, value):
        variable_manager = self._variable_manager()
        if variable_manager is not None:
            variable_manager[key] = value
        self._store[key] = value
        return value

    def __delitem__(self, key):
        variable_manager = self._variable_manager()
        if variable_manager is not None:
            independent_variables = getattr(variable_manager, "independent_variables", {})
            if key in independent_variables:
                del variable_manager[key]
        if key in self._store:
            del self._store[key]

    def __iter__(self):
        variable_manager = self._variable_manager()
        if variable_manager is not None:
            return iter(getattr(variable_manager, "independent_variables", {}))
        return iter(self._store)

    def __len__(self):
        variable_manager = self._variable_manager()
        if variable_manager is not None:
            return len(getattr(variable_manager, "independent_variables", {}))
        return len(self._store)

    def __repr__(self):
        return f"pyDesign(name={self.name}, solver={self.solver}, solution={self.solution}, store={self._store})"

    def get_random_value(self, lower=None, upper=None, resolution=None):
        resolution_str = str(resolution)
        precision = len(resolution_str.split(".")[1]) if "." in resolution_str else 0
        possible_values = np.arange(lower, upper + resolution, resolution)
        value = round(np.random.choice(possible_values), precision)
        return int(value) if resolution == 1 else float(value)

    def random_variable(self, variable_name=None, lower=None, upper=None, resolution=None, unit=""):
        unit = "" if unit is None else unit
        value = self.get_random_value(lower, upper, resolution)
        if variable_name is not None:
            self[variable_name] = f"{value}{unit}"
        return value

    def set_variable(self, variable_name=None, value=None, unit=""):
        if variable_name is not None:
            self[variable_name] = f"{value}{unit}"
        return value

    def set_variables(self, variables, units=None):
        units = units or {}
        for variable_name, value in variables.items():
            self.set_variable(variable_name=variable_name, value=value, unit=units.get(variable_name, ""))
        return variables

    def get_variable(self, variable_name, default=None):
        value = self[variable_name]
        return default if value is None else value

    def get_variable_value(self, variable_name, default=None):
        value = self.get_variable(variable_name, default=default)
        if value is default:
            return default
        return VariableWrapper(str(value)).value()

    def set_setup_properties(self, setup=None, properties=None, update=True, **kwargs):
        """Set setup properties using PyAEDT 1.x names or legacy display names."""
        setup = setup or getattr(self, "setup", None)
        if setup is None:
            raise ValueError("setup must be provided or assigned to design.setup")

        setup_props = getattr(setup, "props", None)
        if setup_props is None:
            setup_props = getattr(setup, "properties", None)
        if setup_props is None:
            raise AttributeError("setup object has neither props nor properties")

        values = {}
        if properties:
            values.update(properties)
        values.update(kwargs)

        for key, value in values.items():
            candidates = SETUP_PROPERTY_ALIASES.get(key, (key,))
            target = next((candidate for candidate in candidates if candidate in setup_props), candidates[0])
            setup_props[target] = value

        if update and hasattr(setup, "update"):
            setup.update()
        return setup

    def get_active_design(self):
        active_design = self.project.desktop.active_design()
        design_name = active_design.GetName()
        design_type = active_design.GetDesignType()
        solution_type = active_design.GetSolutionType()

        if design_type == "Icepak":
            return pyDesign.create_design(self.project, name=design_name, solver="icepak", solution=solution_type)
        if design_type == "Maxwell 3D":
            return pyDesign.create_design(self.project, name=design_name, solver="maxwell3d", solution=solution_type)
        if design_type == "Maxwell 2D":
            return pyDesign.create_design(self.project, name=design_name, solver="maxwell2d", solution=solution_type)
        if design_type == "HFSS":
            return pyDesign.create_design(self.project, name=design_name, solver="hfss", solution=solution_type)
        return False

    def delete_mesh(self, mesh_obj):
        mesh_module = self.odesign.GetModule("MeshSetup")
        meshes = mesh_obj if isinstance(mesh_obj, list) else [mesh_obj]
        for mesh in meshes:
            if isinstance(mesh, str):
                mesh_module.DeleteOp([mesh])
            elif isinstance(getattr(mesh, "name", None), str):
                mesh_module.DeleteOp([mesh.name])
            else:
                raise ValueError("mesh_obj must be a mesh object or mesh name")

    def get_excitation(self, excitation_name=None):
        if excitation_name is None:
            return []
        if isinstance(excitation_name, str):
            if excitation_name in self.excitation_objects:
                return self.excitation_objects[excitation_name]
            raise ValueError(f"Excitation '{excitation_name}' not found")

        excitations = []
        for name in excitation_name:
            if name not in self.excitation_objects:
                raise ValueError(f"Excitation '{name}' not found")
            excitations.append(self.excitation_objects[name])
        return excitations

    @property
    def variables(self) -> dict[str, VariableWrapper]:
        variables = {}
        if self.solver_instance and getattr(self.solver_instance, "odesign", None):
            for var_name in self.solver_instance.odesign.GetVariables():
                variables[var_name] = VariableWrapper(self.solver_instance.odesign.GetVariableValue(var_name))
        for var_name, value in self._store.items():
            variables.setdefault(var_name, VariableWrapper(str(value)))
        return variables

    @property
    def name(self):
        return self.GetName()

    @property
    def solver(self):
        return self.GetDesignType()

    @property
    def solution(self):
        return self.GetSolutionType()
