"""Substitutiva do 7o ano, Caderno A, Takaoka, 4o bimestre de 2026."""

import models
from database import SessionLocal

ESCOLA_NOME = "EMEF YOJIRO TAKAOKA"
BIMESTRE = 4
DIA = 1
SERIE = 7
CODIGO_GABARITO = "SUBSTITUTIVA"
DISCIPLINAS = [
    ("Ed. Fisica", "EF", 6),
    ("Historia", "His", 6),
    ("Portugues", "LP", 12),
    ("Geografia", "Geo", 6),
]
RESPOSTAS = (
    "D", "B", "A", "B", "B", "C",  # Educacao Fisica: 1-6
    "C", "A", "C", "D", "B", "A",  # Historia: 7-12
    "A", "X", "B", "B", "B", "C",  # Portugues: 13-24
    "C", "A", "B", "A", "B", "A",
    "D", "C", "B", "D", "D", "B",  # Geografia: 25-30
)


def main():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada.")
    from main import _buscar_gabarito, _recalcular_resultados_por_gabarito

    disciplinas_questoes = [nome for nome, _, total in DISCIPLINAS for _ in range(total)]
    if len(RESPOSTAS) != len(disciplinas_questoes) or set(RESPOSTAS) - set("ABCDEX"):
        raise ValueError("Gabarito invalido para as 30 questoes da substitutiva.")
    with SessionLocal() as db:
        escola = db.query(models.Escola).filter_by(nome=ESCOLA_NOME).one()
        modelo = db.query(models.ModeloProva).filter_by(
            escola_id=escola.id, bimestre=BIMESTRE, dia=DIA,
        ).one()
        disciplinas = db.query(models.DisciplinaProva).filter_by(modelo_prova_id=modelo.id).all()
        if {d.disciplina: d.quantidade_questoes for d in disciplinas} != {
            nome: total for nome, _, total in DISCIPLINAS
        }:
            raise RuntimeError("O modelo regular difere das disciplinas esperadas.")
        existentes = {g.numero_questao: g for g in db.query(models.Gabarito).filter_by(
            modelo_prova_id=modelo.id, serie=SERIE, codigo_gabarito=CODIGO_GABARITO,
        ).all()}
        if set(existentes) - set(range(1, 31)):
            raise RuntimeError("A substitutiva existente possui questoes adicionais.")
        for numero, resposta in enumerate(RESPOSTAS, 1):
            gabarito = existentes.get(numero)
            if gabarito is None:
                gabarito = models.Gabarito(
                    modelo_prova_id=modelo.id, serie=SERIE,
                    codigo_gabarito=CODIGO_GABARITO, numero_questao=numero,
                )
                db.add(gabarito)
            gabarito.disciplina = disciplinas_questoes[numero - 1]
            gabarito.resposta_correta = resposta
        db.flush()
        recalculados = _recalcular_resultados_por_gabarito(
            db, modelo, SERIE, CODIGO_GABARITO,
            _buscar_gabarito(db, modelo.id, SERIE, CODIGO_GABARITO),
        )
        db.commit()
        print(f"Takaoka: 7o ano, 4o bimestre, dia 1, SUBSTITUTIVA: 30 questoes; 14 anulada.")
        print(f"{recalculados} resultados recalculados.")


if __name__ == "__main__":
    main()
