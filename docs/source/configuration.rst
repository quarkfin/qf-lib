Configuration
=============

Starting directory
------------------

Starting directory is used to turn relative paths into absolute paths.
In many places you’ll be required to specify a path which should be
relative to the starting directory. To set up starting directory one
needs to either:

- call ``set_starting_dir_abs_path("C:\abs\path\to\starting\directory")``
- set ``QF_STARTING_DIRECTORY`` environment variable and put as value path to the project. For example the path might look like this: ``C:\Users\user_name\workspace\qf-lib``

Advanced configuration - Settings files
---------------------------------------

Many components from ``qf-lib`` require the ``Settings`` object as a
dependency. To create it one needs to put in their Python code:

.. code:: python

   from qf_lib.settings import Settings


   settings_path = ...
   secret_settings_path = ...
   settings = Settings(settings_path, secret_settings_path)

where ``settings_path`` is an absolute path of your file containing
settings (JSON, described later) used by the application and the
``secret_settings_path`` which is complementary to the settings file but
contains secret data (e.g. passwords) and thus mustn’t be added to the
CVS. When ``Settings`` object is created, it:

- loads settings defined in the ``settings.json`` file
- loads settings defined in the ``secret_settings.json`` file (if the file exists)
- loads settings defined in the ``QUANTFIN_SECRET`` environment variable (if the ``secret_settings.json`` file doesn’t exist)
- merges both loaded sets of settings together.

Sample content of the ``settings.json``:

.. code:: json

   {
     "some_setting": "value of that setting",
     "another_setting": "value of another setting",
     "some_connection_settings": {
       "username": "john.smith"
     }
   }

Sample content of the ``secret_settings.json``:

.. code:: json

   {
     "some_connection_settings": {
       "password": "my_secret_pass"
     }
   }

QF-Lib used settings
--------------------

You may define your own settings and later on have them loaded into
``Settings`` object. However there are some, which are required for some
QF-Lib components to work correctly.

-  Sample settings can be found in demo configuration
   ``\qf-lib\demo_scripts\demo_configuration\config_files\demo_settings.json``
-  Sample secret settings can be found in demo configuration
   ``\qf-lib\demo_scripts\demo_configuration\config_files\demo_secret_settings.json``

.. note::
    All paths used in the settings should be relative to the
    starting directory (which can be set either by using
    ``set_starting_dir_abs_path(path)`` function or by setting
    ``QF_STARTING_DIRECTORY`` environment variable).

Common QF-Lib settings keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The table below lists keys used by built-in QF-Lib components. Paths are
relative to the starting directory. You may add custom keys; they are
exposed as attributes on the ``Settings`` object.

Provider-specific keys (``quandl_key``, ``bbg_dl``, ``hapi_credentials``, and
others) are summarised in :doc:`tutorials/working_with_data`.

.. list-table::
   :header-rows: 1
   :widths: 24 10 10 56

   * - Key
     - File
     - Required
     - Example / notes
   * - ``output_directory``
     - settings
     - yes
     - ``"output"`` - backtest reports, tearsheets, and other exports.
   * - ``company_name``
     - settings
     - no
     - ``"Sample Org Name"`` - header on PDF tearsheets.
   * - ``logo_path``
     - settings
     - no
     - ``"input/logo.jpg"`` - logo on PDF tearsheets.
   * - ``document_css_directory``
     - settings
     - no
     - ``"input/elements_css"`` - custom CSS for ``PDFExporter``; default styling if omitted.
   * - ``image_format``
     - settings
     - no
     - ``"PNG"`` or ``"SVG"`` - chart format in exported documents (default ``"PNG"``).
   * - ``bloomberg``
     - settings
     - no
     - ``{"host": "localhost", "port": 8194}`` - ``BloombergDataProvider`` (requires BLPAPI).
   * - ``haver_path``
     - settings
     - no
     - ``"C:/path/to/haver-data"`` - local Haver database for ``HaverDataProvider``.
   * - ``smtp``
     - settings
     - no
     - ``{"host": "...", "port": 587, "domain": "...", "tls": true, "sender": "..."}`` - outbound mail.
   * - ``smtp.username``, ``smtp.password``
     - secret
     - no
     - Nested under ``smtp`` in ``secret_settings.json`` (or ``QUANTFIN_SECRET``).

