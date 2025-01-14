Configuration
=============

Starting directory
------------------

Starting directory is used to turn relative paths into absolute paths.
In many places you’ll be required to specify a path which should be
relative to the starting directory. To set up starting directory one
needs to either: - call
``set_starting_dir_abs_path("C:\abs\path\to\starting\directory")`` - or
set ``QF_STARTING_DIRECTORY`` environment variable and put as value path
to the project. - For example the path might look like this:
``C:\Users\user_name\workspace\qf-lib``

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
contains secret data (e.g. passwords) and thus mustn’t be added to the
CVS. When ``Settings`` object is created, it: - loads settings defined
in the ``settings.json`` file - loads settings defined in the
``secret_settings.json`` file (if the file exists) - loads settings
defined in the ``QUANTFIN_SECRET`` environment variable (if the
``secret_settings.json`` file doesn’t exist) - merges both loaded sets
of settings together.

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

NOTICE: all paths used in the settings should be relative to the
starting directory. (which can be set either by using
``set_starting_dir_abs_path(path)`` function or by setting
``QF_STARTING_DIRECTORY`` environment variable)

Below you’ll find a list of examples that can be put into settings

**company_name and logo_path (optional)**

``settings.json``:

.. code:: json

       "company_name": "Sample Org Name",
       "logo_path": "path/to/logo.jpg"

Used by components producing tearsheets (in a form of PDFs). The company
name and a logo is put in the header of those tearsheets.

**document_css_directory (optional)**

``settings.json``:

.. code:: json

       "document_css_directory": "input/elements_css"

Setting used by the ``PDFExporter`` component to style the elements put
in PDFs (e.g. tables, paragraphs, etc.). If ``document_css_directory``
is not specified then the default style will be applied.

**bloomberg (optional)**

``settings.json``:

.. code:: json

     "bloomberg": {
       "host": "localhost",
       "port": 8194
     }

Used by the ``BloombergDataProvider``. To have this component running,
first you need to have a Bloomberg subscription. Then you need to have
the BLPAPI running somewhere. Then you need to specify where the API is
running by specifying its host and port.

**output_directory**

``settings.json``:

.. code:: json

     "output_directory": "output"

A relative path to the directory into which different components will
put their output (e.g. generated tearsheets).
