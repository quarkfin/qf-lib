from os.path import abspath, dirname


def _get_environment():
    from jinja2 import Environment, FileSystemLoader
    templates_dir_abs_path = dirname(abspath(__file__))
    templates_loader = FileSystemLoader(templates_dir_abs_path)
    return Environment(loader=templates_loader)


environment = _get_environment()
