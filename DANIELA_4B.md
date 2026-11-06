# Daniela - 2o Simulado - 4o bimestre

Para cadastrar ou atualizar o gabarito no banco configurado por `DATABASE_URL`:

```sh
python seed_daniela_4b.py
```

O modelo e cadastrado no **4o bimestre, dia 2**, com o codigo `PADRAO` e a
serie interna 8, seguindo a convencao ja usada para o cursinho Daniela.
Sao 62 questoes: 90 a 120 e 136 a 166. As questoes 90, 155 e 161 sao
anuladas (`X`, com pontuacao para todos); a resposta da 166 e **E**.

Os indices internos sao 1 a 62, na ordem da folha. Os rotulos `Questao 90`
a `Questao 166` preservam a numeracao impressa, incluindo o salto de 120
para 136. Na correcao manual, informe as 62 respostas nessa mesma ordem.
A leitura por foto reconhece as duas tabelas de 31 colunas com alternativas A-E.

O script pode ser executado novamente: atualiza as respostas e recalcula
os resultados desse modelo. O envio ao GitHub, por si so, nao executa o
cadastro no banco.

Validacao local, sem acessar o banco de producao:

```sh
python -B -m unittest discover -s tests -v
```
