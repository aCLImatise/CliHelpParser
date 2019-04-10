"""
Utilities for producing workflow wrappers using jinja templates
"""
import jinja2
from declivity import model


def get_env() -> jinja2.Environment:
    """
    Returns a Jinja2 environment with some helpful filters
    :return:
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('declivity', 'converter'),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
    )

    return env
