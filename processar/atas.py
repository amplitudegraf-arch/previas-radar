"""Lê a lista de presença e as justificativas de ausência das atas
eletrônicas do SAPL (PDF gerado pelo próprio sistema da Câmara).

Trechos esperados no texto da ata:
  "Lista de Presença na Sessão: Fulano / PP ; Beltrana / PT ..."
  "Justificativas de Ausências na Sessão: Fulano / Outros ..."
"""

import re
import subprocess
import unicodedata


def _norm(txt):
    txt = unicodedata.normalize("NFD", txt or "")
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", txt).upper().strip()


def texto_pdf(caminho):
    r = subprocess.run(["pdftotext", "-layout", str(caminho), "-"], capture_output=True, text=True)
    return re.sub(r"\s+", " ", r.stdout)


FIM_BLOCO = r"(?=Justificativas de Aus|Expedientes:|Oradores|Mat[ée]rias do Expediente|Ordem do Dia|$)"


def _nomes(trecho):
    nomes = []
    for parte in trecho.split(";"):
        nome = parte.split("/")[0].strip(" .:-")
        if nome:
            nomes.append(nome)
    return nomes


def ler_ata(caminho):
    """Devolve {"presentes": [nomes], "justificados": [nomes]} ou None se a
    ata não tiver o bloco de presença."""
    t = texto_pdf(caminho)
    m = re.search(r"Lista de Presen[çc]a na Sess[ãa]o:\s*(.*?)" + FIM_BLOCO, t, re.I)
    if not m:
        return None
    j = re.search(r"Justificativas de Aus[êe]ncias na Sess[ãa]o:\s*(.*?)(?=Expedientes:|Oradores|Mat[ée]rias do Expediente|Ordem do Dia|$)", t, re.I)
    return {"presentes": _nomes(m.group(1)), "justificados": _nomes(j.group(1)) if j else []}


def casar_nomes(nomes, parlamentares):
    """parlamentares: {id: nome_parlamentar}. Devolve (ids, nao_casados)."""
    por_nome = {_norm(n): pid for pid, n in parlamentares.items()}
    ids, falhou = set(), []
    for n in nomes:
        k = _norm(n)
        if k in por_nome:
            ids.add(por_nome[k])
            continue
        cand = [pid for nome, pid in por_nome.items() if k and (k in nome or nome in k)]
        if len(cand) == 1:
            ids.add(cand[0])
        else:
            falhou.append(n)
    return ids, falhou
