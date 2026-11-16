"""Lê bairro, rua e tema do resumo (ementa) de cada proposta.

Tudo é dedução automática a partir do texto oficial: serve para a busca por
bairro e para achar pedidos repetidos. Cada item continua com o link para o
documento original, onde o morador confere.
"""

import re
import unicodedata


def norm(txt):
    txt = unicodedata.normalize("NFD", txt or "")
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", txt).upper().strip()


# Bairros por cidade: nome que aparece no site -> grafias encontradas nas
# ementas (já sem acento, em maiúsculas). "forte": o nome é tão próprio que
# pode ser achado mesmo sem a palavra "bairro" antes.
BAIRROS = {
    "santana": [
        ("Fonte Nova", ["FONTE NOVA"], True),
        ("Mutirão do Paraíso", ["MUTIRAO DO PARAISO", "MULTIRAO DO PARAISO"], True),
        ("Paraíso", ["PARAISO"], False),
        ("Hospitalidade", ["HOSPITALIDADE"], False),
        ("Nova União", ["NOVA UNIAO"], True),
        ("Nova Brasília", ["NOVA BRASILIA"], True),
        ("Provedor II", ["PROVEDOR II", "PROVEDOR 2", "PROVEDOR LL"], True),
        ("Provedor I", ["PROVEDOR I", "PROVEDOR 1"], True),
        ("Provedor", ["PROVEDOR"], False),
        ("Elesbão", ["ELESBAO"], True),
        ("Igarapé da Fortaleza", ["IGARAPE DA FORTALEZA", "IGARAPE DA FORTELZA", "IGUARAPE DA FORTALEZA"], True),
        ("Parque das Laranjeiras", ["PARQUE DAS LARANJEIRAS", "PARQUE DA LARANJEIRA", "LARANJEIRAS"], True),
        ("Remédios II", ["REMEDIOS II", "REMEDIOS 2", "REMEDIO II", "REMEDIO 2", "REMEDIOS LL", "REMEDIO LL"], True),
        ("Remédios I", ["REMEDIOS I", "REMEDIOS 1", "REMEDIO I", "REMEDIO 1"], True),
        ("Remédios", ["REMEDIOS", "REMEDIO"], False),
        ("Novo Horizonte", ["NOVO HORIZONTE"], False),
        ("Jardim de Deus", ["JARDIM DE DEUS"], True),
        ("Jardim Floresta", ["JARDIM FLORESTA"], True),
        ("Monte das Oliveiras", ["MONTE DAS OLIVEIRAS"], True),
        ("Acquaville", ["ACQUAVILLE", "AQUAVILLE", "ACQUAVILE"], True),
        ("Piçarreira", ["PICARREIRA", "PICAREIRA"], True),
        ("Vila Amazonas", ["VILA AMAZONAS"], True),
        ("Vila Daniel", ["VILA DANIEL", "DANIEL"], False),
        ("Delta", ["DELTA"], False),
        ("Matapi Mirim", ["MATAPI MIRIM", "MATAPI MIRM"], True),
        ("Ambrósio", ["AMBROSIO"], False),
        ("Fé em Deus", ["FE EM DEUS"], True),
        ("Vale das Bênçãos", ["VALE DAS BENCAOS", "VALE DAS BENCOES"], True),
        ("Área Portuária", ["AREA PORTUARIA"], True),
        ("Área Comercial", ["AREA COMERCIAL", "COMERCIAL"], False),
        ("Centro", ["CENTRAL", "CENTRO"], False),
        ("Ilha de Santana", ["ILHA DE SANTANA"], True),
    ],
}

PALAVRA_BAIRRO = r"(?:BAIRROS?|CONJUNTO|LOTEAMENTO|RESIDENCIAL|COMUNIDADE|DISTRITO|LOCALIDADE)\s+(?:D[OAE]S?\s+)?"


def _padroes(cidade):
    saida = []
    for nome, grafias, forte in BAIRROS.get(cidade, []):
        alt = "|".join(re.escape(g) for g in sorted(grafias, key=len, reverse=True))
        fim = r"(?![A-Z0-9])"
        saida.append((nome, re.compile(PALAVRA_BAIRRO + r"(?:" + alt + r")" + fim),
                      re.compile(r"(?<![A-Z])(?:" + alt + r")" + fim) if forte else None))
    return saida


_CACHE = {}


def bairros(texto, cidade):
    if cidade not in _CACHE:
        _CACHE[cidade] = _padroes(cidade)
    t = norm(texto)
    achados = []
    usado = t
    for nome, com_palavra, solto in _CACHE[cidade]:
        m = com_palavra.search(usado) or (solto.search(usado) if solto else None)
        if m:
            achados.append(nome)
            # apaga o trecho para "Provedor I" não contar também como "Provedor"
            usado = usado[:m.start()] + " " * (m.end() - m.start()) + usado[m.end():]
    return achados


TIPOS_RUA = [
    (r"AVENIDAS?|AV\.?", "Avenida"), (r"RUAS?|R\.", "Rua"), (r"TRAVESSAS?|TRAV\.?|TV\.", "Travessa"),
    (r"ALAMEDAS?", "Alameda"), (r"PASSAGEM|PASSAGENS", "Passagem"), (r"RAMAL", "Ramal"),
    (r"ESTRADA", "Estrada"), (r"RODOVIA", "Rodovia"),
]
_L = "A-ZÀÁÂÃÇÉÊÍÓÔÕÚÜ"
_PARA = (r"NO|NA|NOS|NAS|ENTRE|ESQUINA|PR[OÓ]XIM[OA]|EM|AT[EÉ]|E\s(?:AV|RUA|TRAV)|COM|DESDE|DO\sBAIRRO|BAIRRO|QUE|"
         r"PARA|POR|NESTE|DESTE|-|–|TRECHO|LOCALIZAD[OA]")
_RUA = re.compile(
    rf"(?<![{_L}])(" + "|".join(p for p, _ in TIPOS_RUA) + rf")\s+(?!D[AEO]S?\s+(?:MUNIC[IÍ]PIO|CIDADE)\b)"
    rf"([{_L}0-9][{_L}0-9 .'-]{{1,50}}?)"
    rf"(?=\s*(?:,|;|\(|\)|$|\s(?:{_PARA})(?![{_L}])|\.\s|\.$))")
_ABREV = [(r"\bPRES\.\s*", "PRESIDENTE "), (r"\bDR\.\s*", "DOUTOR "), (r"\bPROF\.\s*", "PROFESSOR "),
          (r"\bGEN\.\s*", "GENERAL "), (r"\bCEL\.\s*", "CORONEL "), (r"\bSTA\.\s*", "SANTA "), (r"\bSTO\.\s*", "SANTO ")]
_LIXO = {"ACESSO", "PRINCIPAL", "PRINCIPAIS", "CIDADE", "MUNICIPIO", "LOCAL", "MESMA", "REFERIDA", "SUPRACITADA",
         "PUBLICA", "PUBLICAS", "TODA", "TODAS", "ADJACENTES"}


def ruas(texto):
    """Ruas citadas, na ordem do texto. A primeira costuma ser o local do
    pedido; as seguintes, em geral, são as ruas que delimitam o trecho."""
    t = re.sub(r"\s+", " ", (texto or "").upper())
    for a, b in _ABREV:
        t = re.sub(a, b, t)
    saida = []
    for m in _RUA.finditer(t):
        tipo = next(nome for p, nome in TIPOS_RUA if re.fullmatch(p, m.group(1)))
        nome = re.sub(r"\s+", " ", m.group(2)).strip(" .-'")
        nome = re.sub(r"^(?:DENOMINADA|CHAMADA|CONHECIDA COMO)\s+", "", nome)
        if len(nome) < 2 or norm(nome).split()[0] in _LIXO:
            continue
        rotulo = f"{tipo} {_titulo(nome)}"
        if rotulo not in saida:
            saida.append(rotulo)
    return saida


_MINUSC = {"DA", "DE", "DO", "DAS", "DOS", "E"}


def _titulo(nome):
    return " ".join(p.lower() if p in _MINUSC else (p if re.fullmatch(r"[IVXL]+|[A-Z]?\d+[A-Z]?", p) else p.capitalize())
                    for p in nome.split())


def chave_rua(rotulo):
    k = norm(rotulo)
    return re.sub(r"\bIZABEL\b", "ISABEL", k)


TEMAS = [
    ("Iluminação", ["ILUMINA", "LAMPADA", "LUMINARIA", "POSTEAMENTO", "REFLETOR"]),
    ("Água e esgoto", ["CSA", "AGUA POTAVEL", "ABASTECIMENTO DE AGUA", "FORNECIMENTO DE AGUA", "ESGOTO", "VAZAMENTO",
                       "CANO ", "REDE DE AGUA", "POCO ", "CAIXA D"]),
    ("Asfalto e buracos", ["ASFALT", "PAVIMENT", "TAPA-BURACO", "TAPA BURACO", "BURACO", "BLOQUETE", "TERRAPLAN",
                           "RECAPEAMENTO", "PATROLAMENTO", "PATROL", "ENCASCALH", "MESCLA"]),
    ("Pontes e passarelas", ["PONTE", "PASSARELA", "ESTIVA", "TRAPICHE"]),
    ("Drenagem e canais", ["DRENAGEM", "BUEIRO", "CANAL", "MEIO-FIO", "MEIO FIO", "SARJETA", "ALAGA", "VALA"]),
    ("Limpeza e poda", ["LIMPEZA", "CAPINA", "ROCAGEM", "ROCADA", "PODA", "LIXO", "ENTULHO", "COLETA", "TERRENO BALDIO"]),
    ("Trânsito", ["SINALIZA", "FAIXA DE PEDESTRE", "LOMBADA", "QUEBRA-MOLA", "QUEBRA MOLA", "SEMAFORO", "REDUTOR",
                  "TRANSITO", "ONIBUS", "TRANSPORTE"]),
    ("Saúde", ["SAUDE", "UBS", "MEDICO", "HOSPITAL", "ENFERMEIR", "MEDICAMENT", "AMBULANCIA", "VACINA", "SAMU"]),
    ("Educação", ["ESCOLA", "EDUCACAO", "CRECHE", "PROFESSOR", "ALUNO", "MERENDA"]),
    ("Praças, esporte e lazer", ["PRACA", "QUADRA", "CAMPO DE FUTEBOL", "ESPORT", "LAZER", "ACADEMIA", "PARQUE INFANTIL"]),
    ("Segurança", ["POLICIA", "SEGURANCA PUBLICA", "VIATURA", "GUARDA MUNICIPAL", "VIDEOMONITORAMENTO", "CAMERAS"]),
]


def tema(texto):
    t = norm(texto)
    # O começo da ementa costuma trazer o nome e o cargo do destinatário
    # ("Secretário de Saúde..."), que não diz o que foi pedido. Quando há um
    # verbo de pedido, olhamos só o que vem depois dele.
    m = re.search(r"\b(QUE SEJA|QUE SEJAM|SOLICIT|OS SERVICOS|O SERVICO|PROVIDENCI|REALIZ|INSTAL|CONSTRU|REFORM|REPAR)", t)
    trecho = t[m.start():] if m else t
    for nome, chaves in TEMAS:
        if any(c in trecho for c in chaves):
            return nome
    return "Outros pedidos"


# ---------- texto legível ----------
# Muitas ementas vêm TODAS EM MAIÚSCULAS. Para ler melhor no site, passamos
# para a escrita normal (maiúscula no começo da frase, em nomes próprios
# conhecidos e em siglas). O texto oficial continua no link da Câmara.
SIGLAS = {"SEMOP", "PMS", "CSA", "SESA", "SEMSA", "UBS", "CMS", "AP", "SEME", "CBUQ", "UPA", "SAMU", "STTRANS",
          "CEA", "DETRAN", "PM", "PMAP", "CBM", "CBMAP", "SEMED", "SEMAS", "SEMAST", "SEMAD", "SEMMA", "SEMTUR",
          "SEMDEC", "SEINF", "SEDUC", "SETRAP", "CAESA", "IAPEN", "PRF", "PF", "SUS", "CRAS", "CREAS", "CAPS", "EMEF",
          "EMEI", "LDO", "LOA", "PPA", "CPF", "INSS", "ONG", "BR", "AP-010", "CEP", "TV", "PRODAP", "SEPLAN", "DNIT",
          "ANEEL", "SEMSU", "SEMSUR", "GEA", "PMA", "SANEAMENTO"}
SIGLAS.discard("SANEAMENTO")
_HONRA = r"(senhor|senhora|sr\.|sra\.|sr|sra|governador|governadora|deputad[oa] (?:estadual|federal)|senador|senadora|vereador|vereadora)"
_PART = {"da", "de", "do", "das", "dos", "e"}


def _cap_nome(trecho):
    return " ".join(w if w in _PART else w[:1].upper() + w[1:] for w in trecho.split(" "))


def legivel(texto, nomes=()):
    letras = [c for c in texto if c.isalpha()]
    if not letras or sum(c.isupper() for c in letras) / len(letras) < 0.7:
        return texto
    original = texto
    t = texto.lower()
    # nomes de pessoas depois de "senhor", "governador" etc., até a vírgula/travessão
    t = re.sub(_HONRA + r"\s+(?!d[aeo]s?\s|que\s|a\s|o\s|prefeit|secret|govern|president|diretor|vereador|deputad|senador|ministr|comandante|superintend|coordenad)([a-zà-ÿ][a-zà-ÿ. ]{2,60}?)(?=\s*[–—\-,;(:]|\s+(?:prefeit|secret|govern|diretor|president|coordenad|superintend|comandante)|$)",
               lambda m: m.group(1) + " " + _cap_nome(m.group(2)), t)
    # nome logo depois do cargo: "prefeito municipal de santana, sebastião bala rocha,"
    def nome_apos_cargo(m):
        nome = m.group(2)
        palavras = nome.split()
        if not 2 <= len(palavras) <= 5 or any(w.endswith(("ndo", "ar", "er", "ir")) or w in {"que", "com", "para", "no", "na", "os", "as", "o", "a"} for w in palavras):
            return m.group(0)
        return m.group(1) + _cap_nome(nome)
    t = re.sub(r"((?:prefeit[oa]|secretári[oa]|governador[a]?|president[ea])[^,;]{0,60},\s+)([a-zà-ÿ][a-zà-ÿ ]{4,50}?)(?=,)", nome_apos_cargo, t)
    # nomes conhecidos: ruas, bairros, vereadores, cidades
    for n in sorted(set(nomes) | {"Santana", "Amapá", "Macapá", "Brasil", "Ilha de Santana", "Governo do Estado"}, key=len, reverse=True):
        if n:
            t = re.sub(r"(?<![a-zà-ÿ])" + re.escape(n.lower()) + r"(?![a-zà-ÿ])", n, t)
    # siglas: conhecidas, ou que aparecem depois de travessão ou entre parênteses
    sig = set(SIGLAS)
    def parece_sigla(w):
        return len(w) <= 6 and sum(c in "AEIOU" for c in w) / len(w) <= 0.5
    sig |= {w for w in re.findall(r"[–—-]\s*([A-ZÇ]{2,8})\b", original) + re.findall(r"\(([A-ZÇ]{2,8})\)", original) if parece_sigla(w)}
    for s in sig:
        t = re.sub(r"(?<![a-zà-ÿ])" + re.escape(s.lower()) + r"(?![a-zà-ÿ])", s, t)
    # algarismos romanos em nomes (Provedor ii -> Provedor II)
    t = re.sub(r"([A-ZÀ-Ý][a-zà-ÿ]+ )(i{1,3}|iv)(?![a-zà-ÿ0-9])", lambda m: m.group(1) + m.group(2).upper(), t)
    # maiúscula no começo de cada frase
    t = re.sub(r"(^|[.!?]\s+)([a-zà-ÿ])", lambda m: m.group(1) + m.group(2).upper(), t)
    return t
