from IPython.core.magic import Magics, line_cell_magic, magics_class


@magics_class
class QlMagics(Magics):
    def __init__(self, project, shell=None, **kwargs):
        self.project = project
        super().__init__(shell, **kwargs)

    @line_cell_magic
    def ql(self, line, cell=None):
        if cell is None:
            return self.project.ql(line).df(format=True)
        return self.project.ql(cell).df(format=True)
