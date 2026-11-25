# -*- coding: utf-8 -*-

import time
import unittest

from controllers import app_controller as ac
from controllers.app_controller import AppController
from models import conexao
from tests.fake_supabase import BancoFalso, ClienteFalso


def novo_controller(banco):
    return AppController(cliente=ClienteFalso(banco))


def criar_e_entrar(banco, nome="Ana", email="ana@escola.com", senha="senha1234"):
    c = novo_controller(banco)
    ok, _, _ = c.cadastrar(nome, email, senha, senha)
    assert ok
    ok, _, _ = c.entrar(email, senha)
    assert ok
    return c


class TestLogin(unittest.TestCase):
    def setUp(self):
        self.banco = BancoFalso()

    def test_mensagem_generica_para_senha_errada_e_email_inexistente(self):
        c = criar_e_entrar(self.banco)
        c.sair()
        _, msg1, _ = c.entrar("ana@escola.com", "senhaERRADA1")
        _, msg2, _ = c.entrar("naoexiste@escola.com", "qualquer123")
        _, msg3, _ = c.entrar("isso-nao-e-email", "qualquer123")
        self.assertEqual(msg1, ac.MSG_LOGIN_INVALIDO)
        self.assertEqual(msg1, msg2)
        self.assertEqual(msg1, msg3)

    def test_bloqueio_temporario_apos_varias_falhas(self):
        c = criar_e_entrar(self.banco)
        c.sair()
        for _ in range(ac.MAX_FALHAS_LOGIN):
            c.entrar("ana@escola.com", "errada12345")
        ok, msg, _ = c.entrar("ana@escola.com", "senha1234")  # senha certa, mas bloqueado
        self.assertFalse(ok)
        self.assertIn("Muitas tentativas", msg)
        c._bloqueado_ate = time.monotonic() - 1  # passa o tempo
        self.assertTrue(c.entrar("ana@escola.com", "senha1234")[0])

    def test_cadastro_valida_campos(self):
        c = novo_controller(self.banco)
        self.assertFalse(c.cadastrar("", "a@b.com", "senha1234", "senha1234")[0])
        self.assertFalse(c.cadastrar("Ana", "ruim", "senha1234", "senha1234")[0])
        self.assertFalse(c.cadastrar("Ana", "a@b.com", "curta", "curta")[0])
        self.assertFalse(c.cadastrar("Ana", "a@b.com", "senha1234", "outra12345")[0])
        self.assertEqual(self.banco.usuarios, {})

    def test_perfil_carregado_no_login(self):
        c = criar_e_entrar(self.banco, nome="Ana Souza")
        self.assertEqual(c.usuario_atual["nome"], "Ana Souza")


class TestSemLogin(unittest.TestCase):
    def test_nenhuma_funcao_funciona_sem_sessao(self):
        c = novo_controller(BancoFalso())
        chamadas = [
            lambda: c.listar_materias(), lambda: c.criar_materia("Mat", ""),
            lambda: c.atualizar_materia(1, "Mat", ""), lambda: c.excluir_materia(1),
            lambda: c.listar_estudos(), lambda: c.criar_estudo("Titulo", 1, "pendente", "30"),
            lambda: c.atualizar_estudo(1, "Titulo", 1, "pendente", "30"),
            lambda: c.excluir_estudo(1), lambda: c.atualizar_perfil("Ana"),
        ]
        for chamada in chamadas:
            ok, msg, _ = chamada()
            self.assertFalse(ok)
            self.assertEqual(msg, ac.MSG_SESSAO_EXPIRADA)

    def test_logout_bloqueia_novamente(self):
        banco = BancoFalso()
        c = criar_e_entrar(banco)
        self.assertTrue(c.listar_materias()[0])
        c.sair()
        self.assertIsNone(c.usuario_atual)
        self.assertFalse(c.listar_materias()[0])


class TestCrud(unittest.TestCase):
    def setUp(self):
        self.banco = BancoFalso()
        self.c = criar_e_entrar(self.banco)

    def _materia(self, nome="Matemática"):
        self.assertTrue(self.c.criar_materia(nome, "")[0])
        return self.c.listar_materias()[2][-1]["id"]

    def test_fluxo_completo_das_tres_tabelas(self):
        mid = self._materia()
        self.assertTrue(self.c.criar_estudo("Revisar funções", mid, "pendente", "45")[0])
        estudo = self.c.listar_estudos()[2][0]
        self.assertEqual(estudo["materia_nome"], "Matemática")
        self.assertTrue(self.c.atualizar_estudo(estudo["id"], "Revisar funções 2", mid, "concluido", "60")[0])
        estudo = self.c.listar_estudos()[2][0]
        self.assertEqual((estudo["titulo"], estudo["status"], estudo["duracao_min"]), ("Revisar funções 2", "concluido", 60))
        self.assertEqual(self.c.resumo([estudo])["concluido"], 1)
        self.assertTrue(self.c.excluir_estudo(estudo["id"])[0])
        self.assertEqual(self.c.listar_estudos()[2], [])
        self.assertTrue(self.c.atualizar_materia(mid, "Álgebra", "Capítulo 1")[0])
        self.assertTrue(self.c.excluir_materia(mid)[0])
        self.assertTrue(self.c.atualizar_perfil("Ana Maria")[0])

    def test_entradas_invalidas_sao_recusadas(self):
        mid = self._materia()
        casos = [
            ("", mid, "pendente", "30"), ("ab", mid, "pendente", "30"), ("x" * 81, mid, "pendente", "30"),
            ("Titulo ok", None, "pendente", "30"), ("Titulo ok", "abc", "pendente", "30"),
            ("Titulo ok", mid, "inventado", "30"), ("Titulo ok", mid, "pendente", "abc"),
            ("Titulo ok", mid, "pendente", "-5"), ("Titulo ok", mid, "pendente", "9999"),
            ("Titulo ok", mid, "pendente", ""),
        ]
        for caso in casos:
            self.assertFalse(self.c.criar_estudo(*caso)[0], caso)
        self.assertEqual(self.banco.tabelas["estudos"], [])
        self.assertFalse(self.c.criar_materia("", "")[0])
        self.assertFalse(self.c.criar_materia("Ok", "d" * 201)[0])

    def test_erro_tecnico_nao_vaza_para_a_tela(self):
        self.banco.falhar_com = 'relation "public.estudos" does not exist (SQLSTATE 42P01)'
        ok, msg, _ = self.c.listar_estudos()
        self.assertFalse(ok)
        self.assertEqual(msg, ac.MSG_ERRO_GENERICO)
        self.assertNotIn("estudos", msg)

    def test_mutacoes_repetidas_sao_bloqueadas(self):
        c = criar_e_entrar(self.banco)
        mid = c.criar_materia("Matéria", "")
        self.assertTrue(mid[0])
        c._mutacoes = ac.MAX_MUTACOES - 1
        ok, msg, _ = c.criar_materia("Nova matéria", "")
        self.assertFalse(ok)
        self.assertIn("Muitas operações", msg)


class TestIsolamento(unittest.TestCase):
    def test_conta_b_nao_ve_nem_altera_dados_da_conta_a(self):
        banco = BancoFalso()
        a = criar_e_entrar(banco, "Ana", "ana@escola.com")
        b = criar_e_entrar(banco, "Beto", "beto@escola.com")
        a.criar_materia("Física", "")
        mid_a = a.listar_materias()[2][0]["id"]
        a.criar_estudo("Leis de Newton", mid_a, "pendente", "30")
        eid_a = a.listar_estudos()[2][0]["id"]

        self.assertEqual(b.listar_materias()[2], [])
        self.assertEqual(b.listar_estudos()[2], [])
        b.excluir_estudo(eid_a)
        b.atualizar_estudo(eid_a, "Invadido", mid_a, "concluido", "5")
        self.assertEqual(len(a.listar_estudos()[2]), 1)
        self.assertEqual(a.listar_estudos()[2][0]["titulo"], "Leis de Newton")


class TestConexao(unittest.TestCase):
    def setUp(self):
        import os
        self.os = os
        self._antigo = {k: os.environ.get(k) for k in ("SUPABASE_URL", "SUPABASE_KEY")}

    def tearDown(self):
        for k, v in self._antigo.items():
            if v is None:
                self.os.environ.pop(k, None)
            else:
                self.os.environ[k] = v

    def _jwt(self, role):
        import base64, json
        b64 = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
        header = {"alg": "HS256"}
        payload = {"role": role}
        return f"{b64(header)}.{b64(payload)}.assinatura"

    def test_exige_variaveis(self):
        self.os.environ["SUPABASE_URL"] = ""
        self.os.environ["SUPABASE_KEY"] = ""
        with self.assertRaises(conexao.ConfiguracaoError):
            conexao.ler_configuracao()

    def test_recusa_chave_privilegiada(self):
        self.os.environ["SUPABASE_URL"] = "https://x.supabase.co"
        for chave in ("sb_secret_abc123", self._jwt("service_role")):
            self.os.environ["SUPABASE_KEY"] = chave
            with self.assertRaises(conexao.ConfiguracaoError):
                conexao.ler_configuracao()

    def test_aceita_chave_publica_e_limpa_a_url(self):
        self.os.environ["SUPABASE_URL"] = "https://x.supabase.co/rest/v1/"
        for chave in ("sb_publishable_abc123", self._jwt("anon")):
            self.os.environ["SUPABASE_KEY"] = chave
            url, k = conexao.ler_configuracao()
            self.assertEqual((url, k), ("https://x.supabase.co", chave))


if __name__ == "__main__":
    unittest.main()
