"""
Backends de IA para os casos em dúvida. Dois modos:

  • "max": chama o **Claude Code** instalado no PC (usa o login do seu plano
    Max/Pro). Sem chave de API e sem custo por uso.
  • "api": usa a chave da API da Anthropic (sk-ant-...), cobrança por uso.

Cada backend é uma função simples: perguntar(prompt: str) -> str.
Retorna None se o modo não estiver disponível (ex.: Claude Code não instalado).
"""
from __future__ import annotations

import shutil
import subprocess


def claude_code_disponivel() -> bool:
    return shutil.which("claude") is not None


def backend_claude_code(modelo: str | None = None, timeout: int = 120):
    """Usa o Claude Code (assinatura Max) via linha de comando."""
    exe = shutil.which("claude")
    if not exe:
        return None

    def perguntar(prompt: str) -> str:
        cmd = [exe, "-p", prompt]
        if modelo:
            cmd += ["--model", modelo]
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        if r.returncode != 0:
            raise RuntimeError((r.stderr or "Claude Code falhou").strip()[:200])
        return (r.stdout or "").strip()

    return perguntar


def backend_api(chave: str, modelo: str, max_tokens: int = 160):
    """Usa a API da Anthropic (chave sk-ant-...)."""
    try:
        from anthropic import Anthropic
    except Exception:
        return None
    cliente = Anthropic(api_key=chave)

    def perguntar(prompt: str) -> str:
        resp = cliente.messages.create(
            model=modelo, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()

    return perguntar
