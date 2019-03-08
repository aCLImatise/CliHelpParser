import jinja2
from declivity import model


def get_env() -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('declivity', 'converter'),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
    )

    env.filters['synonym_to_words'] = model.Flag.synonym_to_words
    env.filters['synonym_to_snake'] = model.Flag.synonym_to_snake
    env.filters['synonym_to_camel'] = model.Flag.synonym_to_camel
    return env
