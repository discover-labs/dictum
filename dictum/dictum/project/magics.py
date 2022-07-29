from IPython.core.magic import Magics, line_cell_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring


@magics_class
class QlMagics(Magics):
    def __init__(self, project, shell=None, **kwargs):
        super().__init__(shell=shell, **kwargs)
        self.project = project

    @line_cell_magic("ql")
    @magic_arguments()
    @argument(
        "-r",
        "--result",
        default=None,
        action="store",
        help="Store the resulting dataframe in a local variable",
    )
    @argument(
        "-f",
        "--format-result",
        action="store_true",
        default=False,
        help="Format the result returned to a local variable",
    )
    @argument(
        "-n",
        "--no-formatting",
        action="store_true",
        default=False,
        help="Display the result without formatting",
    )
    @argument(
        "query",
        default=None,
        action="store",
        nargs="*",  # the rest is query
    )
    def ql(self, line, cell=None):
        args = parse_argstring(self.ql, line)
        format = not args.no_formatting

        query = cell
        if cell is None:
            query = " ".join(args.query)

        if args.result is not None:
            result = self.project.ql(query).df(format=args.format_result)
            self.shell.user_ns.update({args.result: result})
            print(f"Returned {result.shape[0]} rows to {args.result}")
            return  # don't show the result in Jupiter

        result = self.project.ql(query).df(format=format)
        return result
