from pyaedt_module.solver._compat import (
    build_solver_kwargs,
    coerce_assignment_names,
    default_solution_name,
    normalize_solver_name,
)


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
