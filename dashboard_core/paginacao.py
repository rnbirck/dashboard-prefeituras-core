"""Leitura completa das consultas PostgREST usadas pelo Streamlit."""
from types import SimpleNamespace
import re
import time

import httpx


def _identificador(nome):
    if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", nome):
        return nome
    return '"' + nome.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _executar(consulta):
    for tentativa in range(3):
        try:
            resposta = consulta.execute()
            if getattr(resposta, 'error', None):
                raise RuntimeError(str(resposta.error))
            if not isinstance(resposta.data, list):
                raise ValueError('Resposta tabular inválida do Supabase')
            return resposta.data
        except httpx.TransportError:
            if tentativa == 2:
                raise
            time.sleep(2 ** tentativa)


def executar_paginado(consulta, tamanho=5000):
    """Preserva filtros e multiplicidade, inclusive sem coluna id no destino.

    Ordena por todas as colunas e avança pelo tamanho realmente devolvido. O
    limite configurado no servidor pode ser menor que o tamanho solicitado.
    Erros interrompem a leitura; uma resposta parcial nunca é armazenada no cache.
    """
    if tamanho <= 0:
        raise ValueError('Tamanho de página deve ser positivo')
    amostra = _executar(consulta.range(0, 0))
    if not amostra:
        return SimpleNamespace(data=[])
    for coluna in sorted(amostra[0]):
        consulta = consulta.order(_identificador(coluna))
    registros = []
    while True:
        lote = _executar(consulta.range(len(registros), len(registros) + tamanho - 1))
        if not lote:
            return SimpleNamespace(data=registros)
        registros.extend(lote)
