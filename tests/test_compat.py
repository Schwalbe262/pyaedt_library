from pyaedt_module.solver._compat import (
    build_maxwell_matrix_schema,
    build_solver_kwargs,
    coerce_assignment_names,
    default_solution_name,
    normalize_solver_name,
)
from pyaedt_module.core.pydesign import pyDesign


class FakeDesktop:
    aedt_process_id = 1234
    port = 50051
    machine = "localhost"
    non_graphical = True


class Named:
    def __init__(self, name):
        self.name = name


def test_solver_name_and_default_solution():
    assert normalize_solver_name("maxwell3d") == "Maxwell 3D"
    assert normalize_solver_name("Circuit Design") == "Circuit Design"
    assert default_solution_name("Maxwell 2D") == "Magnetostatic"
    assert default_solution_name("HFSS", "DrivenModal") == "DrivenModal"


def test_build_solver_kwargs_prefers_pyaedt_1_names():
    params = {
        "project",
        "design",
        "solution_type",
        "new_desktop",
        "close_on_exit",
        "aedt_process_id",
        "port",
        "machine",
        "non_graphical",
    }
    kwargs = build_solver_kwargs(
        params,
        desktop=FakeDesktop(),
        project_name="Project1",
        design_name="Design1",
        solution_type="AC Magnetic",
    )
    assert kwargs == {
        "project": "Project1",
        "design": "Design1",
        "solution_type": "AC Magnetic",
        "aedt_process_id": 1234,
        "port": 50051,
        "machine": "localhost",
        "non_graphical": True,
        "new_desktop": False,
        "close_on_exit": False,
    }


def test_coerce_assignment_names_accepts_objects_strings_and_dicts():
    assert coerce_assignment_names("W1") == ["W1"]
    assert coerce_assignment_names([Named("W1"), "W2"]) == ["W1", "W2"]
    assert coerce_assignment_names({"group": [Named("W1"), "W2"]}) == {"group": ["W1", "W2"]}


def test_legacy_matrix_adapter_builds_pyaedt_1_schema():
    matrix = build_maxwell_matrix_schema(["Tx", Named("Rx")], "Matrix", "AC Magnetic")

    assert type(matrix).__name__ == "MatrixACMagnetic"
    assert matrix.matrix_name == "Matrix"
    assert [source.name for source in matrix.signal_sources] == ["Tx", "Rx"]


def test_legacy_matrix_adapter_uses_magnetostatic_schema():
    matrix = build_maxwell_matrix_schema(["Mag1"], "Matrix", "Magnetostatic")

    assert type(matrix).__name__ == "MatrixMagnetostatic"
    assert [source.name for source in matrix.signal_sources] == ["Mag1"]
    assert matrix.group_sources == []


def test_set_setup_properties_accepts_legacy_display_names():
    class FakeSetup:
        def __init__(self):
            self.props = {
                "MaximumPasses": 6,
                "MinimumPasses": 1,
                "MinimumConvergedPasses": 1,
                "PercentError": 1,
                "Frequency": "60Hz",
            }
            self.updated = False

        def update(self):
            self.updated = True

    design = object.__new__(pyDesign)
    design.setup = FakeSetup()

    design.set_setup_properties(
        properties={
            "Max. Number of Passes": 12,
            "Min. Number of Passes": 2,
            "Min. Converged Passes": 3,
            "Percent Error": 2.5,
            "Frequency Setup": "20kHz",
        }
    )

    assert design.setup.props["MaximumPasses"] == 12
    assert design.setup.props["MinimumPasses"] == 2
    assert design.setup.props["MinimumConvergedPasses"] == 3
    assert design.setup.props["PercentError"] == 2.5
    assert design.setup.props["Frequency"] == "20kHz"
    assert design.setup.updated is True


def test_variable_getitem_accepts_pyaedt_expression_objects():
    class FakeVariable:
        expression = "20kHz"

    class FakeVariableManager:
        independent_variables = {"frequency": FakeVariable()}

    class FakeSolver:
        variable_manager = FakeVariableManager()

    design = object.__new__(pyDesign)
    design.solver_instance = FakeSolver()
    design._store = {}

    assert design["frequency"] == "20kHz"
