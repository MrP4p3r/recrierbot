import os
import jinja2

_templates_path = os.path.join(os.path.dirname(__file__), 'templates')
_env = jinja2.Environment(loader=jinja2.FileSystemLoader(_templates_path))


def render(template_path: str, data: dict):
    template_path = template_path + '.j2'
    return _env.get_template(template_path).render(data=data)
