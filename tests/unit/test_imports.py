"""Every package module imports on the CPU core install.

Guards against silent breakage in modules no other test touches (the ES
refactor removed SPELL_FR and broke ext/codeswitch.py unnoticed). Optional
model dependencies are imported inside functions, so this needs no GPU.
"""

import importlib
import pkgutil

import voxentity_eu


def test_all_modules_import():
    names = [m.name for m in pkgutil.walk_packages(voxentity_eu.__path__, "voxentity_eu.")]
    assert len(names) > 30
    for name in names:
        importlib.import_module(name)
