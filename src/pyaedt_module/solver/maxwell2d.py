from ansys.aedt.core import Maxwell2d as AEDTMaxwell2d


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

        sources = assignment
        if not isinstance(sources, dict):
            sources = [item.name if hasattr(item, "name") else item for item in sources]

        return super().assign_matrix(MatrixACMagnetic(sources=sources, matrix_name=matrix_name))
