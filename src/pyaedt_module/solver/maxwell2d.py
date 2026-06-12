from ansys.aedt.core import Maxwell2d as AEDTMaxwell2d

from ._compat import coerce_assignment_names


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

        from ansys.aedt.core.modules.boundary.maxwell_boundary import MatrixACMagnetic

        return super().assign_matrix(
            MatrixACMagnetic(sources=coerce_assignment_names(assignment), matrix_name=matrix_name)
        )
