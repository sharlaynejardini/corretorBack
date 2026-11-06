"""Gabarito Daniela: 2o Simulado, 4o bimestre, folha ENEM do dia 2."""

import models
from database import SessionLocal
from seed_daniela_agosto import ESCOLA_NOME, _normalizar_texto, _preparar_banco


BIMESTRE = 4
DIA = 2
SERIE = 8  # Convencao usada pelo sistema para as turmas do cursinho Daniela.
CODIGO_GABARITO = "PADRAO"
NOME_MODELO = "Daniela - 2o Simulado - 4o bimestre"
NUMEROS_IMPRESSOS = (*range(90, 121), *range(136, 167))
RESPOSTAS = (
    # 90 a 120; X representa questao anulada.
    "X", "B", "C", "E", "A", "A", "C", "D", "E", "D",
    "C", "A", "A", "E", "D", "D", "D", "E", "B", "B",
    "D", "D", "B", "E", "C", "C", "A", "E", "D", "B", "B",
    # 136 a 166. A ultima resposta foi confirmada como E.
    "A", "B", "B", "A", "B", "B", "A", "D", "D", "D",
    "B", "B", "C", "E", "C", "E", "A", "D", "C", "X",
    "B", "C", "C", "C", "D", "X", "A", "D", "C", "B", "E",
)
# O sistema usa indices consecutivos; o rotulo preserva o numero da folha.
DISCIPLINAS = [(f"Questao {numero}", f"Q{numero}", 1) for numero in NUMEROS_IMPRESSOS]


def main():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada.")
    if (len(RESPOSTAS) != 62 or len(NUMEROS_IMPRESSOS) != len(RESPOSTAS)
            or set(RESPOSTAS) - set("ABCDEX")):
        raise ValueError("O modelo Daniela deve ter 62 questoes.")
    _preparar_banco()

    with SessionLocal() as db:
        escola = next((e for e in db.query(models.Escola).all()
                       if "DANIELA" in _normalizar_texto(e.nome)), None)
        if escola is None:
            escola = models.Escola(nome=ESCOLA_NOME)
            db.add(escola)
            db.flush()
        modelo = db.query(models.ModeloProva).filter_by(
            escola_id=escola.id, bimestre=BIMESTRE, dia=DIA,
        ).one_or_none()
        if modelo is None:
            modelo = models.ModeloProva(
                escola_id=escola.id, bimestre=BIMESTRE, dia=DIA, nome=NOME_MODELO,
            )
            db.add(modelo)
            db.flush()
        modelo.nome = NOME_MODELO

        disciplinas = db.query(models.DisciplinaProva).filter_by(
            modelo_prova_id=modelo.id,
        ).order_by(models.DisciplinaProva.ordem).all()
        if disciplinas:
            if [(d.disciplina, d.sigla, d.quantidade_questoes) for d in disciplinas] != DISCIPLINAS:
                raise RuntimeError("Modelo existente difere das 62 questoes esperadas.")
        else:
            for ordem, (nome, sigla, quantidade) in enumerate(DISCIPLINAS, 1):
                db.add(models.DisciplinaProva(
                    modelo_prova_id=modelo.id, disciplina=nome, sigla=sigla,
                    quantidade_questoes=quantidade, ordem=ordem,
                ))

        existentes = {g.numero_questao: g for g in db.query(models.Gabarito).filter_by(
            modelo_prova_id=modelo.id, serie=SERIE, codigo_gabarito=CODIGO_GABARITO,
        ).all()}
        if set(existentes) - set(range(1, 63)):
            raise RuntimeError("Gabarito existente possui questoes adicionais.")
        for indice, resposta in enumerate(RESPOSTAS, 1):
            gabarito = existentes.get(indice)
            if gabarito is None:
                gabarito = models.Gabarito(
                    modelo_prova_id=modelo.id, serie=SERIE,
                    codigo_gabarito=CODIGO_GABARITO, numero_questao=indice,
                )
                db.add(gabarito)
            gabarito.disciplina = DISCIPLINAS[indice - 1][0]
            gabarito.resposta_correta = resposta
        db.flush()

        from main import _buscar_gabarito, _recalcular_resultados_por_gabarito

        recalculados = _recalcular_resultados_por_gabarito(
            db, modelo, SERIE, CODIGO_GABARITO,
            _buscar_gabarito(db, modelo.id, SERIE, CODIGO_GABARITO),
        )
        db.commit()
        print(f"{NOME_MODELO}: 62 questoes; 90, 155 e 161 anuladas; 166 = E.")
        print(f"{recalculados} resultados recalculados.")


if __name__ == "__main__":
    main()
