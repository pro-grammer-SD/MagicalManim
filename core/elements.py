import inspect
import importlib
import pkgutil
import manim

def get_exposed_classes(package_name: str = "manim"):
    package = importlib.import_module(package_name)
    classes = set()
    visited = set()

    def walk_module(mod):
        if mod in visited:
            return
        visited.add(mod)
        for attr_name in dir(mod):
            if attr_name.startswith("_"):
                continue
            try:
                attr = getattr(mod, attr_name)
                if inspect.isclass(attr):
                    classes.add(attr)
                elif inspect.ismodule(attr) and attr.__name__.startswith(package_name):
                    walk_module(attr)
            except Exception:
                continue

    walk_module(package)

    for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            mod = importlib.import_module(name)
            walk_module(mod)
        except Exception:
            continue

    return list(classes)

def get_class_init_params(cls):
    props = {}
    try:
        sig = inspect.signature(cls)
    except (TypeError, ValueError):
        return props

    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        param_type = (
            param.annotation.__name__
            if hasattr(param.annotation, "__name__")
            else str(param.annotation)
            if param.annotation is not inspect.Parameter.empty
            else "str"
        )
        default = (
            param.default if param.default is not inspect.Parameter.empty else ""
        )
        props[name] = {"type": param_type, "default": default}
    return props

def is_mobject_class(cls):
    try:
        return issubclass(cls, manim.mobject.mobject.Mobject)
    except Exception:
        return False

def class_in_manim_animations(class_name: str) -> bool:
    try:
        manim_animations = importlib.import_module("manim.animation")
        for _, modname, _ in pkgutil.walk_packages(
            manim_animations.__path__, manim_animations.__name__ + "."
        ):
            try:
                module = importlib.import_module(modname)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if name == class_name:
                        return True
            except Exception:
                continue
    except Exception:
        return False
    return False
