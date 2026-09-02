# ============================================================
# routers/__init__.py — Exportación modular de routers
# ============================================================

from . import auth
from . import usuarios
from . import categorias
from . import movimientos
from . import presupuestos
from . import metas
from . import resumen
from . import analitica

__all__ = [
    "auth",
    "usuarios",
    "categorias",
    "movimientos",
    "presupuestos",
    "metas",
    "resumen",
    "analitica",
]
