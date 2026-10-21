"""Cadastra os gabaritos do simulado mensal, Dia 1, Caderno A."""

import models
from database import SessionLocal


ESCOLA_NOME = "EMEF YOJIRO TAKAOKA"
BIMESTRE = 4
DIA = 1
CODIGO_GABARITO = "CADERNO_A"
DISCIPLINAS = [
    ("Portugues", "LP", 12),
    ("Historia", "His", 6),
    ("Geografia", "Geo", 6),
    ("Ed. Fisica", "EF", 6),
]
GABARITOS = {
    6: "A B A B B B B C A B A B A C D C B D B C B A C B B B A A B D".split(),
    7: "A A B B B C C A B A B A C A C D B A D C B D D B D B A B B C".split(),
}


def main():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada.")

    disciplinas_questoes = [
        nome for nome, _sigla, quantidade in DISCIPLINAS for _ in range(quantidade)
    ]
    for serie, respostas in GABARITOS.items():
        if len(respostas) != len(disciplinas_questoes) or not set(respostas) <= set("ABCD"):
            raise RuntimeError(f"Gabarito invalido para o {serie} ano.")

    with SessionLocal() as db:
        escola = db.query(models.Escola).filter_by(nome=ESCOLA_NOME).one()
        modelo = db.query(models.ModeloProva).filter_by(
            escola_id=escola.id, bimestre=BIMESTRE, dia=DIA
        ).one_or_none()
        if modelo is None:
            modelo = models.ModeloProva(
                escola_id=escola.id,
                nome="Simulado mensal - 4o Bimestre - Dia 1",
                bimestre=BIMESTRE,
                dia=DIA,
            )
            db.add(modelo)
            db.flush()

        disciplinas = db.query(models.DisciplinaProva).filter_by(
            modelo_prova_id=modelo.id
        ).order_by(models.DisciplinaProva.ordem).all()
        if disciplinas:
            configuracao = [
                (d.disciplina, d.sigla, d.quantidade_questoes) for d in disciplinas
            ]
            if configuracao != DISCIPLINAS:
                raise RuntimeError("O modelo existente possui disciplinas diferentes.")
        else:
            for ordem, (nome, sigla, quantidade) in enumerate(DISCIPLINAS, 1):
                db.add(models.DisciplinaProva(
                    modelo_prova_id=modelo.id, disciplina=nome, sigla=sigla,
                    quantidade_questoes=quantidade, ordem=ordem,
                ))

        for serie, respostas in GABARITOS.items():
            existentes = db.query(models.Gabarito).filter_by(
                modelo_prova_id=modelo.id, serie=serie,
                codigo_gabarito=CODIGO_GABARITO,
            ).order_by(models.Gabarito.numero_questao).all()
            esperado = [
                (numero, disciplinas_questoes[numero - 1], resposta)
                for numero, resposta in enumerate(respostas, 1)
            ]
            if existentes:
                atual = [
                    (g.numero_questao, g.disciplina, g.resposta_correta) for g in existentes
                ]
                if atual != esperado:
                    raise RuntimeError(f"O gabarito existente do {serie} ano e diferente.")
            else:
                for numero, disciplina, resposta in esperado:
                    db.add(models.Gabarito(
                        modelo_prova_id=modelo.id, serie=serie,
                        codigo_gabarito=CODIGO_GABARITO, numero_questao=numero,
                        disciplina=disciplina, resposta_correta=resposta,
                    ))

        db.commit()
        print("Gabaritos conferidos: 6o e 7o anos, Caderno A, 30 respostas por serie.")


if __name__ == "__main__":
    main()
