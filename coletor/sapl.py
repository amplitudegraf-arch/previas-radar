"""Coletor genérico de câmaras que usam o SAPL (Interlegis).

Baixa as coleções da API REST do SAPL, página por página, com pausa entre
as chamadas para não pesar no servidor da Câmara, e grava o JSON bruto em
dados/bruto/<cidade>/<colecao>.json.

Uso:  python3 coletor/sapl.py santana
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
UA = "PreviasRadar/0.1 (coleta de dados abertos legislativos; https://www.previas26.com.br)"
PAUSA = 0.4          # segundos entre chamadas
PAGE_SIZE = 100

CAMARAS = {
    "santana": {
        "base": "https://sapl.santana.ap.leg.br/api",
        "legislatura": 10,          # 2025–2028
        "ano_inicio": 2025,
    },
}

# (arquivo, caminho, parâmetros fixos)
def colecoes(cfg):
    leg = cfg["legislatura"]
    yield "legislaturas", "parlamentares/legislatura/", {}
    yield "parlamentares", "parlamentares/parlamentar/", {}
    yield "mandatos", "parlamentares/mandato/", {}
    yield "filiacoes", "parlamentares/filiacao/", {}
    yield "partidos", "parlamentares/partido/", {}
    yield "sessoes_legislativas", "parlamentares/sessaolegislativa/", {}
    yield "mesas_diretoras", "parlamentares/mesadiretora/", {}
    yield "composicao_mesa", "parlamentares/composicaomesa/", {}
    yield "cargos_mesa", "parlamentares/cargomesa/", {}
    yield "autores", "base/autor/", {}
    yield "tipos_materia", "materia/tipomaterialegislativa/", {}
    for ano in range(cfg["ano_inicio"], int(time.strftime("%Y")) + 1):
        yield f"materias_{ano}", "materia/materialegislativa/", {"ano": ano}
    yield "autorias", "materia/autoria/", {}
    yield "tipos_sessao", "sessao/tiposessaoplenaria/", {}
    yield "sessoes", "sessao/sessaoplenaria/", {"legislatura": leg}
    yield "presencas", "sessao/sessaoplenariapresenca/", {}
    yield "presencas_ordem_dia", "sessao/presencaordemdia/", {}
    yield "justificativas", "sessao/justificativaausencia/", {}
    yield "tipos_justificativa", "sessao/tipojustificativa/", {}
    yield "ordem_dia", "sessao/ordemdia/", {}
    yield "expediente_materias", "sessao/expedientemateria/", {}
    yield "registros_votacao", "sessao/registrovotacao/", {}
    yield "votos", "sessao/votoparlamentar/", {}


def get_json(url, tentativas=4):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            espera = 2 ** (i + 1)
            print(f"    falhou ({e}); tentando de novo em {espera}s", file=sys.stderr)
            time.sleep(espera)
    raise RuntimeError(f"não consegui baixar {url}")


def baixar_tudo(base, caminho, params):
    itens, pagina = [], 1
    while True:
        # o=id: ordem fixa. Sem ela, a API do SAPL repete registros entre
        # páginas e deixa outros de fora (o total bate, o conteúdo não).
        q = dict(params, o="id", page=pagina, page_size=PAGE_SIZE)
        dados = get_json(f"{base}/{caminho}?{urllib.parse.urlencode(q)}")
        itens += dados["results"]
        pag = dados["pagination"]
        if not pag.get("next_page"):
            break
        pagina = pag["next_page"]
        time.sleep(PAUSA)
    total = dados["pagination"]["total_entries"]
    unicos = {x["id"]: x for x in itens}
    if len(itens) != total or len(unicos) != total:
        raise RuntimeError(f"{caminho}: baixei {len(itens)} ({len(unicos)} únicos) de {total} — coleta incompleta")
    return list(unicos.values())


def baixar_atas(cfg, destino):
    """Baixa o PDF da ata de cada sessão da legislatura (fonte oficial mais
    completa da lista de presença). Só baixa de novo se a sessão mudou."""
    pasta = destino / "atas"
    pasta.mkdir(exist_ok=True)
    indice_arq = pasta / "_indice.json"
    indice = json.loads(indice_arq.read_text()) if indice_arq.exists() else {}
    novas = 0
    for s in json.loads((destino / "sessoes.json").read_text(encoding="utf-8")):
        url = (s.get("upload_ata") or "").replace("http://", "https://")
        if not url:
            continue
        chave = str(s["id"])
        pdf = pasta / f"{chave}.pdf"
        versao = f"{url}|{s.get('data_ultima_atualizacao')}"
        if pdf.exists() and indice.get(chave) == versao:
            continue
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            pdf.write_bytes(r.read())
        indice[chave] = versao
        novas += 1
        time.sleep(PAUSA)
    indice_arq.write_text(json.dumps(indice, ensure_ascii=False, indent=1))
    print(f"atas                 {novas:6d} novas/atualizadas ({len(indice)} no total)")


def main(cidade, retomar=False):
    cfg = CAMARAS[cidade]
    destino = RAIZ / "dados" / "bruto" / cidade
    destino.mkdir(parents=True, exist_ok=True)
    for nome, caminho, params in colecoes(cfg):
        if retomar and (destino / f"{nome}.json").exists():
            continue
        t0 = time.time()
        itens = baixar_tudo(cfg["base"], caminho, params)
        (destino / f"{nome}.json").write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        print(f"{nome:20s} {len(itens):6d} itens  ({time.time() - t0:.0f}s)")
        time.sleep(PAUSA)
    baixar_atas(cfg, destino)
    (destino / "_coletado_em.txt").write_text(time.strftime("%Y-%m-%dT%H:%M:%S%z"), encoding="utf-8")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "santana", retomar="--retomar" in sys.argv)
