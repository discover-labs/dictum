import json
import subprocess
import tempfile
from functools import wraps
from pathlib import Path

import altair as alt

altair_output = Path(__file__).parent / "altair_output"


def save_result(fn, name: str):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        result = fn(*args, **kwargs)
        if isinstance(result, alt.TopLevelMixin):
            with tempfile.NamedTemporaryFile(mode="w") as fp:
                json.dump(result._rendered_dict(), fp)
                png = altair_output / f"{name}.png"
                fp.flush()
                subprocess.check_call(
                    [
                        "npx",
                        "-p",
                        "vega",
                        "-p",
                        "vega-lite",
                        "-p",
                        "vega-cli",
                        "vl2png",
                        fp.name,
                        str(png),
                    ]
                )
        return result

    return wrapped


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        item.obj = save_result(item.obj, item.name)
