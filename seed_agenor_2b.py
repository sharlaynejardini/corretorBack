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

            print(f"{nome_modelo}: {sum(item[2] for item in disciplinas)} questoes")

        db.commit()


if __name__ == "__main__":
    main()
