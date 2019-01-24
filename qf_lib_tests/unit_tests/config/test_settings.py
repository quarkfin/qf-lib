from os.path import join

from qf_lib.get_sources_root import get_src_root
from qf_lib.settings import Settings


def get_test_settings() -> Settings:
    config_dir = join(get_src_root(), 'qf_lib_tests', 'unit_tests', 'config')
    test_settings_path = join(config_dir, 'test_settings.json')
    secret_test_settings_path = join(config_dir, 'secret_test_settings.json')

    return Settings(test_settings_path, secret_test_settings_path)
