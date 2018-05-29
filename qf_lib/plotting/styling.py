def add_style_lib(lib_path: str):
    """
    Parameters
    ----------
    lib_path
        absolute path to the directory containing .mplstyle files
    """
    import matplotlib.style.core as style_core

    style_core.USER_LIBRARY_PATHS.append(lib_path)
    style_core.reload_library()
