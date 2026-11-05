"""Verifica parâmetros, integridade FIFO e detecção do deadlock intencional da A4."""

import unittest

from experimento import AMOSTRAS, D1, D2, N, executar


class TestExperimento(unittest.TestCase):
    """Testes de comportamento executados em processos isolados, como as medições."""

    def test_parametros_individuais(self):
        """Sem parâmetros/retorno; confere os valores exigidos para o nome do autor."""
        self.assertEqual((D1, D2, N, AMOSTRAS), (4, 0, 3, 20_000))

    def test_fifo_com_semaforos(self):
        """Sem parâmetros/retorno; verifica FIFO inclusive com buffer de uma posição."""
        for capacidade in (1, 3, 7):
            with self.subTest(capacidade=capacidade):
                resultado = executar(2, total=137, capacidade=capacidade)
                self.assertEqual(resultado["produzidas"], 137)
                self.assertEqual(resultado["consumidas"], 137)
                self.assertEqual(resultado["unicas"], 137)
                self.assertEqual(resultado["perdidas"], 0)
                self.assertEqual(resultado["duplicadas"], 0)
                self.assertEqual(resultado["invalidas"], 0)
                self.assertTrue(resultado["em_ordem"])
                self.assertFalse(resultado["travou"])

    def test_deadlock_por_inversao(self):
        """Sem parâmetros/retorno; confirma espera circular ao encher a versão 3."""
        resultado = executar(3, total=137, capacidade=3)
        self.assertTrue(resultado["travou"])
        self.assertEqual(resultado["produzidas"], 3)
        self.assertEqual(resultado["consumidas"], 0)
        self.assertEqual(resultado["perdidas"], 137)
        self.assertEqual(resultado["estado_produtor"], "retém mutex e aguarda vazio")
        self.assertEqual(resultado["estado_consumidor"], "retém cheio e aguarda mutex")

    def test_contabilidade_sem_sincronizacao(self):
        """Sem parâmetros/retorno; confere métricas sem exigir uma corrida específica."""
        resultado = executar(1, total=137, capacidade=3)
        self.assertEqual(resultado["perdidas"] + resultado["unicas"], 137)
        self.assertEqual(resultado["consumidas"], resultado["unicas"]
                         + resultado["duplicadas"] + resultado["invalidas"])


if __name__ == "__main__":
    unittest.main()
