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


def _limiarizar_folha(folha):
    folha_cinza = cv2.cvtColor(folha, cv2.COLOR_BGR2GRAY)
    folha_cinza = cv2.GaussianBlur(folha_cinza, (3, 3), 0)

    folha_threshold = cv2.threshold(
        folha_cinza,
        0,
        255,
        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU,
    )[1]

    return folha_cinza, folha_threshold


def _mascara_marcacoes_azuis(folha):
    hsv = cv2.cvtColor(folha, cv2.COLOR_BGR2HSV)
    mascara = cv2.inRange(
        hsv,
        np.array([80, 25, 20]),
        np.array([140, 255, 255]),
    )
    return cv2.morphologyEx(mascara, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))


def _recortar_gabarito_takaoka(imagem, bordas):
    contornos = cv2.findContours(
        bordas.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    contornos = imutils.grab_contours(contornos)

    candidatos = []

    for contorno in contornos:
        x, y, w, h = cv2.boundingRect(contorno)
        area = cv2.contourArea(contorno)
        proporcao = w / float(h)

        if area > 10000 and h > 250 and 1.6 <= proporcao <= 2.4:
            candidatos.append((area, x, y, w, h))

    if not candidatos:
        return None

    _, x, y, w, h = max(candidatos, key=lambda item: item[0])
    margem = 4
    y1 = max(y - margem, 0)
    x1 = max(x - margem, 0)
    y2 = min(y + h + margem, imagem.shape[0])
    x2 = min(x + w + margem, imagem.shape[1])

    return imagem[y1:y2, x1:x2]


def processar_folha(caminho_arquivo, total_questoes=None):
    imagem = cv2.imread(caminho_arquivo)

    if imagem is None:
        return None, "Erro ao abrir imagem"

    try:
        imagem = imutils.resize(imagem, height=1200)
        original = imagem.copy()

        cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(cinza, (5, 5), 0)
        bordas = cv2.Canny(blur, 75, 200)

        if total_questoes == 30:
            folha = _recortar_gabarito_takaoka(original, bordas)

            if folha is not None:
                folha_cinza, folha_threshold = _limiarizar_folha(folha)
                mascara_azul = _mascara_marcacoes_azuis(folha)

                if cv2.countNonZero(mascara_azul) > 200:
                    folha_threshold = mascara_azul

                return {
                    "folha": folha,
                    "folha_cinza": folha_cinza,
                    "folha_threshold": folha_threshold,
                }, None

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
        folha_cinza, folha_threshold = _limiarizar_folha(folha)

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


def _grade_questoes(largura, altura, total_questoes, ajuste_x=0, ajuste_y=0, escala_x=1.0, escala_y=1.0):
    if total_questoes != 30:
        linhas = _linhas_alternativas(altura)
        return [
            {
                "questao": indice,
                "x": min(max(int((x - (largura / 2)) * escala_x + (largura / 2) + ajuste_x), 0), largura - 1),
                "linhas": {
                    alternativa: min(max(int((y - (altura / 2)) * escala_y + (altura / 2) + ajuste_y), 0), altura - 1)
                    for alternativa, y in linhas.items()
                },
                "bloco": "padrao",
            }
            for indice, x in enumerate(_centros_questoes(largura, total_questoes), start=1)
        ]

    blocos = [
        (1, 12, 0.075, 0.600, [0.285, 0.346, 0.402, 0.464], "portugues"),
        (13, 6, 0.693, 0.931, [0.285, 0.346, 0.402, 0.464], "historia"),
        (19, 6, 0.174, 0.414, [0.705, 0.775, 0.834, 0.899], "geografia"),
        (25, 6, 0.600, 0.841, [0.705, 0.759, 0.829, 0.899], "ed_fisica"),
    ]
    grade = []

    for questao_inicial, quantidade, inicio, fim, linhas, bloco in blocos:
        passo = (fim - inicio) / max(quantidade - 1, 1)
        raio_x = max(int(largura * passo * 0.40), 6)
        raio_y = max(int(altura * 0.035), 6)
        centros_y_base = {
            alternativa: altura * proporcao
            for alternativa, proporcao in zip(("A", "B", "C", "D"), linhas)
        }

        for deslocamento, x in enumerate(_distribuir_centros(largura, quantidade, inicio, fim)):
            x_ajustado = int((x - (largura / 2)) * escala_x + (largura / 2) + ajuste_x)
            centros_y = {
                alternativa: min(
                    max(int((y - (altura / 2)) * escala_y + (altura / 2) + ajuste_y), 0),
                    altura - 1,
                )
                for alternativa, y in centros_y_base.items()
            }

            grade.append(
                {
                    "questao": questao_inicial + deslocamento,
                    "x": min(max(x_ajustado, 0), largura - 1),
                    "linhas": centros_y,
                    "bloco": bloco,
                    "raio_x": raio_x,
                    "raio_y": raio_y,
                }
            )

    return grade


def _ler_grade(folha_threshold, total_questoes, grade):
    altura, largura = folha_threshold.shape
    raio_x_padrao = max(int(largura * 0.012), 8)
    raio_y_padrao = max(int(altura * 0.045), 8)
    respostas = {}
    debug = []

    for item in grade:
        questao = item["questao"]
        x = item["x"]
        linhas = item["linhas"]
        raio_x = item.get("raio_x", raio_x_padrao)
        raio_y = item.get("raio_y", raio_y_padrao)
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


def _clusters_linhas(projecao, minimo):
    indices = np.where(projecao >= minimo)[0]
    if len(indices) == 0:
        return []

    clusters = []
    inicio = indices[0]
    anterior = indices[0]

    for indice in indices[1:]:
        if indice > anterior + 1:
            clusters.append((inicio, anterior))
            inicio = indice
        anterior = indice

    clusters.append((inicio, anterior))
    return [int((inicio + fim) / 2) for inicio, fim in clusters]


def _intervalos_linhas(posicoes, minimo_intervalo=4):
    posicoes = sorted(set(posicoes))
    return [
        (inicio, fim)
        for inicio, fim in zip(posicoes, posicoes[1:])
        if fim - inicio >= minimo_intervalo
    ]


def _detectar_blocos_grade(folha_threshold):
    altura, largura = folha_threshold.shape
    kernel_vertical = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, max(int(altura * 0.08), 15)),
    )
    kernel_horizontal = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(int(largura * 0.04), 20), 1),
    )
    linhas_verticais = cv2.morphologyEx(folha_threshold, cv2.MORPH_OPEN, kernel_vertical)
    linhas_horizontais = cv2.morphologyEx(folha_threshold, cv2.MORPH_OPEN, kernel_horizontal)
    grade = cv2.add(linhas_verticais, linhas_horizontais)

    contornos = cv2.findContours(
        grade.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    contornos = imutils.grab_contours(contornos)
    blocos = []

    for contorno in contornos:
        x, y, w, h = cv2.boundingRect(contorno)
        area = w * h

        if area < largura * altura * 0.025:
            continue

        if w > largura * 0.92 and h > altura * 0.88:
            continue

        if w < largura * 0.12 or h < altura * 0.18:
            continue

        blocos.append((x, y, w, h))

    if len(blocos) < 4:
        return None

    blocos = sorted(blocos, key=lambda bloco: bloco[2] * bloco[3], reverse=True)[:4]
    blocos_ordenados = []
    blocos_por_altura = sorted(blocos, key=lambda bloco: bloco[1])
    topo = blocos_por_altura[:2]
    baixo = blocos_por_altura[2:4]
    blocos_ordenados.extend(sorted(topo, key=lambda bloco: bloco[0]))
    blocos_ordenados.extend(sorted(baixo, key=lambda bloco: bloco[0]))

    quantidades = [12, 6, 6, 6]
    questao_inicial = 1
    resultado = []

    for bloco, quantidade in zip(blocos_ordenados, quantidades):
        resultado.append(
            {
                "rect": bloco,
                "questao_inicial": questao_inicial,
                "quantidade": quantidade,
            }
        )
        questao_inicial += quantidade

    return resultado, linhas_verticais, linhas_horizontais


def _ler_grade_por_blocos(folha_threshold, blocos_info):
    blocos, linhas_verticais, linhas_horizontais = blocos_info
    respostas = {}
    debug = []

    for bloco in blocos:
        x, y, w, h = bloco["rect"]
        quantidade = bloco["quantidade"]
        questao_inicial = bloco["questao_inicial"]

        recorte_vertical = linhas_verticais[y : y + h, x : x + w]
        recorte_horizontal = linhas_horizontais[y : y + h, x : x + w]
        xs = _clusters_linhas(
            np.sum(recorte_vertical > 0, axis=0),
            max(int(h * 0.30), 8),
        )
        ys = _clusters_linhas(
            np.sum(recorte_horizontal > 0, axis=1),
            max(int(w * 0.25), 12),
        )

        intervalos_x = _intervalos_linhas(xs)
        intervalos_y = _intervalos_linhas(ys)

        if len(intervalos_x) < quantidade or len(intervalos_y) < 4:
            return None

        intervalos_x = sorted(intervalos_x, key=lambda intervalo: intervalo[0])[-quantidade:]
        intervalos_y = sorted(intervalos_y, key=lambda intervalo: intervalo[0])[-4:]

        for deslocamento, intervalo_x in enumerate(intervalos_x):
            questao = questao_inicial + deslocamento
            melhor_alternativa = None
            maior_pixels = -1
            contagens = {}
            regioes = {}

            for alternativa, intervalo_y in zip(("A", "B", "C", "D"), intervalos_y):
                x1 = x + intervalo_x[0] + 3
                x2 = x + intervalo_x[1] - 3
                y1 = y + intervalo_y[0] + 3
                y2 = y + intervalo_y[1] - 3

                if x2 <= x1 or y2 <= y1:
                    pixels = 0
                else:
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
                    "bloco": "detectado",
                    "contagens": contagens,
                    "maior_pixels": maior_pixels,
                    "segundo_maior_pixels": segundo_maior,
                    "diferenca_pixels": diferenca,
                    "confianca": confianca,
                    "centro_x": int((regioes[melhor_alternativa]["x1"] + regioes[melhor_alternativa]["x2"]) / 2),
                    "centros_y": {
                        alternativa: int((regiao["y1"] + regiao["y2"]) / 2)
                        for alternativa, regiao in regioes.items()
                    },
                    "regioes": regioes,
                    "tentativa_grade": {"metodo": "linhas_detectadas"},
                }
            )

    return respostas, debug


def _pontuar_debug(debug):
    confiancas = [item["confianca"] for item in debug]
    diferencas = [item["diferenca_pixels"] for item in debug]
    positivos = sum(1 for item in debug if item["maior_pixels"] > 0)

    return (
        positivos * 1000
        + sum(min(confianca, 8) for confianca in confiancas)
        + sum(max(diferenca, 0) for diferenca in diferencas) / 100
    )


def _ler_grade_com_tentativas(folha_threshold, total_questoes):
    altura, largura = folha_threshold.shape

    if total_questoes != 30:
        grade = _grade_questoes(largura, altura, total_questoes)
        return _ler_grade(folha_threshold, total_questoes, grade)

    blocos_info = _detectar_blocos_grade(folha_threshold)
    if blocos_info is not None:
        leitura_blocos = _ler_grade_por_blocos(folha_threshold, blocos_info)
        if leitura_blocos is not None:
            return leitura_blocos

    melhor = None
    deslocamentos_x = [0, -8, 8, -14, 14]
    deslocamentos_y = [0, -6, 6, -10, 10]
    escalas_x = [1.0, 0.985, 1.015]
    escalas_y = [1.0, 0.985, 1.015]

    for ajuste_x in deslocamentos_x:
        for ajuste_y in deslocamentos_y:
            for escala_x in escalas_x:
                for escala_y in escalas_y:
                    grade = _grade_questoes(
                        largura,
                        altura,
                        total_questoes,
                        ajuste_x=ajuste_x,
                        ajuste_y=ajuste_y,
                        escala_x=escala_x,
                        escala_y=escala_y,
                    )
                    respostas, debug = _ler_grade(folha_threshold, total_questoes, grade)
                    pontuacao = _pontuar_debug(debug)

                    if melhor is None or pontuacao > melhor[0]:
                        melhor = (pontuacao, respostas, debug, ajuste_x, ajuste_y, escala_x, escala_y)

    _, respostas, debug, ajuste_x, ajuste_y, escala_x, escala_y = melhor

    for item in debug:
        item["tentativa_grade"] = {
            "ajuste_x": ajuste_x,
            "ajuste_y": ajuste_y,
            "escala_x": escala_x,
            "escala_y": escala_y,
        }

    return respostas, debug


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

    return _ler_grade_com_tentativas(folha_threshold, total_questoes)
