import os
import unittest
from unittest.mock import patch

from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

with patch.dict(os.environ, {"DATABASE_URL": ""}):
    import models
    import seed_takaoka_4b_7ano_substitutiva_dia1 as seed
    from database import Base
    from main import buscar_modelo_prova, salvar_gabarito, _comparar_e_salvar_respostas, _tabular_respostas


class TakaokaSubstitutivaTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as db:
            escola = models.Escola(nome=seed.ESCOLA_NOME)
            db.add(escola)
            db.flush()
            modelo = models.ModeloProva(escola_id=escola.id, bimestre=4, dia=1, nome="Regular")
            db.add(modelo)
            db.flush()
            self.escola_id, self.modelo_id = escola.id, modelo.id
            disciplinas = [seed.DISCIPLINAS[i] for i in (2, 1, 3, 0)]
            numero = 1
            for ordem, (nome, sigla, total) in enumerate(disciplinas, 1):
                db.add(models.DisciplinaProva(modelo_prova_id=modelo.id, disciplina=nome,
                       sigla=sigla, quantidade_questoes=total, ordem=ordem))
                for _ in range(total):
                    db.add(models.Gabarito(modelo_prova_id=modelo.id, serie=7,
                           codigo_gabarito="CADERNO_A", numero_questao=numero,
                           disciplina=nome, resposta_correta="A"))
                    numero += 1
            db.commit()
        with patch.object(seed, "SessionLocal", self.sessions):
            seed.main()
            seed.main()

    def tearDown(self):
        self.engine.dispose()

    def test_layout_e_salvamento_preservam_a_ordem_da_prova(self):
        with self.sessions() as db:
            dados = buscar_modelo_prova(self.escola_id, 4, 1, 7, "SUBSTITUTIVA", db)
            blocos = jsonable_encoder(dados)["disciplinas"]
            self.assertEqual([(d["disciplina"], d["quantidade_questoes"]) for d in blocos],
                             [(nome, total) for nome, _, total in seed.DISCIPLINAS])
            salvar_gabarito(escola_id=self.escola_id, bimestre=4, dia=1, serie=7,
                            codigo_gabarito="SUBSTITUTIVA", respostas=",".join(seed.RESPOSTAS), db=db)
            gs = db.query(models.Gabarito).filter_by(modelo_prova_id=self.modelo_id,
                  serie=7, codigo_gabarito="SUBSTITUTIVA").order_by(models.Gabarito.numero_questao).all()
            self.assertEqual(tuple(g.resposta_correta for g in gs), seed.RESPOSTAS)
            self.assertEqual([gs[i-1].disciplina for i in (1, 7, 13, 25)],
                             ["Ed. Fisica", "Historia", "Portugues", "Geografia"])
            self.assertEqual(gs[13].resposta_correta, "A")
            regular = db.query(models.Gabarito).filter_by(modelo_prova_id=self.modelo_id,
                      serie=7, codigo_gabarito="CADERNO_A").all()
            self.assertEqual(len(regular), 30)
            self.assertTrue(all(g.resposta_correta == "A" for g in regular))
            padrao = buscar_modelo_prova(self.escola_id, 4, 1, db=db)
            self.assertEqual(padrao["disciplinas"][0].disciplina, "Portugues")

    def test_correcao_na_numeracao_original(self):
        with self.sessions() as db:
            aluno = models.Aluno(escola_id=self.escola_id, nome="Aluno teste", numero_chamada=1)
            db.add(aluno)
            db.flush()
            gs = db.query(models.Gabarito).filter_by(modelo_prova_id=self.modelo_id,
                  serie=7, codigo_gabarito="SUBSTITUTIVA").order_by(models.Gabarito.numero_questao).all()
            respostas = {i: r for i, r in enumerate(seed.RESPOSTAS, 1) if r != "X"}
            acertos, _ = _comparar_e_salvar_respostas(db, aluno.id, self.modelo_id, gs, respostas)
            self.assertEqual(acertos, 30)
            respostas[1] = "A"
            acertos, salvas = _comparar_e_salvar_respostas(db, aluno.id, self.modelo_id, gs, respostas)
            self.assertEqual(acertos, 29)
            self.assertEqual(salvas[0]["disciplina"], "Ed. Fisica")
            self.assertFalse(salvas[0]["acertou"])
            self.assertTrue(salvas[13]["acertou"])
            tabulado = _tabular_respostas(salvas)
            self.assertEqual(list(tabulado["por_disciplina"]),
                             ["Portugues", "Historia", "Geografia", "Ed. Fisica"])
            self.assertEqual(tabulado["por_disciplina"]["Portugues"]["total"], 12)
            self.assertEqual(tabulado["linhas"][0]["numero_questao"], 1)

    def test_recorrige_resultado_anterior_com_questao_14_anulada(self):
        with self.sessions() as db:
            gs = db.query(models.Gabarito).filter_by(modelo_prova_id=self.modelo_id,
                  serie=7, codigo_gabarito="SUBSTITUTIVA").order_by(models.Gabarito.numero_questao).all()
            gs[13].resposta_correta = "X"
            for chamada, resposta14 in enumerate(("A", "B", None), 1):
                aluno = models.Aluno(escola_id=self.escola_id, nome=f"Teste {chamada}", numero_chamada=chamada)
                db.add(aluno)
                db.flush()
                respostas = {i: r for i, r in enumerate(seed.RESPOSTAS, 1)}
                respostas[14] = resposta14
                acertos, _ = _comparar_e_salvar_respostas(db, aluno.id, self.modelo_id, gs, respostas)
                self.assertEqual(acertos, 30)
                db.add(models.ResultadoAluno(aluno_id=aluno.id, modelo_prova_id=self.modelo_id,
                       escola_id=self.escola_id, bimestre=4, dia=1, serie=7,
                       codigo_gabarito="SUBSTITUTIVA", acertos=30, total_questoes=30, nota_global=10))
            db.commit()
        with patch.object(seed, "SessionLocal", self.sessions):
            seed.main()
        with self.sessions() as db:
            resultados = db.query(models.ResultadoAluno).join(models.Aluno).order_by(models.Aluno.numero_chamada).all()
            self.assertEqual([r.acertos for r in resultados], [30, 29, 29])
            respostas14 = db.query(models.RespostaAluno).filter_by(modelo_prova_id=self.modelo_id,
                          numero_questao=14).all()
            self.assertTrue(all(r.resposta_correta == "A" for r in respostas14))
            self.assertEqual(sum(r.acertou for r in respostas14), 1)


if __name__ == "__main__":
    unittest.main()
