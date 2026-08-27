import unicodedata

from sqlalchemy import text

import models
from database import SessionLocal, engine


ESCOLA_NOME = "EMEF MARIA VILANI DANIELA PINHEIRO"
BIMESTRE = 3
DIA = 1
NOME_MODELO = "Simulado Agosto"
SERIE = 8
CODIGO_GABARITO = "PADRAO"
DISCIPLINAS = [
    ("Q01 - H16 - Lingua Portuguesa", "Q01", 1),
    ("Q02 - H22 - Lingua Portuguesa", "Q02", 1),
    ("Q03 - H18 - Lingua Portuguesa", "Q03", 1),
    ("Q04 - H15 - Lingua Portuguesa", "Q04", 1),
    ("Q05 - H21 - Lingua Portuguesa", "Q05", 1),
    ("Q06 - H21 - Lingua Portuguesa / Literatura", "Q06", 1),
    ("Q07 - H17 - Lingua Portuguesa", "Q07", 1),
    ("Q08 - H17 - Lingua Portuguesa", "Q08", 1),
    ("Q09 - H19 - Lingua Portuguesa", "Q09", 1),
    ("Q10 - H19 - Lingua Portuguesa", "Q10", 1),
    ("Q11 - CA 1 - H4 - Lingua Portuguesa / Cidadania", "Q11", 1),
    ("Q12 - CA 5 - H17 - Literatura Periferica", "Q12", 1),
    ("Q13 - CA 5 - H16 - Literatura (Realismo)", "Q13", 1),
    ("Q14 - CA 8 - H25 - Sociolinguistica", "Q14", 1),
    ("Q15 - CA 5 - H15 - Literatura Contemporanea", "Q15", 1),
    ("Q16 - CA 1 - H3 - Comunicacao Social", "Q16", 1),
    ("Q17 - CA 8 - H26 - Sociolinguistica", "Q17", 1),
    ("Q18 - CA 6 - H18 - Lingua Portuguesa", "Q18", 1),
    ("Q19 - CA 1 - H1 - Lingua Portuguesa", "Q19", 1),
    ("Q20 - CA 8 - H27 - Lingua Portuguesa", "Q20", 1),
]

GABARITO = [
    "E",
    "E",
    "C",
    "E",
    "B",
    "C",
    "D",
    "A",
    "C",
    "C",
    "B",
    "C",
    "B",
    "B",
    "C",
    "C",
    "B",
    "C",
    "C",
    "C",
]


def _normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", valor or "")
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return texto.upper()


def _disciplinas_por_questao(disciplinas):
    disciplinas_questoes = []

    for disciplina, _sigla, quantidade in disciplinas:
        disciplinas_questoes.extend([disciplina] * quantidade)

    return disciplinas_questoes


def _preparar_banco():
    if engine is None:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                alter table if exists gabaritos
                drop constraint if exists gabaritos_resposta_correta_check
                """
            )
        )
        conn.execute(
            text(
                """
                alter table if exists gabaritos
                add constraint gabaritos_resposta_correta_check
                check (resposta_correta in ('A', 'B', 'C', 'D', 'E', 'X'))
                """
            )
        )
        conn.execute(
            text(
                """
                alter table if exists respostas_alunos
                drop constraint if exists respostas_alunos_resposta_aluno_check
                """
            )
        )
        conn.execute(
            text(
                """
                alter table if exists respostas_alunos
                add constraint respostas_alunos_resposta_aluno_check
                check (resposta_aluno in ('A', 'B', 'C', 'D', 'E', 'X'))
                """
            )
        )
        conn.execute(
            text(
                """
                alter table if exists respostas_alunos
                drop constraint if exists respostas_alunos_resposta_correta_check
                """
            )
        )
        conn.execute(
            text(
                """
                alter table if exists respostas_alunos
                add constraint respostas_alunos_resposta_correta_check
                check (resposta_correta in ('A', 'B', 'C', 'D', 'E', 'X'))
                """
            )
        )


def main():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada.")

    _preparar_banco()

    with SessionLocal() as db:
        escolas = db.query(models.Escola).all()
        escola = next(
            (
                escola
                for escola in escolas
                if "DANIELA" in _normalizar_texto(escola.nome)
            ),
            None,
        )

        if not escola:
            escola = models.Escola(nome=ESCOLA_NOME)
            db.add(escola)
            db.flush()
            print(f"Escola criada: {ESCOLA_NOME}")

        modelo = (
            db.query(models.ModeloProva)
            .filter(models.ModeloProva.escola_id == escola.id)
            .filter(models.ModeloProva.bimestre == BIMESTRE)
            .filter(models.ModeloProva.dia == DIA)
            .first()
        )

        if not modelo:
            modelo = models.ModeloProva(
                escola_id=escola.id,
                nome=NOME_MODELO,
                bimestre=BIMESTRE,
                dia=DIA,
            )
            db.add(modelo)
            db.flush()
        else:
            modelo.nome = NOME_MODELO

        disciplinas_existentes = (
            db.query(models.DisciplinaProva)
            .filter(models.DisciplinaProva.modelo_prova_id == modelo.id)
            .all()
        )

        for disciplina in disciplinas_existentes:
            db.delete(disciplina)

        db.flush()

        for ordem, (disciplina, sigla, quantidade) in enumerate(DISCIPLINAS, start=1):
            db.add(
                models.DisciplinaProva(
                    modelo_prova_id=modelo.id,
                    disciplina=disciplina,
                    sigla=sigla,
                    quantidade_questoes=quantidade,
                    ordem=ordem,
                )
            )

        disciplinas_questoes = _disciplinas_por_questao(DISCIPLINAS)

        if GABARITO:
            if len(GABARITO) != len(disciplinas_questoes):
                raise RuntimeError(
                    f"Gabarito tem {len(GABARITO)} respostas, mas o modelo tem "
                    f"{len(disciplinas_questoes)} questoes."
                )

            gabaritos_existentes = {
                gabarito.numero_questao: gabarito
                for gabarito in (
                    db.query(models.Gabarito)
                    .filter(models.Gabarito.modelo_prova_id == modelo.id)
                    .filter(models.Gabarito.serie == SERIE)
                    .filter(models.Gabarito.codigo_gabarito == CODIGO_GABARITO)
                    .all()
                )
            }

            for numero_questao, resposta in enumerate(GABARITO, start=1):
                disciplina = disciplinas_questoes[numero_questao - 1]
                gabarito = gabaritos_existentes.get(numero_questao)

                if gabarito:
                    gabarito.disciplina = disciplina
                    gabarito.resposta_correta = resposta
                else:
                    db.add(
                        models.Gabarito(
                            modelo_prova_id=modelo.id,
                            serie=SERIE,
                            codigo_gabarito=CODIGO_GABARITO,
                            numero_questao=numero_questao,
                            disciplina=disciplina,
                            resposta_correta=resposta,
                        )
                    )

            print(f"Gabarito Daniela Agosto: {len(GABARITO)} respostas")
        else:
            print("Modelo criado sem gabarito oficial preenchido.")

        print(f"{NOME_MODELO}: {sum(item[2] for item in DISCIPLINAS)} questoes")
        db.commit()


if __name__ == "__main__":
    main()
