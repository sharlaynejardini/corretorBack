from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class Escola(Base):
    __tablename__ = "escolas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)


class Turma(Base):
    __tablename__ = "turmas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escola_id = Column(UUID(as_uuid=True), ForeignKey("escolas.id"))
    nome = Column(String, nullable=False)


class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escola_id = Column(UUID(as_uuid=True), ForeignKey("escolas.id"))
    turma_id = Column(UUID(as_uuid=True), ForeignKey("turmas.id"))
    numero_chamada = Column(Integer, nullable=False)
    nome = Column(String, nullable=False)


class ModeloProva(Base):
    __tablename__ = "modelos_prova"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escola_id = Column(UUID(as_uuid=True), ForeignKey("escolas.id"))
    nome = Column(String, nullable=False)
    dia = Column(Integer, nullable=False)
    bimestre = Column(Integer, nullable=False)


class DisciplinaProva(Base):
    __tablename__ = "disciplinas_prova"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    modelo_prova_id = Column(UUID(as_uuid=True), ForeignKey("modelos_prova.id"))
    disciplina = Column(String, nullable=False)
    sigla = Column(String, nullable=False)
    quantidade_questoes = Column(Integer, nullable=False)
    ordem = Column(Integer, nullable=False)


class Gabarito(Base):
    __tablename__ = "gabaritos"
    __table_args__ = (
        UniqueConstraint("modelo_prova_id", "serie", "numero_questao", name="uq_gabaritos_modelo_serie_questao"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    modelo_prova_id = Column(UUID(as_uuid=True), ForeignKey("modelos_prova.id"))
    serie = Column(Integer, nullable=False)
    numero_questao = Column(Integer, nullable=False)
    disciplina = Column(String, nullable=False)
    resposta_correta = Column(String, nullable=False)


class RespostaAluno(Base):
    __tablename__ = "respostas_alunos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aluno_id = Column(UUID(as_uuid=True), ForeignKey("alunos.id"))
    modelo_prova_id = Column(UUID(as_uuid=True), ForeignKey("modelos_prova.id"))
    numero_questao = Column(Integer, nullable=False)
    disciplina = Column(String, nullable=False)
    resposta_aluno = Column(String)
    resposta_correta = Column(String)
    acertou = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResultadoAluno(Base):
    __tablename__ = "resultados_alunos"
    __table_args__ = (
        UniqueConstraint("aluno_id", "modelo_prova_id", name="uq_resultados_alunos_aluno_modelo"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aluno_id = Column(UUID(as_uuid=True), ForeignKey("alunos.id"), nullable=False)
    modelo_prova_id = Column(UUID(as_uuid=True), ForeignKey("modelos_prova.id"), nullable=False)
    escola_id = Column(UUID(as_uuid=True), ForeignKey("escolas.id"), nullable=False)
    bimestre = Column(Integer, nullable=False)
    dia = Column(Integer, nullable=False)
    serie = Column(Integer, nullable=False)
    acertos = Column(Integer, nullable=False)
    total_questoes = Column(Integer, nullable=False)
    nota_global = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
