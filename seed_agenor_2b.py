import models
from database import SessionLocal


ESCOLA_NOME = "EMEF DEP. AGENOR LINO DE MATTOS"
BIMESTRE = 2
MODELOS = {
    1: [
        ("Língua Portuguesa", "LP", 10),
        ("História", "His", 5),
        ("Geografia", "Geo", 5),
        ("Educação Física", "Ed.F", 5),
    ],
    2: [
        ("Matemática", "Mat", 10),
        ("Ciências", "Ciê", 5),
        ("Artes", "Art", 5),
        ("Inglês", "Ing", 5),
    ],
}

GABARITOS = {
    (1, 5, "CADERNO_A"): [
        "D",
        "C",
        "B",
        "C",
        "A",
        "B",
        "C",
        "A",
        "D",
        "A",
        "C",
        "A",
        "B",
        "C",
        "D",
        "B",
        "D",
        "B",
        "A",
        "C",
        "A",
        "A",
        "A",
        "C",
        "B",
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
            nome_modelo = f"Prova Bimestral - {BIMESTRE}º Bimestre - Dia {dia}"
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
