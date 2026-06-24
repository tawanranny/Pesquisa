"""
Cache de análise por hash de arquivo.

Garante que cada livro seja analisado UMA única vez. Se o arquivo não mudou
(mesmo hash), o resultado vem do cache e nenhum token é gasto novamente.
"""
from __future__ import annotations

import json
from pathlib import Path

ARQUIVO_CACHE = Path("cache_pesquisa.json")


class Cache:
    def __init__(self, caminho: Path = ARQUIVO_CACHE):
        self.caminho = caminho
        self._dados: dict[str, dict] = {}
        self._carregar()

    def _carregar(self) -> None:
        if self.caminho.exists():
            try:
                self._dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            except Exception:
                self._dados = {}

    def obter(self, hash_arquivo: str) -> dict | None:
        return self._dados.get(hash_arquivo)

    def salvar(self, hash_arquivo: str, resultado: dict) -> None:
        self._dados[hash_arquivo] = resultado
        self._persistir()

    def _persistir(self) -> None:
        self.caminho.write_text(
            json.dumps(self._dados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def limpar(self) -> None:
        self._dados = {}
        if self.caminho.exists():
            self.caminho.unlink()
