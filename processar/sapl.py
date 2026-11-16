"""Transforma os dados brutos do SAPL num arquivo enxuto para o site.

Entrada:  dados/bruto/<cidade>/*.json   (gerados por coletor/sapl.py)
Saída:    dados/site/<cidade>.json

Regras (as mesmas para todos os vereadores — ver REGRAS e o texto em
site/como-funciona):
- Presença: só contam sessões em que a Câmara registrou a presença de
  pelo menos um vereador ("dado ausente não é falta"), e só sessões
  dentro do período do mandato do vereador.
- Propostas: cada matéria de autoria do vereador cai em um grupo, por
  tipo + palavras da ementa (classificar()).
"""

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atas  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent

CAMARAS = {
    "santana": {
        "nome": "Santana",
        "uf": "AP",
        "camara": "Câmara Municipal de Santana",
        "legislatura": 10,
        "site": "https://sapl.santana.ap.leg.br",
    },
    "porto-grande": {
        "nome": "Porto Grande",
        "uf": "AP",
        "camara": "Câmara Municipal de Porto Grande",
        "legislatura": 9,
        "site": "https://sapl.portogrande.ap.leg.br",
    },
}

# ----------------------------------------------------------------------------
# Classificação das propostas
# ----------------------------------------------------------------------------

GRUPOS = {
    "melhoria": "Pedidos de melhoria",
    "cobranca": "Perguntas e cobranças",
    "homenagem": "Homenagens",
    "lei": "Propostas de lei e emendas",
    "outros": "Outros",
}

# Tipos que não são proposta de vereador (atos da Mesa, atas, pareceres...)
TIPOS_FORA = (
    "ATA DE SESSAO", "PARECER DE COMISS", "ATO DA PRESIDENCIA", "ATO DA MESA",
    "EDITAL", "OFICIO RECEBIDO", "COMUNICADO", "ATO DE CONVOCACAO", "VETO",
    "JUSTIFICATIVA DE FALTA",
)

TIPOS_LEI = (
    "PROJETO DE LEI", "PROJETO DE DECRETO", "PROJETO DE RESOLUCAO",
    "PROPOSTA DE EMENDA", "EMENDA IMPOSITIVA",
)

PALAVRAS_HOMENAGEM = (
    "MOCAO DE APLAUSO", "APLAUSOS", "MOCAO DE PESAR", "VOTO DE PESAR", "PESAR",
    "CONGRATULA", "PARABENIZ", "HOMENAGE", "TITULO DE CIDADA", "TITULO HONORIFICO",
    "CIDADAO SANTANENSE", "CIDADA SANTANENSE", "HONRA AO MERITO", "COMENDA",
    "MEDALHA", "DENOMINA", "DIA MUNICIPAL", "SEMANA MUNICIPAL", "DATA COMEMORATIVA",
    "CALENDARIO OFICIAL", "SESSAO SOLENE", "UTILIDADE PUBLICA",
    "ALTERACAO DO NOME", "ALTERA O NOME", "DA NOME", "DENOMINACAO",
)

PALAVRAS_COBRANCA = (
    "INFORMACA", "INFORMACOE", "ESCLARECIMENT", "EXPLICAC", "CONVOCA",
    "PRESTACAO DE CONTAS", "PRESTE CONTAS", "COPIA INTEGRAL",
    "COPIA DO PROCESSO", "COPIA DOS DOCUMENTOS", "COPIAS DOS DOCUMENTOS", "COPIA DO CONTRATO",
    "COPIAS DOS CONTRATOS", "RELATORIO", "AUDITORIA", "DENUNCIA",
)

# Requerimento/indicação dirigido à própria Câmara (licença, sessão, uso da tribuna...)
PALAVRAS_INTERNO = (
    "PRESIDENTE DA CAMARA", "PRESIDENTE DESTA CASA", "MESA DIRETORA", "SOBERANO PLENARIO E CUMPRIDO",
    "LICENCA PARA", "USO DA TRIBUNA", "TRIBUNA LIVRE", "SESSAO ESPECIAL", "SESSAO ITINERANTE",
    "ARQUIVAMENTO", "RETIRADA DE PAUTA", "DESARQUIVAMENTO",
)

REGRAS = [
    ("Homenagens", "Moções de aplauso, pesar ou congratulação, títulos de cidadão, honrarias, nome de rua ou prédio, datas comemorativas, sessões solenes e títulos de utilidade pública — de qualquer tipo de documento."),
    ("Propostas de lei e emendas", "Projetos de lei, de decreto legislativo, de resolução e propostas de emenda (inclusive emendas ao orçamento), quando não forem homenagem."),
    ("Perguntas e cobranças", "Requerimentos e indicações que pedem informações, esclarecimentos, cópias de documentos ou prestação de contas, ou que convocam autoridades — mesmo quando também pedem uma obra."),
    ("Pedidos de melhoria", "Os demais requerimentos e indicações dirigidos à Prefeitura, ao Governo do Estado, a concessionárias, a parlamentares ou a órgãos públicos pedindo obra, serviço, equipamento ou recurso (inclusive os enviados por meio da Mesa Diretora)."),
    ("Outros", "Pedidos internos da Câmara (licença, uso da tribuna, sessões especiais, arquivamento), moções de repúdio e documentos que não se encaixam acima."),
]


def norm(txt):
    txt = unicodedata.normalize("NFD", txt or "")
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", txt).upper().strip()


def classificar(tipo_desc, ementa):
    t, e = norm(tipo_desc), norm(ementa)
    if any(t.startswith(x) for x in TIPOS_FORA):
        return None
    if t.startswith("MOCAO"):
        return "homenagem" if "REPUDIO" not in e else "outros"
    if any(p in e for p in PALAVRAS_HOMENAGEM):
        return "homenagem"
    if any(t.startswith(x) for x in TIPOS_LEI):
        return "lei"
    if t.startswith("REQUERIMENTO") or t.startswith("INDICACAO") or t.startswith("PEDIDO DE INFORMA"):
        if t.startswith("PEDIDO DE INFORMA") or any(p in e for p in PALAVRAS_COBRANCA):
            return "cobranca"
        # "Requer à Mesa Diretora ... que seja expedido ofício ao Prefeito" é só o
        # caminho formal de um pedido à Prefeitura — não é assunto interno.
        externo = any(p in e for p in ("OFICIO AO", "OFICIO A", "PREFEIT", "SECRETARI", "GOVERNADOR", "CONCESSIONARIA", "DIRETOR"))
        if any(p in e for p in PALAVRAS_INTERNO) and not externo:
            return "outros"
        return "melhoria"
    return "outros"


# ----------------------------------------------------------------------------

def carregar(pasta, nome):
    return json.loads((pasta / f"{nome}.json").read_text(encoding="utf-8"))


def slug(txt):
    return re.sub(r"[^a-z0-9]+", "-", norm(txt).lower()).strip("-")


def nome_bonito(txt):
    minusculas = {"de", "da", "do", "das", "dos", "e"}
    partes = (txt or "").strip().lower().split()
    return " ".join(p if p in minusculas and i else p.capitalize() for i, p in enumerate(partes))


def main(cidade):
    cfg = CAMARAS[cidade]
    bruto = RAIZ / "dados" / "bruto" / cidade
    base = cfg["site"]
    leg_id = cfg["legislatura"]

    legislaturas = {l["id"]: l for l in carregar(bruto, "legislaturas")}
    leg = legislaturas[leg_id]
    parlamentares = {p["id"]: p for p in carregar(bruto, "parlamentares")}
    partidos = {p["id"]: p for p in carregar(bruto, "partidos")}
    tipos = {t["id"]: t["descricao"] for t in carregar(bruto, "tipos_materia")}

    # ---- vereadores da legislatura (titulares e suplentes que assumiram)
    mandatos = [m for m in carregar(bruto, "mandatos") if m["legislatura"] == leg_id]
    filiacoes = defaultdict(list)
    for f in carregar(bruto, "filiacoes"):
        filiacoes[f["parlamentar"]].append(f)

    def partido_atual(pid):
        fs = sorted(filiacoes.get(pid, []), key=lambda f: f["data"] or "")
        ativas = [f for f in fs if not f["data_desfiliacao"]] or fs
        if not ativas:
            return None
        p = partidos.get(ativas[-1]["partido"])
        return p["sigla"] if p else None

    vereadores = {}
    for m in mandatos:
        p = parlamentares[m["parlamentar"]]
        v = vereadores.setdefault(p["id"], {
            "id": p["id"],
            "nome": nome_bonito(p["nome_parlamentar"]),
            "nome_completo": nome_bonito(p["nome_completo"]),
            "slug": slug(p["nome_parlamentar"]),
            "partido": partido_atual(p["id"]),
            "foto": p["fotografia"].replace("http://", "https://") if p.get("fotografia") else None,
            "email": p.get("email") or None,
            "ativo": p.get("ativo"),
            "titular": m["titular"],
            "periodos": [],
            "fonte": f"{base}/parlamentar/{p['id']}",
        })
        v["titular"] = v["titular"] or m["titular"]
        v["periodos"].append([m["data_inicio_mandato"] or leg["data_inicio"], m["data_fim_mandato"] or leg["data_fim"]])

    def em_mandato(pid, dia):
        return any(ini <= dia <= fim for ini, fim in vereadores[pid]["periodos"])

    # ---- presença (união das 3 fontes oficiais: lista de abertura, lista da
    #      Ordem do Dia e lista de presença da ata eletrônica em PDF)
    sessoes = {s["id"]: s for s in carregar(bruto, "sessoes") if s["legislatura"] == leg_id}
    tipos_sessao = {t["id"]: t["nome"] for t in carregar(bruto, "tipos_sessao")}
    tipos_just = {t["id"]: t["descricao"] for t in carregar(bruto, "tipos_justificativa")}
    hoje = date.today().isoformat()
    nomes_parl = {pid: p["nome_parlamentar"] for pid, p in parlamentares.items()}
    presentes = defaultdict(set)
    fonte_pres = defaultdict(dict)
    for arq in ("presencas", "presencas_ordem_dia"):
        for pr in carregar(bruto, arq):
            if pr["sessao_plenaria"] in sessoes:
                presentes[pr["sessao_plenaria"]].add(pr["parlamentar"])
    justificadas = defaultdict(dict)       # sessao -> {parlamentar: motivo}
    for j in carregar(bruto, "justificativas"):
        if j["sessao_plenaria"] in sessoes:
            justificadas[j["sessao_plenaria"]][j["parlamentar"]] = tipos_just.get(j["tipo_ausencia"], "Justificada")
    atas_lidas, atas_sem_lista = 0, []
    for pdf in sorted((bruto / "atas").glob("*.pdf")):
        sid = int(pdf.stem)
        if sid not in sessoes:
            continue
        r = atas.ler_ata(pdf)
        if not r:
            atas_sem_lista.append(sid)
            continue
        atas_lidas += 1
        ids, _ = atas.casar_nomes(r["presentes"], nomes_parl)
        presentes[sid] |= ids
        jids, _ = atas.casar_nomes(r["justificados"], nomes_parl)
        for pid in jids:
            justificadas[sid].setdefault(pid, "Justificada na ata")

    ordem = sorted([s for s in sessoes.values() if s["data_inicio"] <= hoje], key=lambda s: (s["data_inicio"], s["id"]))
    sessoes_com_registro = [s for s in ordem if presentes[s["id"]]]
    sessoes_sem_registro = [s for s in ordem if not presentes[s["id"]]]

    posses = sorted({m["data_inicio_mandato"] for m in mandatos if not m["titular"] and m["data_inicio_mandato"]})

    def montar_lista(pid):
        lista = []
        for s in sessoes_com_registro:
            if not em_mandato(pid, s["data_inicio"]):
                continue
            if pid in presentes[s["id"]]:
                situacao, motivo = "presente", None
            elif pid in justificadas[s["id"]]:
                situacao, motivo = "justificada", justificadas[s["id"]][pid]
            else:
                situacao, motivo = "ausente", None
            lista.append({
                "sessao": s["id"], "data": s["data_inicio"], "nome": s["__str__"],
                "tipo": tipos_sessao.get(s["tipo"], ""), "situacao": situacao, "motivo": motivo,
                "fonte": f"{base}/sessao/{s['id']}",
            })
        return lista

    listas = {pid: montar_lista(pid) for pid in vereadores}
    afastamentos = defaultdict(list)

    def marcar(pid, de, ate, texto):
        n = 0
        for x in listas[pid]:
            if de <= x["data"] <= ate and x["situacao"] == "ausente":
                x["situacao"], x["motivo"] = "afastamento", texto
                n += 1
        if n:
            afastamentos[pid].append({"de": de, "ate": ate, "sessoes": n, "motivo": texto})

    # Substituição: o suplente é do mesmo partido do titular que ele substitui.
    # Enquanto o suplente esteve em exercício (da 1ª à última presença), o
    # titular do mesmo partido sem nenhuma presença no período é tratado como
    # afastado; a sequência de ausências logo antes da posse também (a posse
    # costuma vir dias depois do afastamento). Depois que o titular volta, as
    # ausências do suplente deixam de contar (ele saiu do exercício).
    for sid_, sup in vereadores.items():
        if sup["titular"]:
            continue
        dias_pres = [x["data"] for x in listas[sid_] if x["situacao"] == "presente"]
        if not dias_pres:
            continue
        ini_ex, fim_ex = dias_pres[0], dias_pres[-1]
        candidatos = []
        for tid, tit in vereadores.items():
            if not tit["titular"] or tit["partido"] != sup["partido"]:
                continue
            no_periodo = [x for x in listas[tid] if ini_ex <= x["data"] <= fim_ex]
            if no_periodo and not any(x["situacao"] == "presente" for x in no_periodo):
                candidatos.append(tid)
        if len(candidatos) != 1:
            continue
        tid = candidatos[0]
        anteriores = [x for x in listas[tid] if x["data"] < ini_ex]
        de = ini_ex
        for x in reversed(anteriores):
            if x["situacao"] != "ausente":
                break
            de = x["data"]
        volta = [x["data"] for x in listas[tid] if x["data"] > fim_ex and x["situacao"] == "presente"]
        ate_tit = (min(volta) if volta else "9999-12-31")
        marcar(tid, de, ate_tit, f"Provável afastamento: {sup['nome']}, suplente do mesmo partido ({sup['partido']}), estava em exercício no período")
        if volta:
            marcar(sid_, min(volta), "9999-12-31", f"Fim do exercício como suplente: {vereadores[tid]['nome']}, titular do mesmo partido, voltou à Câmara")
        sup["substituiu"] = vereadores[tid]["nome"]

    for pid, v in vereadores.items():
        lista = listas[pid]
        cont = Counter(x["situacao"] for x in lista)
        consideradas = cont["presente"] + cont["ausente"] + cont["justificada"]
        v["presenca"] = {
            "sessoes_consideradas": consideradas,
            "presente": cont["presente"],
            "ausente": cont["ausente"],
            "justificada": cont["justificada"],
            "afastamento": cont["afastamento"],
            "periodos_afastamento": afastamentos[pid],
            "percentual": round(100 * cont["presente"] / consideradas, 1) if consideradas else None,
            "sessoes": lista,
        }

    # ---- propostas
    autores = {a["id"]: a for a in carregar(bruto, "autores")}
    autor_para_parl = {}
    for a in autores.values():
        rel = a.get("autor_related") or {}
        if a.get("object_id") in parlamentares and rel.get("value") == a.get("object_id"):
            autor_para_parl[a["id"]] = a["object_id"]

    materias = {}
    for arq in sorted(bruto.glob("materias_*.json")):
        for m in json.loads(arq.read_text(encoding="utf-8")):
            materias[m["id"]] = m

    autorias = defaultdict(list)          # materia -> [parlamentar]
    for au in carregar(bruto, "autorias"):
        pid = autor_para_parl.get(au["autor"])
        if pid and au["materia"] in materias and pid not in autorias[au["materia"]]:
            autorias[au["materia"]].append(pid)

    for v in vereadores.values():
        v["propostas"] = []
        v["justificativas_falta"] = []

    for mid, m in materias.items():
        if m["data_apresentacao"] < leg["data_inicio"]:
            continue
        tipo_desc = tipos.get(m["tipo"], "")
        grupo = classificar(tipo_desc, m["ementa"])
        for pid in autorias.get(mid, []):
            if pid not in vereadores:
                continue
            item = {
                "id": mid,
                "tipo": tipo_desc.capitalize() if tipo_desc.isupper() else tipo_desc,
                "numero": m["numero"],
                "ano": m["ano"],
                "data": m["data_apresentacao"],
                "ementa": re.sub(r"\s+", " ", m["ementa"] or "").strip(),
                "coautores": len(autorias[mid]) - 1,
                "fonte": f"{base}/materia/{mid}",
            }
            if norm(tipo_desc).startswith("JUSTIFICATIVA DE FALTA"):
                vereadores[pid]["justificativas_falta"].append(item)
            elif grupo:
                item["grupo"] = grupo
                vereadores[pid]["propostas"].append(item)

    for v in vereadores.values():
        v["propostas"].sort(key=lambda x: (x["data"], x["id"]), reverse=True)
        v["resumo_propostas"] = {g: sum(1 for p in v["propostas"] if p["grupo"] == g) for g in GRUPOS}

    # ---- votos nominais (data e sessão vêm da Ordem do Dia / Expediente)
    registros = {r["id"]: r for r in carregar(bruto, "registros_votacao")}
    od = {o["id"]: o["sessao_plenaria"] for o in carregar(bruto, "ordem_dia")}
    ex = {e_["id"]: e_["sessao_plenaria"] for e_ in carregar(bruto, "expediente_materias")}

    def sessao_do_registro(r):
        return od.get(r["ordem"]) if r["ordem"] else ex.get(r["expediente"])

    votos_por_registro = defaultdict(list)
    for vt in carregar(bruto, "votos"):
        votos_por_registro[vt["votacao"]].append(vt)
    votacoes_leg = [r for r in registros.values() if sessao_do_registro(r) in sessoes]
    nominais = [r for r in votacoes_leg if votos_por_registro[r["id"]]]
    for v in vereadores.values():
        v["votos"] = []
    votos_sem_presenca = 0
    for r in nominais:
        sid = sessao_do_registro(r)
        s_ = sessoes[sid]
        m = materias.get(r["materia"])
        for vt in votos_por_registro[r["id"]]:
            pid = vt["parlamentar"]
            if pid not in vereadores:
                continue
            if pid not in presentes[sid]:
                votos_sem_presenca += 1
            vereadores[pid]["votos"].append({
                "data": s_["data_inicio"],
                "sessao": s_["__str__"],
                "voto": vt["voto"],
                "materia": (r["__str__"].split(" - ", 1)[-1].split(" em ")[0]) if not m else f"{tipos.get(m['tipo'], '').capitalize()} nº {m['numero']}/{m['ano']}",
                "ementa": re.sub(r"\s+", " ", (m or {}).get("ementa") or "").strip()[:300],
                "placar": {"sim": r["numero_votos_sim"], "nao": r["numero_votos_nao"], "abstencao": r["numero_abstencoes"]},
                "fonte": f"{base}/materia/{r['materia']}" if r.get("materia") else f"{base}/sessao/{sid}",
                "fonte_sessao": f"{base}/sessao/{sid}",
            })
    for v in vereadores.values():
        v["votos"].sort(key=lambda x: x["data"], reverse=True)
        v["resumo_votos"] = dict(Counter(x["voto"] for x in v["votos"]))
    total_votos = Counter(vt["voto"] for r in nominais for vt in votos_por_registro[r["id"]])

    # ---- Mesa Diretora: cargo de cada vereador em cada ano da legislatura
    if (bruto / "composicao_mesa.json").exists():
        sls = {s["id"]: s for s in carregar(bruto, "sessoes_legislativas") if s["legislatura"] == leg_id}
        mesas = {m["id"]: sls[m["sessao_legislativa"]] for m in carregar(bruto, "mesas_diretoras") if m["sessao_legislativa"] in sls}
        cargos = {c["id"]: c["descricao"] for c in carregar(bruto, "cargos_mesa")}
        for v in vereadores.values():
            v["mesa"] = []
        for c in carregar(bruto, "composicao_mesa"):
            if c["mesa_diretora"] in mesas and c["parlamentar"] in vereadores:
                sl = mesas[c["mesa_diretora"]]
                vereadores[c["parlamentar"]]["mesa"].append({"cargo": cargos.get(c["cargo"], ""), "ano": sl["data_inicio"][:4]})
        for v in vereadores.values():
            v["mesa"].sort(key=lambda x: x["ano"])

    saida = {
        "cidade": cfg["nome"],
        "uf": cfg["uf"],
        "camara": cfg["camara"],
        "fonte": base,
        "legislatura": {"numero": leg["numero"], "inicio": leg["data_inicio"], "fim": leg["data_fim"]},
        "coletado_em": (bruto / "_coletado_em.txt").read_text(encoding="utf-8").strip() if (bruto / "_coletado_em.txt").exists() else None,
        "grupos": GRUPOS,
        "regras_classificacao": REGRAS,
        "sessoes": {
            "com_registro_presenca": len(sessoes_com_registro),
            "atas_lidas": atas_lidas,
            "posses_suplentes": posses,
            "votacoes": len(votacoes_leg),
            "votacoes_nominais": len(nominais),
            "votos_nominais": dict(total_votos),
            "votos_de_quem_nao_consta_presente": votos_sem_presenca,
            "sem_registro_presenca": [{"data": s["data_inicio"], "nome": s["__str__"], "fonte": f"{base}/sessao/{s['id']}"} for s in sorted(sessoes_sem_registro, key=lambda s: s["data_inicio"])],
        },
        "vereadores": sorted(vereadores.values(), key=lambda v: (not v["titular"], v["nome"])),
    }
    destino = RAIZ / "dados" / "site"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{cidade}.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- resumo no terminal
    print(f"{cfg['camara']} — {leg['numero']}ª legislatura ({leg['data_inicio']} a {leg['data_fim']})")
    print(f"sessões com presença registrada: {len(sessoes_com_registro)} | sem registro: {len(sessoes_sem_registro)}")
    print(f"votações: {len(votacoes_leg)} | nominais: {len(nominais)} | votos: {dict(total_votos)} | votos de quem não consta na lista de presença: {votos_sem_presenca}")
    print(f"atas lidas: {atas_lidas} | atas sem lista: {atas_sem_lista} | posses de suplentes: {posses}")
    print(f"{'vereador':28s} {'partido':10s} {'tit':3s} {'pres%':>6s} {'cons':>4s} {'pres':>4s} {'aus':>4s} {'just':>4s} {'afast':>5s}  " + " ".join(f"{g[:5]:>5s}" for g in GRUPOS) + "  votos")
    for v in saida["vereadores"]:
        pr = v["presenca"]
        print(f"{v['nome'][:28]:28s} {str(v['partido'])[:10]:10s} {'sim' if v['titular'] else 'sup':3s} "
              f"{str(pr['percentual']):>6s} {pr['sessoes_consideradas']:4d} {pr['presente']:4d} {pr['ausente']:4d} {pr['justificada']:4d} {pr['afastamento']:5d}  "
              + " ".join(f"{v['resumo_propostas'][g]:5d}" for g in GRUPOS)
              + f"  {len(v['votos']):5d}")
        for a in pr["periodos_afastamento"]:
            print(f"      {a['sessoes']:3d} sessões fora da conta ({a['de']} a {a['ate'][:10]}): {a['motivo']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "santana")
