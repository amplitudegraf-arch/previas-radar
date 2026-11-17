"""Lê a lista de presença e as justificativas de ausência das atas
eletrônicas do SAPL (PDF gerado pelo próprio sistema da Câmara).

Trechos esperados no texto da ata:
  "Lista de Presença na Sessão: Fulano / PP ; Beltrana / PT ..."
  "Justificativas de Ausências na Sessão: Fulano / Outros ..."
  "Lista de Presença na Ordem do Dia: ..." (quem chegou depois da abertura)
  "Oradores do Expediente: 1 - Fulano / PP ; 2 - ..." (quem discursou estava presente)

Em Porto Grande há atas em que um vereador discursou mas não consta da lista
de presença da abertura; por isso a presença é a união de tudo isso.
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


_ITEM = re.compile(r"\s*(?:\d+\s*-?\s*)?([A-ZÀ-Ý][A-ZÀ-Ý'. ]+?)\s*/\s*[A-Za-z]+\s*;?")


def _sequencia(t, ini):
    """Nomes "NOME / PARTIDO ;" em sequência a partir de ini; para no primeiro trecho que não é nome."""
    nomes, pos = [], ini
    while True:
        m = _ITEM.match(t, pos)
        if not m:
            return nomes
        nomes.append(m.group(1).strip())
        pos = m.end()


def outros_presentes(t):
    """Presença na Ordem do Dia + oradores (Expediente, Ordem do Dia, Explicações Pessoais)."""
    nomes = []
    for m in re.finditer(r"(?:Lista de Presen[çc]a na Ordem do Dia|Oradores d[aoe]s? (?:Expediente|Ordem do Dia|Explica[çc][õo]es Pessoais)):", t):
        nomes += _sequencia(t, m.end())
    return nomes


def ler_ata(caminho):
    """Devolve {"presentes": [nomes], "justificados": [nomes]} ou None se a
    ata não tiver o bloco de presença."""
    t = texto_pdf(caminho)
    m = re.search(r"Lista de Presen[çc]a na Sess[ãa]o:\s*(.*?)" + FIM_BLOCO, t, re.I)
    if not m:
        return None
    j = re.search(r"Justificativas de Aus[êe]ncias na Sess[ãa]o:\s*(.*?)(?=Expedientes:|Oradores|Mat[ée]rias do Expediente|Ordem do Dia|$)", t, re.I)
    return {"presentes": _nomes(m.group(1)), "justificados": _nomes(j.group(1)) if j else [],
            "outros_presentes": outros_presentes(t)}


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
