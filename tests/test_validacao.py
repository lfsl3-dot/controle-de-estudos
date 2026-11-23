# -*- coding: utf-8 -*-

import unittest

from controllers import validacao as v


class TestValidacao(unittest.TestCase):
    def test_email(self):
        self.assertIsNone(v.validar_email("aluno@escola.edu.br"))
        for ruim in ["", "   ", "sem-arroba", "a@b", "a b@c.com", "x" * 260 + "@a.com"]:
            self.assertIsNotNone(v.validar_email(ruim), ruim)

    def test_senha_cadastro(self):
        self.assertIsNone(v.validar_senha_cadastro("abc12345"))
        for ruim in [None, "", "curta1", "somenteletras", "12345678", "a1" * 40]:
            self.assertIsNotNone(v.validar_senha_cadastro(ruim), ruim)

    def test_texto(self):
        self.assertEqual(v.validar_texto("  Prova  ", "título", 3, 10), ("Prova", None))
        self.assertIsNotNone(v.validar_texto("", "título", 3, 10)[1])
        self.assertIsNotNone(v.validar_texto("ab", "título", 3, 10)[1])
        self.assertIsNotNone(v.validar_texto("x" * 11, "título", 3, 10)[1])
        self.assertIsNotNone(v.validar_texto("ab\x00cd", "título", 3, 10)[1])
        self.assertEqual(v.validar_texto("", "descrição", 0, 10, obrigatorio=False), ("", None))

    def test_inteiro(self):
        self.assertEqual(v.validar_inteiro(" 45 ", "duração", 1, 600), (45, None))
        for ruim in ["abc", "", None, "4.5", "0", "-3", "601"]:
            self.assertIsNone(v.validar_inteiro(ruim, "duração", 1, 600)[0], ruim)

    def test_status_e_id(self):
        self.assertIsNone(v.validar_status("pendente"))
        self.assertIsNotNone(v.validar_status("hackeado"))
        self.assertEqual(v.validar_id("7")[0], 7)
        for ruim in [None, "x", 0, -1, "1; drop table"]:
            self.assertIsNone(v.validar_id(ruim)[0], ruim)


if __name__ == "__main__":
    unittest.main()
