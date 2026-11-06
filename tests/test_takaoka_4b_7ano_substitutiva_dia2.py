import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

with patch.dict(os.environ, {"DATABASE_URL": ""}):
    import models
    import seed_takaoka_4b_7ano_substitutiva_dia2 as seed
    from database import Base
    from main import buscar_modelo_prova, salvar_gabarito, _comparar_e_salvar_respostas, _tabular_respostas


class TakaokaSubstitutivaDia2Test(unittest.TestCase):
    def test_cadastro_correcao_e_ordem_final_do_dia_2(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        ordem_normal = ["Matematica", "Ciencias", "Artes", "Ingles"]
        with sessions() as db:
            escola = models.Escola(nome=seed.ESCOLA_NOME)
            db.add(escola)
            db.flush()
            modelo = models.ModeloProva(escola_id=escola.id, bimestre=4, dia=2, nome="Regular dia 2")
            db.add(modelo)
            db.flush()
            escola_id, modelo_id = escola.id, modelo.id
            numero = 1
            for ordem, indice in enumerate((3, 1, 2, 0), 1):
                nome, sigla, total = seed.DISCIPLINAS[indice]
                db.add(models.DisciplinaProva(modelo_prova_id=modelo.id, disciplina=nome,
                       sigla=sigla, quantidade_questoes=total, ordem=ordem))
                for _ in range(total):
                    db.add(models.Gabarito(modelo_prova_id=modelo.id, serie=7,
                           codigo_gabarito="CADERNO_B", numero_questao=numero,
                           disciplina=nome, resposta_correta="D"))
                    numero += 1
            db.commit()
        with patch.object(seed, "SessionLocal", sessions):
            seed.main()
            seed.main()
        with sessions() as db:
            dados = buscar_modelo_prova(escola_id, 4, 2, 7, "SUBSTITUTIVA", db)
            self.assertEqual([d.disciplina for d in dados["disciplinas"]],
                             ["Ingles", "Ciencias", "Artes", "Matematica"])
            salvar_gabarito(escola_id=escola_id, bimestre=4, dia=2, serie=7,
                            codigo_gabarito="SUBSTITUTIVA", respostas=",".join(seed.RESPOSTAS), db=db)
            gs = db.query(models.Gabarito).filter_by(modelo_prova_id=modelo_id,
                  serie=7, codigo_gabarito="SUBSTITUTIVA").order_by(models.Gabarito.numero_questao).all()
            self.assertEqual(len(gs), 30)
            self.assertEqual(tuple(g.resposta_correta for g in gs), seed.RESPOSTAS)
            self.assertEqual(gs[21].resposta_correta, "C")  # Questao 22 do caderno enviado.
            aluno = models.Aluno(escola_id=escola_id, nome="Aluno teste", numero_chamada=1)
            db.add(aluno)
            db.flush()
            respostas = dict(enumerate(seed.RESPOSTAS, 1))
            acertos, salvas = _comparar_e_salvar_respostas(db, aluno.id, modelo_id, gs, respostas)
            self.assertEqual(acertos, 30)
            self.assertEqual(list(_tabular_respostas(salvas)["por_disciplina"]), ordem_normal)
            respostas[22] = "A"
            acertos, salvas = _comparar_e_salvar_respostas(db, aluno.id, modelo_id, gs, respostas)
            self.assertEqual(acertos, 29)
            self.assertEqual(salvas[21]["disciplina"], "Matematica")
            regular = db.query(models.Gabarito).filter_by(modelo_prova_id=modelo_id,
                      serie=7, codigo_gabarito="CADERNO_B").all()
            self.assertEqual(len(regular), 30)
            self.assertTrue(all(g.resposta_correta == "D" for g in regular))
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
