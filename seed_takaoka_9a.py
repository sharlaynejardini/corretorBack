import models
from database import SessionLocal


ESCOLA_NOME = "EMEF YOJIRO TAKAOKA"
TURMA_NOME = "9A"
ALUNOS = [
    (26, "BRUNO ALEXANDRE BERCOVICI"),
]


def main():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada.")

    with SessionLocal() as db:
        escola = db.query(models.Escola).filter(models.Escola.nome == ESCOLA_NOME).first()

        if not escola:
            escola = models.Escola(nome=ESCOLA_NOME)
            db.add(escola)
            db.flush()
            print(f"Escola criada: {ESCOLA_NOME}")

        turma = (
            db.query(models.Turma)
            .filter(models.Turma.escola_id == escola.id)
            .filter(models.Turma.nome == TURMA_NOME)
            .first()
        )

        if not turma:
            turma = models.Turma(escola_id=escola.id, nome=TURMA_NOME)
            db.add(turma)
            db.flush()
            print(f"Turma criada: {TURMA_NOME}")

        for numero_chamada, nome in ALUNOS:
            aluno = (
                db.query(models.Aluno)
                .filter(models.Aluno.turma_id == turma.id)
                .filter(models.Aluno.numero_chamada == numero_chamada)
                .first()
            )

            if not aluno:
                aluno = (
                    db.query(models.Aluno)
                    .filter(models.Aluno.turma_id == turma.id)
                    .filter(models.Aluno.nome == nome)
                    .first()
                )

            if aluno:
                aluno.escola_id = escola.id
                aluno.turma_id = turma.id
                aluno.numero_chamada = numero_chamada
                aluno.nome = nome
                print(f"Aluno atualizado: {numero_chamada} - {nome}")
            else:
                db.add(
                    models.Aluno(
                        escola_id=escola.id,
                        turma_id=turma.id,
                        numero_chamada=numero_chamada,
                        nome=nome,
                    )
                )
                print(f"Aluno criado: {numero_chamada} - {nome}")

        db.commit()


if __name__ == "__main__":
    main()
