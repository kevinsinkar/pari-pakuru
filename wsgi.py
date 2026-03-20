"""
PythonAnywhere WSGI entry point.

In PythonAnywhere's Web tab, set the WSGI file path to:
    /home/<username>/pari-pakuru/wsgi.py

And configure:
    Source code:       /home/<username>/pari-pakuru
    Working directory: /home/<username>/pari-pakuru
    Static files:      URL /static/  -> /home/<username>/pari-pakuru/web/static

The database (skiri_pawnee.db) must be uploaded separately to the
project root since it is not tracked in git.
"""

import os
import sys

# Project root = directory containing this file
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Point the app at the database in project root
os.environ.setdefault("SKIRI_DB_PATH", os.path.join(project_root, "skiri_pawnee.db"))

from web.app import app as application  # noqa: E402
