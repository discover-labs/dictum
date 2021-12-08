def repr_expr_constant(val):
    if isinstance(val, str):
        return f"'{val}'"
    return str(val)
