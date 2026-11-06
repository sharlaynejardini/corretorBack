import unittest
from unittest.mock import patch

import cv2
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
import seed_daniela_4b as seed
from database import Base
from main import _comparar_e_salvar_respostas
from processador_imagem import ler_respostas_grade_fixa


class DanielaGabaritoTest(unittest.TestCase):
    def test_cadastro_repetido_e_correcao(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        with patch.object(seed, "SessionLocal", sessions), patch.object(seed, "_preparar_banco"):
            seed.main()
            seed.main()
        with sessions() as db:
            modelo = db.query(models.ModeloProva).one()
            self.assertEqual((modelo.bimestre, modelo.dia), (4, 2))
            self.assertEqual(db.query(models.DisciplinaProva).count(), 62)
            gabaritos = db.query(models.Gabarito).order_by(models.Gabarito.numero_questao).all()
            self.assertEqual(len(gabaritos), 62)
            por_numero = dict(zip(seed.NUMEROS_IMPRESSOS, (g.resposta_correta for g in gabaritos)))
            self.assertEqual({n for n, r in por_numero.items() if r == "X"}, {90, 155, 161})
            self.assertEqual(por_numero[166], "E")
            self.assertEqual(gabaritos[30].disciplina, "Questao 120")
            self.assertEqual(gabaritos[31].disciplina, "Questao 136")
            escola = db.query(models.Escola).one()
            aluno = models.Aluno(escola_id=escola.id, nome="Aluno teste", numero_chamada=1)
            db.add(aluno)
            db.flush()
            # Prova sem marcacoes recebe apenas os tres pontos das anuladas.
            acertos, _ = _comparar_e_salvar_respostas(db, aluno.id, modelo.id, gabaritos, {})
            self.assertEqual(acertos, 3)
            respostas = {g.numero_questao: g.resposta_correta for g in gabaritos
                         if g.resposta_correta != "X"}
            acertos, _ = _comparar_e_salvar_respostas(db, aluno.id, modelo.id, gabaritos, respostas)
            self.assertEqual(acertos, 62)
        engine.dispose()


class DanielaLeituraTest(unittest.TestCase):
    def test_duas_tabelas_com_cinco_alternativas(self):
        imagem = np.zeros((760, 1700), dtype=np.uint8)
        esperadas = {}
        for bloco, y in enumerate((40, 400)):
            x, w, h = 45, 1612, 280
            cv2.line(imagem, (x, y), (x, y + h), 255, 2)
            cv2.line(imagem, (x + w, y), (x + w, y + h), 255, 2)
            for linha in range(8):
                cv2.line(imagem, (x, y + linha * 40), (x + w, y + linha * 40), 255, 2)
            for coluna in range(32):
                xx = x + coluna * 52
                cv2.line(imagem, (xx, y + 40), (xx, y + h), 255, 2)
            for coluna in range(31):
                numero = bloco * 31 + coluna + 1
                alternativa = (coluna + bloco) % 5
                esperadas[numero] = "ABCDE"[alternativa]
                xx, yy = x + coluna * 52, y + (alternativa + 2) * 40
                cv2.rectangle(imagem, (xx + 6, yy + 6), (xx + 46, yy + 34), 255, -1)
        respostas, _ = ler_respostas_grade_fixa(imagem, 62, imagem)
        self.assertEqual(respostas, esperadas)


if __name__ == "__main__":
    unittest.main()
