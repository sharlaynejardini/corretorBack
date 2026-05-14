import cv2
import imutils
import numpy as np


def ordenar_pontos(pontos):
    retangulo = np.zeros((4, 2), dtype="float32")

    soma = pontos.sum(axis=1)
    retangulo[0] = pontos[np.argmin(soma)]
    retangulo[2] = pontos[np.argmax(soma)]

    diferenca = np.diff(pontos, axis=1)
    retangulo[1] = pontos[np.argmin(diferenca)]
    retangulo[3] = pontos[np.argmax(diferenca)]

    return retangulo


def transformar_perspectiva(imagem, pontos):
    retangulo = ordenar_pontos(pontos)
    topo_esq, topo_dir, baixo_dir, baixo_esq = retangulo

    largura_a = np.linalg.norm(baixo_dir - baixo_esq)
    largura_b = np.linalg.norm(topo_dir - topo_esq)
    largura = max(int(largura_a), int(largura_b))

    altura_a = np.linalg.norm(topo_dir - baixo_dir)
    altura_b = np.linalg.norm(topo_esq - baixo_esq)
    altura = max(int(altura_a), int(altura_b))

    if largura <= 0 or altura <= 0:
        raise ValueError("Dimensoes invalidas para corrigir perspectiva")

    destino = np.array(
        [
            [0, 0],
            [largura - 1, 0],
            [largura - 1, altura - 1],
            [0, altura - 1],
        ],
        dtype="float32",
    )

    matriz = cv2.getPerspectiveTransform(retangulo, destino)
    imagem_corrigida = cv2.warpPerspective(imagem, matriz, (largura, altura))

    return imagem_corrigida


def processar_folha(caminho_arquivo):
    imagem = cv2.imread(caminho_arquivo)

    if imagem is None:
        return None, "Erro ao abrir imagem"

    try:
        imagem = imutils.resize(imagem, height=1200)
        original = imagem.copy()

        cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(cinza, (5, 5), 0)
        bordas = cv2.Canny(blur, 75, 200)

        contornos = cv2.findContours(
            bordas.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        contornos = imutils.grab_contours(contornos)
        contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:10]

        folha_contorno = None

        for contorno in contornos:
            perimetro = cv2.arcLength(contorno, True)
            aproximado = cv2.approxPolyDP(contorno, 0.02 * perimetro, True)

            if len(aproximado) == 4:
                folha_contorno = aproximado
                break

        if folha_contorno is None:
            return None, "Nao consegui encontrar o contorno da folha"

        pontos = folha_contorno.reshape(4, 2)
        folha = transformar_perspectiva(original, pontos)

        folha_cinza = cv2.cvtColor(folha, cv2.COLOR_BGR2GRAY)
        folha_cinza = cv2.GaussianBlur(folha_cinza, (3, 3), 0)

        folha_threshold = cv2.threshold(
            folha_cinza,
            0,
            255,
            cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU,
        )[1]

        return {
            "folha": folha,
            "folha_cinza": folha_cinza,
            "folha_threshold": folha_threshold,
        }, None
    except Exception as exc:
        return None, f"Erro ao processar imagem: {exc}"


def detectar_bolhas(folha_threshold):
    contornos = cv2.findContours(
        folha_threshold.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    contornos = imutils.grab_contours(contornos)
    bolhas = []

    for contorno in contornos:
        x, y, w, h = cv2.boundingRect(contorno)
        area = cv2.contourArea(contorno)
        proporcao = w / float(h)

        if (
            w >= 15
            and h >= 15
            and area >= 100
            and 0.65 <= proporcao <= 1.35
        ):
            bolhas.append((x, y, w, h))

    return sorted(bolhas, key=lambda bolha: (bolha[1], bolha[0]))


def _distribuir_centros(largura, quantidade, inicio, fim):
    if quantidade == 1:
        return [int(largura * inicio)]

    passo = (fim - inicio) / (quantidade - 1)
    return [int(largura * (inicio + indice * passo)) for indice in range(quantidade)]


def _centros_questoes(largura, total_questoes):
    if total_questoes == 22:
        grupos = [
            (10, 0.022, 0.380),
            (4, 0.462, 0.582),
            (4, 0.662, 0.782),
            (4, 0.862, 0.982),
        ]
    else:
        margem = 0.035
        passo = (1 - (2 * margem)) / max(total_questoes - 1, 1)
        return [int(largura * (margem + indice * passo)) for indice in range(total_questoes)]

    centros = []

    for quantidade, inicio, fim in grupos:
        centros.extend(_distribuir_centros(largura, quantidade, inicio, fim))

    return centros


def _linhas_alternativas(altura):
    return {
        "A": int(altura * 0.515),
        "B": int(altura * 0.655),
        "C": int(altura * 0.795),
        "D": int(altura * 0.935),
    }


def _linhas_takaoka(altura, topo=True):
    if topo:
        proporcoes = {
            "A": 0.300,
            "B": 0.360,
            "C": 0.420,
            "D": 0.480,
        }
    else:
        proporcoes = {
            "A": 0.695,
            "B": 0.755,
            "C": 0.815,
            "D": 0.875,
        }

    return {
        alternativa: int(altura * proporcao)
        for alternativa, proporcao in proporcoes.items()
    }


def _grade_questoes(largura, altura, total_questoes):
    if total_questoes != 30:
        linhas = _linhas_alternativas(altura)
        return [
            {"questao": indice, "x": x, "linhas": linhas, "bloco": "padrao"}
            for indice, x in enumerate(_centros_questoes(largura, total_questoes), start=1)
        ]

    blocos = [
        (1, 12, 0.072, 0.602, _linhas_takaoka(altura, topo=True), "topo_esquerda"),
        (13, 6, 0.692, 0.928, _linhas_takaoka(altura, topo=True), "topo_direita"),
        (19, 6, 0.168, 0.409, _linhas_takaoka(altura, topo=False), "baixo_esquerda"),
        (25, 6, 0.598, 0.834, _linhas_takaoka(altura, topo=False), "baixo_direita"),
    ]
    grade = []

    for questao_inicial, quantidade, inicio, fim, linhas, bloco in blocos:
        for deslocamento, x in enumerate(_distribuir_centros(largura, quantidade, inicio, fim)):
            grade.append(
                {
                    "questao": questao_inicial + deslocamento,
                    "x": x,
                    "linhas": linhas,
                    "bloco": bloco,
                }
            )

    return grade


def ler_respostas_grade_fixa(folha_threshold, total_questoes=22):
    """
    Le respostas de uma grade fixa com alternativas A/B/C/D.

    O total de questoes deve vir do gabarito oficial:
    - 22 para EMEF DEP. AGENOR LINO DE MATTOS
    - 30 para EMEF YOJIRO TAKAOKA
    """
    if folha_threshold is None:
        raise ValueError("Imagem threshold nao informada")

    if len(folha_threshold.shape) != 2:
        raise ValueError("A leitura espera uma imagem threshold em escala de cinza")

    altura, largura = folha_threshold.shape
    grade = _grade_questoes(largura, altura, total_questoes)

    respostas = {}
    debug = []

    raio_x = max(int(largura * 0.012), 8)
    raio_y = max(int(altura * (0.022 if total_questoes == 30 else 0.045)), 8)

    for item in grade:
        questao = item["questao"]
        x = item["x"]
        linhas = item["linhas"]
        melhor_alternativa = None
        maior_pixels = -1
        contagens = {}
        regioes = {}

        for alternativa, y in linhas.items():
            x1 = max(x - raio_x, 0)
            x2 = min(x + raio_x, largura)
            y1 = max(y - raio_y, 0)
            y2 = min(y + raio_y, altura)

            recorte = folha_threshold[y1:y2, x1:x2]
            pixels = int(cv2.countNonZero(recorte))

            contagens[alternativa] = pixels
            regioes[alternativa] = {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            }

            if pixels > maior_pixels:
                maior_pixels = pixels
                melhor_alternativa = alternativa

        ordenadas = sorted(contagens.values(), reverse=True)
        segundo_maior = ordenadas[1] if len(ordenadas) > 1 else 0
        diferenca = maior_pixels - segundo_maior
        confianca = round(maior_pixels / max(segundo_maior, 1), 2)

        respostas[questao] = melhor_alternativa

        debug.append(
            {
                "questao": questao,
                "resposta": melhor_alternativa,
                "bloco": item["bloco"],
                "contagens": contagens,
                "maior_pixels": maior_pixels,
                "segundo_maior_pixels": segundo_maior,
                "diferenca_pixels": diferenca,
                "confianca": confianca,
                "centro_x": x,
                "centros_y": linhas,
                "regioes": regioes,
            }
        )

    return respostas, debug
