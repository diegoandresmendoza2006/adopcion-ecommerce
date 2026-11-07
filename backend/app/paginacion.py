"""Paginación opcional y compatible con lo que ya existía.

Las listas antiguas devolvían TODO. Para no romper Angular, la paginación solo se activa si el
cliente manda ?pagina=N (la app móvil la usa para el scroll infinito). El total de filas viaja
en la cabecera X-Total-Count.
"""
from typing import Optional
from fastapi import Response


def paginar(consulta, response: Response, pagina: Optional[int], por_pagina: int):
    total = consulta.order_by(None).count()
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    if pagina is None:
        return consulta.all()
    return consulta.offset((pagina - 1) * por_pagina).limit(por_pagina).all()


def like(texto: str) -> str:
    """Patrón LIKE seguro: los % y _ que escriba el usuario se tratan como texto normal."""
    seguro = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{seguro}%"
