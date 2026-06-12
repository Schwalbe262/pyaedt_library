"""Compatibility helpers for PyAEDT application wrappers."""


SOLVER_ALIASES = {
    "hfss": "HFSS",
    "maxwell3d": "Maxwell 3D",
    "maxwell2d": "Maxwell 2D",
    "icepak": "Icepak",
    "mechanical": "Mechanical",
    "circuit": "Circuit Design",
    "circuitdesign": "Circuit Design",
}

DEFAULT_SOLUTIONS = {
    "HFSS": "HFSS Terminal Network",
    "Maxwell 3D": "Magnetostatic",
    "Maxwell 2D": "Magnetostatic",
    "Icepak": "SteadyState TemperatureAndFlow",
    "Mechanical": "",
    "Circuit Design": "None",
}


def normalize_solver_name(solver):
    if solver is None:
        return "Maxwell 3D"
    normalized = str(solver).lower().replace(" ", "")
    return SOLVER_ALIASES.get(normalized, solver)


def default_solution_name(solver, solution=None):
    if solution is not None:
        return solution
    return DEFAULT_SOLUTIONS.get(solver)


def _set_first_supported(kwargs, params, candidates, value, *, skip_none=True):
    if skip_none and value is None:
        return
    for candidate in candidates:
        if candidate in params:
            kwargs[candidate] = value
            return


def build_solver_kwargs(params, *, desktop, project_name, design_name, solution_type=None):
    """Build constructor kwargs accepted by the detected PyAEDT app signature.

    PyAEDT 1.0 uses ``project`` and ``design``. Older versions used names such
    as ``projectname`` and ``designname``. This helper keeps our wrapper logic
    explicit and testable.
    """
    kwargs = {}

    _set_first_supported(kwargs, params, ("project", "projectname", "project_name"), project_name)
    _set_first_supported(kwargs, params, ("design", "designname", "design_name"), design_name)
    _set_first_supported(kwargs, params, ("solution_type", "solution"), solution_type)

    if "desktop" in params:
        kwargs["desktop"] = desktop

    pid = getattr(desktop, "aedt_process_id", None)
    if pid is None:
        pid = getattr(desktop, "pid", None)
    _set_first_supported(kwargs, params, ("aedt_process_id",), pid)

    port = getattr(desktop, "port", None)
    if port is None:
        port = getattr(desktop, "grpc_port", None)
    _set_first_supported(kwargs, params, ("port",), port)

    machine = getattr(desktop, "machine", None)
    _set_first_supported(kwargs, params, ("machine",), machine)

    non_graphical = getattr(desktop, "non_graphical", None)
    _set_first_supported(kwargs, params, ("non_graphical",), non_graphical)

    _set_first_supported(
        kwargs,
        params,
        ("new_desktop", "new_desktop_session", "new_session", "AlwaysNew", "always_new"),
        False,
        skip_none=False,
    )
    _set_first_supported(
        kwargs,
        params,
        ("close_on_exit", "release_on_exit"),
        False,
        skip_none=False,
    )

    return kwargs


def coerce_assignment_names(assignment):
    """Return assignment names while accepting AEDT objects, strings, or dicts."""
    if isinstance(assignment, dict):
        return {
            key: [item.name if hasattr(item, "name") else item for item in value]
            if isinstance(value, (list, tuple, set))
            else value.name if hasattr(value, "name")
            else value
            for key, value in assignment.items()
        }
    if isinstance(assignment, str):
        return [assignment]
    return [item.name if hasattr(item, "name") else item for item in assignment]
