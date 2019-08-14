#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

def _setup_matplotlib_config():
    from os.path import join, dirname

    import matplotlib.pyplot as plt
    import matplotlib.style.core as style_core

    this_dir = dirname(__file__)
    style_lib_dir = join(this_dir, "stylelib")

    # that is pretty dirty but I've found no other way to set your own config directory
    # (why there is no matplotlib function like set_config_dir() or add_config_dir() ?!)
    style_core.USER_LIBRARY_PATHS = [join(style_lib_dir)]
    style_core.reload_library()

    plt.style.use('qfstyle')


_setup_matplotlib_config()
