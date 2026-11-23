"""Teste de integração opcional com o projeto Supabase configurado em .env."""
import os
import time
import unittest

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


class TestSupabaseReal(unittest.TestCase):
    def setUp(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_KEY", "")
        if not self.url or not self.key:
            self.skipTest("SUPABASE_URL/SUPABASE_KEY não configuradas")

    def _nova_conta(self, nome):
        cliente = create_client(self.url, self.key)
        stamp = int(time.time() * 1000)
        email = f"{nome.lower()}-{stamp}@example.com"
        senha = "TesteRLS123!"
        cadastro = cliente.auth.sign_up({
            "email": email,
            "password": senha,
            "options": {"data": {"nome": nome}},
        })
        self.assertIsNotNone(cadastro.user)
        if cadastro.session is None:
            login = cliente.auth.sign_in_with_password({"email": email, "password": senha})
            uid = login.user.id
        else:
            uid = cadastro.user.id
        return cliente, str(uid)

    def test_sem_confirmacao_e_isolamento_rls(self):
        a, uid_a = self._nova_conta("ContaA")
        b, uid_b = self._nova_conta("ContaB")

        materia = a.table("materias").insert({
            "user_id": uid_a,
            "nome": "Matéria privada",
            "descricao": "Dados da ContaA",
        }).execute()
        self.assertEqual(len(materia.data), 1)
        materia_id = materia.data[0]["id"]

        estudo = a.table("estudos").insert({
            "user_id": uid_a,
            "materia_id": materia_id,
            "titulo": "Estudo privado",
            "status": "pendente",
            "duracao_min": 30,
        }).execute()
        self.assertEqual(len(estudo.data), 1)

        materias_b = b.table("materias").select("*").execute()
        estudos_b = b.table("estudos").select("*").execute()
        self.assertEqual(materias_b.data, [])
        self.assertEqual(estudos_b.data, [])

        materias_a = a.table("materias").select("*").execute()
        estudos_a = a.table("estudos").select("*").execute()
        self.assertEqual(len(materias_a.data), 1)
        self.assertEqual(len(estudos_a.data), 1)


if __name__ == "__main__":
    unittest.main()
