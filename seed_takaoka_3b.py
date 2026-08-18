import models
from database import SessionLocal


ESCOLA_NOME = "EMEF YOJIRO TAKAOKA"
BIMESTRE = 3
MODELOS = {
    1: [
        ("Portugues", "LP", 12),
        ("Historia", "His", 6),
        ("Geografia", "Geo", 6),
        ("Ed. Fisica", "EF", 6),
    ],
    2: [
        ("Matematica", "Mat", 12),
        ("Ciencias", "Cie", 6),
        ("Artes", "Art", 6),
        ("Ingles", "Ing", 6),
    ],
}

# Preencha aqui quando as respostas oficiais do 3o bimestre chegarem.
# Exemplo de chave: (dia, serie, codigo_gabarito)
# Para o 8o ano no Dia 1, a correcao automatica usa:
# - "8AC" para turmas 8A e 8C
# - "8B" para turma 8B
GABARITOS = {
    (1, 6, "PADRAO"): [
        "B",
        "B",
        "A",
        "B",
        "B",
        "B",
        "A",
        "A",
        "C",
        "C",
        "B",
        "C",
        "B",
        "C",
        "D",
        "B",
        "C",
        "A",
        "B",
        "A",
        "B",
        "C",
        "A",
        "D",
        "C",
        "B",
        "B",
        "C",
        "A",
        "C",
    ],
    (1, 7, "PADRAO"): [
        "A",
        "B",
        "B",
        "B",
        "B",
        "B",
        "C",
        "B",
        "D",
        "B",
        "A",
        "A",
        "C",
        "D",
        "D",
        "B",
        "D",
        "A",
        "A",
        "D",
        "A",
        "B",
        "A",
        "C",
        "A",
        "C",
        "C",
        "B",
        "A",
        "B",
    ],
    (1, 8, "8AC"): [
        "B",
        "B",
        "C",
        "B",
        "B",
        "B",
        "B",
        "B",
        "C",
        "B",
        "C",
        "C",
        "A",
        "D",
        "C",
        "C",
        "D",
        "B",
        "A",
        "A",
        "A",
        "A",
        "B",
        "C",
        "B",
        "C",
        "C",
        "C",
        "A",
        "B",
    ],
    (1, 8, "8B"): [
        "A",
        "B",
        "D",
        "C",
        "D",
        "A",
        "B",
        "A",
        "B",
        "C",
        "D",
        "C",
        "A",
        "D",
        "C",
        "C",
        "D",
        "B",
        "A",
        "A",
        "A",
        "A",
        "B",
        "C",
        "B",
        "C",
        "C",
        "C",
        "A",
        "B",
    ],
    (1, 9, "PADRAO"): [
        "A",
        "B",
        "D",
        "C",
        "D",
        "A",
        "D",
        "D",
        "B",
        "A",
        "B",
        "A",
        "A",
        "C",
        "B",
        "C",
        "B",
        "D",
        "C",
        "D",
        "A",
        "D",
        "A",
        "D",
        "C",
        "B",
        "B",
        "C",
        "B",
        "B",
    ],
    (2, 6, "PADRAO"): [
        "D",
        "B",
        "C",
        "B",
        "D",
        "A",
        "D",
        "C",
        "A",
        "D",
        "B",
        "A",
        "B",
        "D",
        "D",
        "B",
        "A",
        "C",
        "A",
        "B",
        "D",
        "D",
        "D",
        "C",
        "B",
        "B",
        "C",
        "A",
        "B",
        "C",
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
