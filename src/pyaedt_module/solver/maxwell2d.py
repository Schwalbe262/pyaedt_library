from ansys.aedt.core import Maxwell2d as AEDTMaxwell2d

from ._compat import build_maxwell_matrix_schema, get_solution_type


class Maxwell2d(AEDTMaxwell2d):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.design = None
        self.report_list = {}

    def assign_matrix(self, args=None, matrix_name=None, assignment=None, **kwargs):
        if args is not None:
            return super().assign_matrix(args)

        if assignment is None:
            assignment = kwargs.pop("assignment", None)
        if assignment is None:
            assignment = kwargs.pop("sources", None)
        if matrix_name is None:
            matrix_name = kwargs.pop("matrix_name", "Matrix")

        if assignment is None:
            return super().assign_matrix(**kwargs)

        return super().assign_matrix(
            build_maxwell_matrix_schema(
                assignment=assignment,
                matrix_name=matrix_name,
                solution_type=get_solution_type(self),
            )
        )
