def _setup_matplotlib_config():
    import os
    from os.path import join, dirname
    import matplotlib

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
