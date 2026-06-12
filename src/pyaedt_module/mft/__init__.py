"""Reusable MFT helpers built on top of pyaedt_module."""

from .parameters import (
    DEFAULT_PARAMETER_COLUMNS,
    create_input_parameter,
    derive_parameters,
    get_random_value,
    set_design_variables,
    validation_check,
)
from .modeling import create_coil, create_coil_section, create_core
from .reports import (
    get_convergence_report,
    get_icepak_calculator_parameter,
    get_input_parameter,
    get_maxwell_calculator_parameter,
    get_maxwell_magnetic_parameter,
)
from .runner import create_simulation_name, save_geometry_views, save_results_to_csv

__all__ = [
    "DEFAULT_PARAMETER_COLUMNS",
    "create_input_parameter",
    "derive_parameters",
    "get_random_value",
    "set_design_variables",
    "validation_check",
    "create_coil",
    "create_coil_section",
    "create_core",
    "get_convergence_report",
    "get_icepak_calculator_parameter",
    "get_input_parameter",
    "get_maxwell_calculator_parameter",
    "get_maxwell_magnetic_parameter",
    "create_simulation_name",
    "save_geometry_views",
    "save_results_to_csv",
]
