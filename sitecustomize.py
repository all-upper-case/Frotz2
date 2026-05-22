"""Automatically attach Phone Dev routes when the Replit app imports main.py.

Python imports sitecustomize at interpreter startup when it is present on
sys.path. Gunicorn still imports main:app normally, but this import hook
registers devtools_bp immediately after main.py finishes loading.
"""
import importlib.abc
import importlib.machinery
import sys


class _MainDevtoolsLoader(importlib.abc.Loader):
    def __init__(self, original_loader):
        self.original_loader = original_loader

    def create_module(self, spec):
        if hasattr(self.original_loader, "create_module"):
            return self.original_loader.create_module(spec)
        return None

    def exec_module(self, module):
        self.original_loader.exec_module(module)
        app = getattr(module, "app", None)
        if app is None or "devtools" in getattr(app, "blueprints", {}):
            return
        from devtools import devtools_bp
        app.register_blueprint(devtools_bp)


class _MainDevtoolsFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname != "main":
            return None

        try:
            sys.meta_path.remove(self)
            spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        finally:
            sys.meta_path.insert(0, self)

        if spec and spec.loader:
            spec.loader = _MainDevtoolsLoader(spec.loader)
        return spec


if not any(isinstance(finder, _MainDevtoolsFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, _MainDevtoolsFinder())
