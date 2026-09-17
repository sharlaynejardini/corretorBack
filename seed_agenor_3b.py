import models
from database import SessionLocal


ESCOLA_NOME = "EMEF DEP. AGENOR LINO DE MATTOS"
BIMESTRE = 3
MODELOS = {
    1: [
        ("Lingua Portuguesa", "LP", 10),
        ("Historia", "His", 5),
        ("Geografia", "Geo", 5),
        ("Ed. Fisica", "EF", 5),
    ],
    2: [
        ("Matematica", "Mat", 10),
        ("Ciencias", "Cie", 5),
        ("Artes", "Art", 5),
        ("Ingles", "Ing", 5),
    ],
}

GABARITOS = {
    (1, 5, "CADERNO_A"): [
        "B",
        "C",
        "D",
        "C",
        "A",
        "B",
        "B",
        "A",
        "C",
        "D",
        "C",
        "A",
        "B",
        "A",
        "D",
        "C",
        "C",
        "A",
        "B",
        "D",
        "A",
        "C",
        "C",
        "A",
        "B",
    ],
    (1, 6, "CADERNO_A"): [
        "A",
        "D",
        "A",
        "D",
        "A",
        "C",
        "A",
        "D",
        "A",
        "D",
        "A",
        "B",
        "C",
        "D",
        "C",
        "A",
        "D",
        "C",
        "C",
        "B",
        "B",
        "A",
        "C",
        "A",
        "D",
    ],
    (1, 7, "CADERNO_A"): [
        "A",
        "A",
        "D",
        "C",
        "B",
        "C",
        "B",
        "C",
        "B",
        "C",
        "B",
        "C",
        "D",
        "A",
        "B",
        "A",
        "B",
        "C",
        "D",
        "B",
        "B",
        "A",
        "B",
        "B",
        "B",
    ],
    (1, 8, "CADERNO_A"): [
        "B",
        "D",
        "C",
        "D",
        "B",
        "C",
        "A",
        "B",
        "D",
        "C",
        "B",
        "C",
        "A",
        "C",
        "D",
        "A",
        "B",
        "C",
        "D",
        "B",
        "A",
        "B",
        "A",
        "B",
        "A",
    ],
    (1, 9, "CADERNO_A"): [
        "B",
        "C",
        "C",
        "B",
        "D",
        "D",
        "A",
        "A",
        "D",
        "B",
        "D",
        "B",
        "C",
        "D",
        "A",
        "A",
        "B",
        "C",
        "D",
        "B",
        "B",
        "A",
        "A",
        "B",
        "C",
    ],
    (2, 5, "PADRAO"): [
        "C",
        "D",
        "B",
        "D",
        "A",
        "C",
        "B",
        "D",
        "A",
        "B",
        "B",
        "A",
        "C",
        "D",
        "B",
        "D",
        "C",
        "A",
        "B",
        "C",
        "C",
        "A",
        "A",
        "B",
        "D",
    ],
    (2, 5, "CADERNO_B"): [
        "C",
        "D",
        "B",
        "D",
        "A",
        "C",
        "B",
        "D",
        "A",
        "B",
        "B",
        "A",
        "C",
        "D",
        "B",
        "D",
        "C",
        "A",
        "B",
        "C",
        "C",
        "A",
        "A",
        "B",
        "D",
    ],
    (2, 6, "CADERNO_B"): [
        "C",
        "B",
        "A",
        "C",
        "A",
        "D",
        "C",
        "D",
        "B",
        "B",
        "D",
        "C",
        "D",
        "A",
        "B",
        "B",
        "D",
        "B",
        "C",
        "B",
        "B",
        "B",
        "A",
        "B",
        "A",
    ],
    (2, 7, "CADERNO_B"): [
        "B",
        "D",
        "B",
        "B",
        "C",
        "B",
        "C",
        "A",
        "D",
        "A",
        "D",
        "A",
        "D",
        "B",
        "A",
        "B",
        "D",
        "B",
        "C",
        "B",
        "B",
        "B",
        "A",
        "B",
        "A",
    ],
    (2, 8, "CADERNO_B"): [
        "D",
        "B",
        "D",
        "B",
        "B",
        "C",
        "A",
        "A",
        "D",
        "B",
        "B",
        "C",
        "D",
        "D",
        "C",
        "C",
        "D",
        "C",
        "D",
        "B",
        "B",
        "B",
        "A",
        "B",
        "A",
    ],
    (2, 9, "CADERNO_B"): [
        "C",
        "C",
        "C",
        "B",
        "B",
        "D",
        "B",
        "D",
        "C",
        "A",
        "B",
        "A",
        "C",
        "D",
        "C",
        "C",
        "D",
        "C",
        "D",
        "B",
        "B",
        "B",
        "A",
        "B",
        "A",
    ],
}


def _disciplinas_por_questao(disciplinas):
    disciplinas_questoes = []

    for disciplina, _sigla, quantidade in disciplinas:
        disciplinas_questoes.extend([disciplina] * quantidade)

    return disciplinas_questoes


def main():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada.")

    with SessionLocal() as db:
        escola = db.query(models.Escola).filter(models.Escola.nome == ESCOLA_NOME).first()

        if not escola:
            raise RuntimeError(f"Escola nao encontrada: {ESCOLA_NOME}")

        for dia, disciplinas in MODELOS.items():
            nome_modelo = f"Prova Bimestral - {BIMESTRE}o Bimestre - Dia {dia}"
            modelo = (
                db.query(models.ModeloProva)
                .filter(models.ModeloProva.escola_id == escola.id)
                .filter(models.ModeloProva.bimestre == BIMESTRE)
                .filter(models.ModeloProva.dia == dia)
                .first()
            )

            if not modelo:
                modelo = models.ModeloProva(
                    escola_id=escola.id,
                    nome=nome_modelo,
                    bimestre=BIMESTRE,
                    dia=dia,
                )
                db.add(modelo)
                db.flush()
            else:
                modelo.nome = nome_modelo

            disciplinas_existentes = (
                db.query(models.DisciplinaProva)
                .filter(models.DisciplinaProva.modelo_prova_id == modelo.id)
                .all()
            )

            for disciplina in disciplinas_existentes:
                db.delete(disciplina)

            db.flush()

            for ordem, (disciplina, sigla, quantidade) in enumerate(disciplinas, start=1):
                db.add(
                    models.DisciplinaProva(
                        modelo_prova_id=modelo.id,
                        disciplina=disciplina,
                        sigla=sigla,
                        quantidade_questoes=quantidade,
                        ordem=ordem,
                    )
                )

            disciplinas_questoes = _disciplinas_por_questao(disciplinas)
            for (dia_gabarito, serie, codigo_gabarito), respostas in GABARITOS.items():
                if dia_gabarito != dia:
                    continue

                if len(respostas) != len(disciplinas_questoes):
                    raise RuntimeError(
                        f"Gabarito {codigo_gabarito} do {serie} ano tem "
                        f"{len(respostas)} respostas, mas o modelo tem "
                        f"{len(disciplinas_questoes)} questoes."
                    )

                gabaritos_existentes = {
                    gabarito.numero_questao: gabarito
                    for gabarito in (
                        db.query(models.Gabarito)
                        .filter(models.Gabarito.modelo_prova_id == modelo.id)
                        .filter(models.Gabarito.serie == serie)
                        .filter(models.Gabarito.codigo_gabarito == codigo_gabarito)
                        .all()
                    )
                }

                for numero_questao, resposta in enumerate(respostas, start=1):
                    disciplina = disciplinas_questoes[numero_questao - 1]
                    gabarito = gabaritos_existentes.get(numero_questao)

                    if gabarito:
                        gabarito.disciplina = disciplina
                        gabarito.resposta_correta = resposta
                    else:
                        db.add(
                            models.Gabarito(
                                modelo_prova_id=modelo.id,
                                serie=serie,
                                codigo_gabarito=codigo_gabarito,
                                numero_questao=numero_questao,
                                disciplina=disciplina,
                                resposta_correta=resposta,
                            )
                        )

                print(f"Gabarito {serie} ano {codigo_gabarito}: {len(respostas)} respostas")

            print(f"{nome_modelo}: {sum(item[2] for item in disciplinas)} questoes")

        db.commit()


if __name__ == "__main__":
    main()
