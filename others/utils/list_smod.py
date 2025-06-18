import importlib
import pkgutil

def smod_imports(package_name):
    package = importlib.import_module(package_name)
    if not hasattr(package, '__path__'):
        print(f"{package_name} is not a package.")
        return

    for module_info in pkgutil.iter_modules(package.__path__):
        return f"import manim.{module_info.name}"
        