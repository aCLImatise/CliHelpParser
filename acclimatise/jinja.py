"""
Utilities for producing workflow wrappers using jinja templates
"""
import jinja2
from acclimatise import model


def get_env() -> jinja2.Environment:
    """
    Returns a Jinja2 environment with some helpful filters
    :return:
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader("acclimatise", "converter"),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )

    return env
