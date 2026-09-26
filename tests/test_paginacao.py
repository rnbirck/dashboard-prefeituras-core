from types import SimpleNamespace

import pytest

from dashboard_core.paginacao import executar_paginado


class Consulta:
    def __init__(self, dados, limite=2, falha=None):
        self.dados = dados
        self.limite = limite
        self.falha = falha
        self.ordem = []
        self.faixas = []

    def order(self, coluna):
        self.ordem.append(coluna)
        return self

    def range(self, inicio, fim):
        self.inicio, self.fim = inicio, fim
        self.faixas.append((inicio, fim))
        return self

    def execute(self):
        if self.falha is not None and self.inicio >= self.falha:
            raise RuntimeError('indisponível')
        dados = sorted(self.dados, key=lambda x: tuple(str(x[k]) for k in sorted(x))) if self.ordem else self.dados
        return SimpleNamespace(data=dados[self.inicio:min(self.fim+1,self.inicio+self.limite)])


def test_le_tudo_mesmo_com_limite_menor_e_linhas_repetidas():
    dados = [{'ano': a, 'nascimentos/1000_hab': v} for a, v in [(2025,4),(2024,2),(2024,2),(2026,6),(2023,1)]]
    consulta = Consulta(dados)
    resposta = executar_paginado(consulta, tamanho=5)
    assert len(resposta.data) == 5
    assert resposta.data.count({'ano':2024,'nascimentos/1000_hab':2}) == 2
    assert consulta.ordem == ['ano','"nascimentos/1000_hab"']
    assert consulta.faixas == [(0,0),(0,4),(2,6),(4,8),(5,9)]


def test_falha_em_pagina_nao_devolve_resultado_parcial():
    with pytest.raises(RuntimeError, match='indisponível'):
        executar_paginado(Consulta([{'ano':i} for i in range(6)], falha=2))


def test_consulta_vazia():
    consulta = Consulta([])
    assert executar_paginado(consulta).data == []
    assert consulta.faixas == [(0,0)]
