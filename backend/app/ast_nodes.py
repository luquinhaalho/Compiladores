"""Nós da Árvore Sintática Abstrata do subconjunto didático."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NoAST:
    tipo: str
    linha: int
    coluna: int
    linha_fim: int
    coluna_fim: int
    atributos: dict[str, Any] = field(default_factory=dict)
    filhos: list[NoAST] = field(default_factory=list)
    regra: str | None = None

    def para_dict(self) -> dict[str, Any]:
        return {
            "tipo": self.tipo,
            "linha": self.linha,
            "coluna": self.coluna,
            "linhaFim": self.linha_fim,
            "colunaFim": self.coluna_fim,
            "atributos": self.atributos,
            "regra": self.regra,
            "filhos": [filho.para_dict() for filho in self.filhos],
        }
