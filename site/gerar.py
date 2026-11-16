"""Gera o site estático do Radar a partir de dados/site/<cidade>.json.

Saída em publico/ (HTML + CSS puros, sem JavaScript obrigatório).
Uso:  python3 site/gerar.py santana
"""

import html
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLICO = RAIZ / "publico"
# Tudo fica dentro de /ap/ (previas26.com.br/ap/...): a Vercel do domínio
# repassa esse caminho para cá. Cada cidade tem o seu endereço.
BASE = PUBLICO / "ap"
CAMINHO = {"santana": "santana/radar"}
SITE_URL = "https://www.previas26.com.br/ap/"


def pasta_cidade(cid):
    return BASE / CAMINHO.get(cid, cid)


def subir(cid, extra=0):
    """Caminho relativo da página da cidade (ou de uma subpágina) até /ap/."""
    return "../" * (len(CAMINHO.get(cid, cid).split("/")) + extra)
CONTATO_ERRO = "https://www.instagram.com/previas.ap"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def e(txt):
    return html.escape(str(txt if txt is not None else ""), quote=True)


def data_br(iso):
    if not iso:
        return ""
    a, m, d = iso[:10].split("-")
    return f"{int(d)} {MESES[int(m) - 1]} {a}"


def data_hora_br(iso):
    try:
        iso = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", iso.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d/%m/%Y às %Hh%M")
    except Exception:
        return iso or ""


def foto(cid, v, raiz):
    """Miniatura quadrada centrada no rosto (site/fotos/<cidade>/<slug>.jpg,
    gerada por site/fotos.sh a partir da foto oficial). Sem ela, usa a
    foto original da Câmara."""
    if (RAIZ / "site" / "fotos" / cid / f"{v['slug']}.jpg").exists():
        return f"{raiz}fotos/{cid}/{v['slug']}.jpg"
    return v["foto"] or ""


def num(n):
    return f"{n:,}".replace(",", ".")


def _links_locais(html_txt):
    """Na publicação, links internos ficam limpos (.../santana/radar/).
    Com RADAR_LOCAL=1 apontam para .../index.html, para abrir do disco (duplo clique)."""
    import re as _re
    if not os.environ.get("RADAR_LOCAL"):
        return html_txt
    def troca(m):
        url, ancora = m.group(1), m.group(2) or ""
        if url == "":
            url = "./"
        if url.endswith("/"):
            url += "index.html"
        return f'href="{url}{ancora}"'
    return _re.sub(r'href="((?:\.\./|[a-z0-9-]+/)*)(#[^"]*)?"', troca, html_txt)


def pagina(titulo, corpo, descricao="", raiz="../", voltar=None):
    return _links_locais(_pagina(titulo, corpo, descricao, raiz, voltar))


def _pagina(titulo, corpo, descricao="", raiz="../", voltar=None):
    volta = f'<a class="voltar" href="{e(voltar[0])}">← {e(voltar[1])}</a>' if voltar else ""
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800;900&family=Inter:wght@400;600;700&display=swap">
<link rel="stylesheet" href="{raiz}estilo.css">
<link rel="icon" type="image/png" href="{raiz}favicon.png">
</head>
<body>
<header class="topo"><a href="{raiz}" class="marca"><img src="{raiz}logo-previas.png" alt="Prévias" width="105" height="28"><span>Radar</span></a></header>
<main>
{volta}
{corpo}
</main>
<footer class="rodape">
<p>O Radar mostra só dados oficiais publicados pelas Câmaras. Não damos nota nem opinião.</p>
<p>Achou um erro? <a href="{CONTATO_ERRO}" target="_blank" rel="noopener">Avise pelo Instagram @previas.ap</a> — corrigimos rápido.</p>
</footer>
</body>
</html>
"""


ESTILO = """
:root{--txt:#1d2433;--sub:#5b6474;--linha:#e5e7eb;--fundo:#fff;--suave:#f6f7f9;--azul:#283C59;--acento:#b8860b;--ok:#1f7a4d;--nao:#b42318}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--txt);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--azul)}
main{max-width:760px;margin:0 auto;padding:16px}
.topo{background:var(--azul);padding:12px 16px}
.marca{display:inline-flex;align-items:center;gap:10px;color:#F5EFE3;text-decoration:none}
.marca img{display:block;height:28px;width:auto}
.marca span{font-weight:600;opacity:.8;padding-left:10px;border-left:1px solid rgba(245,239,227,.35);line-height:20px}
h1{font-size:26px;line-height:1.2;margin:12px 0 4px}
h2{font-size:20px;margin:28px 0 8px}
.sub{color:var(--sub);margin:0 0 12px}
.voltar{display:inline-block;margin:4px 0 8px;text-decoration:none;font-size:15px}
.aviso{background:var(--suave);border-left:4px solid var(--azul);padding:12px 14px;border-radius:6px;font-size:15px;margin:16px 0}
.cards{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));margin:16px 0}
.card{display:flex;gap:12px;align-items:center;border:1px solid var(--linha);border-radius:12px;padding:12px;text-decoration:none;color:inherit}
.card:hover{border-color:var(--azul)}
.card img,.foto{width:56px;height:56px;border-radius:50%;object-fit:cover;background:var(--suave);flex:none}
.card b{display:block;line-height:1.25}
.card small{color:var(--sub)}
.perfil{display:flex;gap:16px;align-items:center;margin:8px 0 4px}
.perfil .foto{width:88px;height:88px}
.numeros{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:12px 0}
.numero{background:var(--suave);border-radius:10px;padding:12px}
.numero strong{display:block;font-size:26px;line-height:1.1}
.numero span{font-size:14px;color:var(--sub)}
.numero a{font-size:13px}
details{border:1px solid var(--linha);border-radius:10px;margin:8px 0;padding:0 12px}
summary{cursor:pointer;padding:12px 0;font-weight:600;list-style-position:inside}
summary small{font-weight:400;color:var(--sub)}
ul.itens{list-style:none;margin:0 0 12px;padding:0}
ul.itens li{border-top:1px solid var(--linha);padding:10px 0;font-size:15px}
ul.itens li small{color:var(--sub);display:block}
.tag{display:inline-block;font-size:12px;padding:2px 8px;border-radius:999px;background:var(--suave);color:var(--sub);margin-right:6px}
.v-sim{color:var(--ok);font-weight:700}.v-nao{color:var(--nao);font-weight:700}
.rodape{max-width:760px;margin:32px auto 0;padding:16px;border-top:1px solid var(--linha);color:var(--sub);font-size:14px}
[hidden]{display:none!important}
.salario{background:var(--azul);color:#F5EFE3;border-radius:14px;padding:16px;margin:16px 0}
.salario p{margin:0;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;opacity:.85}
.salario strong{display:block;font-size:clamp(30px,8vw,44px);line-height:1.15;font-variant-numeric:tabular-nums;margin:4px 0}
.salario small{font-size:13px;opacity:.85;display:block}
.salario a{color:#F5EFE3}
.aovivo{display:inline-block;font-size:13px;color:var(--sub);margin:8px 0 0}
.aovivo:before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:#d4673a;margin-right:6px;vertical-align:1px}
section{margin-top:40px}
.olho{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--acento);margin:0}
section h2{margin-top:2px;font-size:24px}
.nota{font-size:14px;color:var(--sub)}
input[type=search],select{font:inherit;padding:12px 14px;border:1px solid var(--linha);border-radius:10px;background:#fff;color:var(--txt);width:100%}
input[type=search]:focus,select:focus{outline:2px solid var(--azul);border-color:transparent}
.chips{display:flex;gap:8px;overflow-x:auto;padding:10px 0 4px;scrollbar-width:none}
.chip{font:inherit;font-size:14px;white-space:nowrap;border:1px solid var(--linha);background:var(--suave);border-radius:999px;padding:6px 12px;cursor:pointer;color:var(--txt)}
.chip.ativo{background:var(--azul);color:#fff;border-color:var(--azul)}
.total{display:flex;align-items:baseline;gap:10px;margin:18px 0 6px}
.total strong{font-size:44px;line-height:1;color:var(--azul)}
.bloco{margin:18px 0}
.bloco h3{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--sub);margin:0 0 8px}
.rank{display:grid;grid-template-columns:1fr auto;gap:2px 10px;align-items:center;padding:6px 0;border-top:1px solid var(--linha);text-decoration:none;color:inherit;font-size:15px}
.rank .trilho{grid-column:1/-1;height:6px;background:var(--suave);border-radius:3px;overflow:hidden}
.rank .trilho span{display:block;height:100%;background:var(--azul);border-radius:3px}
.rank b{font-variant-numeric:tabular-nums}
.pedido{border-top:1px solid var(--linha);padding:12px 0;font-size:15px}
.pedido small{color:var(--sub);display:block;margin-top:4px}
.mais{font:inherit;width:100%;padding:12px;margin:10px 0;border:0;border-radius:10px;background:var(--azul);color:#fff;font-weight:600;cursor:pointer}
.rep{border:1px solid var(--linha);border-radius:12px;margin:10px 0;padding:0}
.rep summary{display:grid;grid-template-columns:64px 1fr;gap:12px;align-items:center;padding:12px;list-style:none}
.rep summary::-webkit-details-marker{display:none}
.rep .vezes{text-align:center;color:#d4673a;font-weight:800;font-size:30px;line-height:1}
.rep .vezes small{display:block;font-size:10px;letter-spacing:.08em;color:var(--sub);font-weight:600}
.rep .onde b{display:block}
.rep .onde small{color:var(--sub);font-weight:400}
.rep .itens{padding:0 12px}
.barra{display:flex;width:100%;border-radius:4px;overflow:hidden;background:var(--suave)}
.barra span{display:block;height:100%}
.legenda{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;margin:10px 0 16px}
.legenda i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px}
.linha-ver{display:block;padding:8px 0;border-top:1px solid var(--linha);text-decoration:none;color:inherit}
.linha-ver span{display:flex;justify-content:space-between;gap:8px;font-size:15px;margin-bottom:5px}
.linha-ver small{color:var(--sub)}
.filtros{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.filtros #nome{grid-column:1/-1}
/* ---------- Radar: layout no padrão do manual, cores da Prévias ---------- */
:root{--ink:#1E2C42;--azul:#283C59;--bege:#F5EFE3;--areia:#EFE7D8;--ouro:#B8860B;--alerta:#B9472E;--linha:#E6E1D6;--suave:#F6F3EC;--sub:#5D6676;--sombra:0 1px 2px rgba(30,44,66,.06),0 6px 18px rgba(30,44,66,.06)}
body{font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:#FFFDF9}
main{max-width:1040px}
h1,h2,h3,.titulo,.stats strong,.salario strong,.total strong,.rep .vezes,.grupo strong,.cracha h3,.caixa b,.anel b{font-family:Archivo,Inter,system-ui,sans-serif}
.titulo{font-size:clamp(44px,11vw,84px);font-weight:900;letter-spacing:-.03em;line-height:.95;margin:14px 0 10px;color:var(--azul);text-transform:uppercase}
.titulo span{color:var(--ouro);display:block}
.lead{font-size:18px;max-width:560px;margin:0 0 14px}
.salario{background:var(--azul);border-radius:18px;padding:18px 20px;box-shadow:var(--sombra)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}
.stats div{background:var(--suave);border-radius:14px;padding:12px 14px}
.stats strong{display:block;font-size:clamp(24px,5vw,34px);font-weight:800;color:var(--cor,var(--ink));line-height:1.1}
.stats span{font-size:13px;color:var(--sub)}
section h2{font-size:clamp(28px,6vw,42px);font-weight:800;letter-spacing:-.02em;line-height:1.05;color:var(--ink)}
.olho{color:var(--sub)}
.caixa-busca{display:flex;align-items:center;gap:10px;border:1.5px solid var(--ink);border-radius:14px;padding:0 14px;background:#fff}
.caixa-busca svg{color:var(--sub);flex:none}
.caixa-busca input{border:0;padding:14px 0;outline:none}
.caixa-busca:focus-within{box-shadow:0 0 0 3px rgba(40,60,89,.15)}
.chip{background:#fff;font-weight:600}
.chip.ativo{background:var(--azul);border-color:var(--azul)}
.painel{border:1px solid var(--linha);border-radius:22px;padding:18px;margin-top:14px;background:#fff;box-shadow:var(--sombra)}
.total strong{font-size:clamp(44px,10vw,64px);font-weight:900;color:var(--azul)}
.total span{max-width:200px;line-height:1.25}
.colunas{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.bloco h3{font-family:Inter,sans-serif;font-weight:700;font-size:12px}
.rank{grid-template-columns:auto 1fr auto;column-gap:10px;border-top:0;padding:7px 0}
.rank .trilho{grid-column:2/-1;height:5px;background:var(--suave)}
.rank .trilho span{background:var(--azul)}
.rank .nome{font-size:14.5px;line-height:1.25}
.rank .nome small{color:var(--sub)}
.av{width:30px;height:30px;border-radius:50%;object-fit:cover;background:var(--areia);flex:none;display:inline-block;vertical-align:middle}
.ic{width:30px;height:30px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;flex:none;background:var(--f,#eef);color:var(--c,#333)}
.ic svg{width:17px;height:17px}
button.rank{font:inherit;background:none;border:0;width:100%;text-align:left;cursor:pointer;color:var(--azul);font-weight:600}
.pedido{display:grid;grid-template-columns:auto 1fr;gap:12px;border:1px solid var(--linha);border-radius:16px;padding:14px;margin:10px 0;background:#fff}
.pedido .txt{font-weight:600;line-height:1.4;font-size:15px}
.pedido .meta{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;margin-top:8px;font-size:13px;color:var(--sub)}
.selo{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;background:var(--f);color:var(--c)}
.selo svg{width:13px;height:13px}
.pedido .rodape-ped{grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;font-size:13px}
.autores{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center}
.autores span{display:inline-flex;align-items:center;gap:6px;font-weight:600}
.autores .av{width:22px;height:22px}
.abrir{font-weight:600;text-decoration:none;white-space:nowrap}
.mais{background:var(--ink);border-radius:12px;font-family:Inter,sans-serif}
.grade-rep{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.rep{margin:0;border-radius:18px;background:#fff;box-shadow:var(--sombra)}
.rep[open]{grid-column:1/-1}
.rep summary{grid-template-columns:auto 1fr;align-items:start;cursor:pointer;padding:16px}
.rep .vezes{color:var(--alerta);font-size:40px;font-weight:900;min-width:56px}
.rep .onde b{font-family:Archivo,sans-serif;font-size:17px;line-height:1.2}
.rep .onde .meta{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px;font-size:13px;color:var(--sub)}
.rep .cobrar{display:block;color:var(--alerta);font-weight:700;font-size:14px;margin-top:10px}
.rep[open] .cobrar:after{content:" (fechar)"}
.rep .itens{padding:0 16px 8px}
.barra.grossa{height:14px;border-radius:999px;margin:14px 0}
.barra span+span{margin-left:3px}
.grupos{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.grupo{border-radius:20px;padding:18px}
.grupo strong{font-size:40px;font-weight:900;color:var(--cor);line-height:1}
.grupo p{margin:6px 0;font-size:16px}
.grupo small{color:#3d4554;font-size:14px;line-height:1.45;display:block}
.filtros{grid-template-columns:repeat(3,1fr);gap:10px}
.filtros #nome{grid-column:auto}
.filtros label{font-size:13px;font-weight:600;color:var(--sub);display:flex;flex-direction:column;gap:5px}
.filtros input,.filtros select{background:var(--suave);border-color:transparent}
.crachas{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin-top:10px}
.cracha{border:1px solid var(--linha);border-radius:26px;overflow:hidden;background:#fff;box-shadow:var(--sombra);display:flex;flex-direction:column;min-width:0}
.cracha header{position:relative;padding:22px 16px 14px}
.cracha .furo{position:absolute;top:10px;left:50%;width:54px;height:8px;margin-left:-27px;border-radius:999px;background:#fff;box-shadow:inset 0 1px 2px rgba(0,0,0,.12)}
.cracha .quem{display:flex;gap:14px;align-items:center}
.cracha .quem img,.cracha .sem-foto{width:92px;height:92px;border-radius:50%;object-fit:cover;border:3px solid var(--azul);background:var(--areia);flex:none}
.cracha h3{font-size:26px;font-weight:800;margin:0;line-height:1.05;letter-spacing:-.01em}
.cracha h3 a{color:var(--ink);text-decoration:none}
.cracha .quem small{color:var(--sub);font-size:13px;display:block;margin-top:4px}
.pills{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.pill{font-size:12px;font-weight:700;padding:3px 9px;border-radius:7px}
.pill.escuro{background:var(--ink);color:#fff}
.pill.claro{background:#fff;color:var(--ink)}
.cracha .corpo{padding:16px 18px 18px}
.pres{display:flex;gap:14px;align-items:center}
.pres p{margin:0;font-size:15px}
.pres small{display:block;color:var(--sub);font-size:13px}
.falta{color:var(--alerta);font-weight:700}
.anel{position:relative;width:76px;height:76px;flex:none}
.anel b{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:19px;font-weight:800}
.anel b.cheio{font-size:16px}
.anel.vazio{border:9px solid #E7E1D4;border-radius:50%}
.caixas,.votos{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0}
.caixa{background:var(--suave);border-radius:12px;padding:10px 12px}
.caixa b{display:block;font-size:20px;font-weight:800}
.caixa span{font-size:12.5px;color:var(--sub)}
.caixa.sim{background:#E6F2EA}.caixa.nao{background:#F8E7E3}
.cracha h4{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--sub);margin:16px 0 8px}
.cracha .barra{height:7px;border-radius:999px}
.linhas{margin-top:6px}
.lin{display:flex;align-items:center;gap:10px;padding:7px 2px;text-decoration:none;color:var(--txt);font-size:15px}
.lin i{width:10px;height:10px;border-radius:3px;flex:none}
.lin b{margin-left:auto;font-variant-numeric:tabular-nums}
.lin em{font-style:normal;color:var(--sub)}
.rep{cursor:pointer;text-align:left;font:inherit;color:inherit;border:1px solid var(--linha);width:100%;display:grid;grid-template-columns:auto 1fr;gap:12px;padding:16px;align-items:start}
.rep:hover{border-color:var(--azul)}
.rep small{color:var(--sub)}
.folha{border:0;padding:0;border-radius:22px;width:min(720px,calc(100% - 24px));max-height:calc(100% - 24px);box-shadow:0 20px 60px rgba(0,0,0,.25);background:#FFFDF9;color:var(--txt)}
.folha::backdrop{background:rgba(30,44,66,.55)}
.folha-in{position:relative;padding:22px 20px 20px}
.fechar{position:absolute;top:12px;right:12px;width:38px;height:38px;border-radius:50%;border:0;background:var(--suave);font-size:24px;line-height:1;cursor:pointer;color:var(--ink)}
.folha-topo{display:flex;gap:12px;align-items:center;padding-right:44px}
.folha-topo .ic{width:44px;height:44px;border-radius:12px}
.folha-topo .ic svg{width:22px;height:22px}
.folha-topo h2{margin:0;font-size:26px}
.folha-topo p{margin:2px 0 0;color:var(--sub);font-size:14px}
.cob{background:#fff;border:1px solid var(--linha);border-radius:18px;padding:16px;margin:16px 0}
.cob h3{margin:0 0 4px;font-size:20px}
.cob p{margin:0 0 12px;color:var(--sub);font-size:14.5px}
.campo{display:flex;flex-direction:column;gap:5px;font-size:13px;font-weight:700;color:var(--sub);margin:10px 0}
.campo select,.campo textarea{font:inherit;font-size:15px;font-weight:400;color:var(--txt);border:1px solid var(--linha);border-radius:12px;padding:10px 12px;background:var(--suave)}
.campo textarea{min-height:150px;resize:vertical;line-height:1.45}
.acoes{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;font:inherit;font-weight:700;font-size:14.5px;padding:11px 16px;border-radius:12px;border:0;cursor:pointer;text-decoration:none;background:var(--azul);color:#fff}
.btn.wa{background:#1F7A4D}
.btn.claro{background:var(--suave);color:var(--ink)}
.contato{font-size:13.5px;color:var(--sub);margin-top:10px}
.folha h4{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--sub);margin:18px 0 6px}
.cracha .links{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;border-top:1px solid var(--linha);padding-top:12px;margin:14px 0 0;font-size:14px;font-weight:600}
.cracha .links a{text-decoration:none}
.transp{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.transp div{background:var(--suave);border-radius:16px;padding:14px 16px}
.transp h3{margin:0 0 6px;font-size:17px}
.transp p{margin:0;font-size:14.5px;color:#3d4554}
@media (max-width:760px){
 .stats{grid-template-columns:repeat(2,1fr)}
 .colunas,.grade-rep,.grupos,.crachas,.transp{grid-template-columns:1fr}
 .filtros{grid-template-columns:1fr 1fr}
 .filtros label:first-child{grid-column:1/-1}
}
table{border-collapse:collapse;width:100%;font-size:15px}
td,th{text-align:left;padding:8px 6px;border-bottom:1px solid var(--linha);vertical-align:top}
"""


def card_vereador(v, raiz_cidade):
    pr = v["presenca"]
    pres = f"{pr['percentual']:.0f}% de presença".replace(".", ",") if pr["percentual"] is not None else "sem registro de presença"
    foto = f'<img src="{e(v["foto"])}" alt="" loading="lazy">' if v["foto"] else '<span class="foto"></span>'
    sup = "" if v["titular"] else " · suplente"
    return (f'<a class="card" href="{raiz_cidade}{e(v["slug"])}/">{foto}<span><b>{e(v["nome"])}</b>'
            f'<small>{e(v["partido"] or "sem partido informado")}{sup}</small><br>'
            f'<small>{pres} · {num(len(v["propostas"]))} propostas</small></span></a>')


# Salário (subsídio) bruto mensal, da tabela oficial publicada pela Câmara.
# O contador do topo é estimativa: cadeiras x valor mensal, proporcional ao
# tempo desde a posse, sem 13º, férias nem verba indenizatória.
SALARIOS = {
    "santana": {
        "cadeiras": 15,
        "valor": 9032,
        "mesa": [["Presidente", 18064], ["1º(ª) Secretário(a)", 13548]],
        "documento": "Tabela Padrão Remuneratório Vereadores — vigente para o exercício de 2026",
        "fonte": "https://www.santana.ap.leg.br/transparencia-old/gestao-de-pessoas/folha-de-pagamento-servidores/padrao-remuneratorio/tabela-remuneratoria-vereadores",
    },
}


def salario_mensal(sal):
    """Soma do mês: vereadores comuns + cargos da Mesa com acréscimo."""
    return (sal["cadeiras"] - len(sal["mesa"])) * sal["valor"] + sum(v for _, v in sal["mesa"])


def brl(v):
    return "R$ " + f"{v:,.0f}".replace(",", ".")


NOMES_PROPRIOS = []


def ementa_legivel(txt):
    sys.path.insert(0, str(RAIZ / "processar"))
    import lugares as L
    return L.legivel(txt, NOMES_PROPRIOS + L.ruas(txt))


CORES_GRUPO = {"melhoria": "#2F5B9A", "cobranca": "#B9722A", "homenagem": "#A4456A", "lei": "#2F7D5B", "outros": "#7B8594"}
FUNDO_GRUPO = {"melhoria": "#E9EFF8", "cobranca": "#FBF1E4", "homenagem": "#F8E9EF", "lei": "#E5F2EA", "outros": "#EEF0F3"}
DESCR_GRUPO = {
    "melhoria": "Tapar buraco, trocar lâmpada, limpar canal, consertar ponte. É um pedido: a Prefeitura decide se faz.",
    "cobranca": "Pedidos de informação, cópias de documentos, prestação de contas e convocação de autoridades.",
    "homenagem": "Moções de aplauso e de pesar, títulos de cidadão, nomes de rua e datas comemorativas.",
    "lei": "Projetos que criam regra, programa ou obrigação na cidade, e emendas, inclusive ao orçamento.",
    "outros": "Pedidos internos da Câmara, moções de repúdio e documentos que não se encaixam nos outros grupos.",
}
# fundo do crachá: tons da Prévias, em rodízio (não tem relação com partido)
FUNDOS_CRACHA = ["#F5EFE3", "#E8EEF6", "#EFE7D8", "#E7EEEA", "#F3E9E4", "#ECEAF3"]

ICONES = {
    "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "seta": '<path d="M7 17 17 7M9 7h8v8"/>',
    "busca": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
}


def icone(nome, tam=18):
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONES[nome]}</svg>')


def montar_pedidos(cid, d, fotos):
    """Junta as propostas sem repetir (documento com vários autores aparece
    uma vez) e lê bairro, rua e tema de cada pedido."""
    sys.path.insert(0, str(RAIZ / "processar"))
    import lugares as L
    global NOMES_PROPRIOS
    NOMES_PROPRIOS = [v["nome"] for v in d["vereadores"]] + [b[0] for b in L.BAIRROS.get(cid, [])]
    uni = {}
    for i, v in enumerate(d["vereadores"]):
        for p in v["propostas"]:
            uni.setdefault(p["id"], dict(p, autores=[]))["autores"].append(i)
    todas = sorted(uni.values(), key=lambda p: (p["data"], p["id"]), reverse=True)
    pedidos = []
    for p in todas:
        if p["grupo"] not in ("melhoria", "cobranca"):
            continue
        ruas_p = L.ruas(p["ementa"])
        pedidos.append({"i": p["id"], "d": p["data"], "t": f'{p["tipo"]} nº {p["numero"]}/{p["ano"]}',
                        "e": L.legivel(p["ementa"], NOMES_PROPRIOS + ruas_p), "g": p["grupo"], "b": L.bairros(p["ementa"], cid), "r": L.ruas(p["ementa"]),
                        "m": L.tema(p["ementa"]), "a": p["autores"], "f": p["fonte"]})
    # pedido repetido: mesma rua (a primeira citada), mesmo bairro, mesmo tema
    grupos = {}
    for p in pedidos:
        if not p["r"] or p["m"] == "Outros pedidos":
            continue
        k = (L.chave_rua(p["r"][0]), p["b"][0] if p["b"] else "", p["m"])
        grupos.setdefault(k, []).append(p)
    rep = []
    for (kr, b, m), ps in grupos.items():
        if len(ps) < 3:
            continue
        nomes = {}
        for p in ps:
            nomes[p["r"][0]] = nomes.get(p["r"][0], 0) + 1
        autores = {a for p in ps for a in p["a"]}
        rep.append({"r": max(nomes, key=nomes.get), "b": b, "m": m, "n": len(ps), "a": len(autores),
                    "d0": min(p["d"] for p in ps), "d1": max(p["d"] for p in ps), "ids": [p["i"] for p in ps]})
    rep.sort(key=lambda x: (x["n"], x["a"], x["d1"]), reverse=True)
    return todas, pedidos, rep


def cargo_atual(v):
    """Cargo na Mesa Diretora no ano mais recente registrado."""
    if not v.get("mesa"):
        return None
    ult = max(m["ano"] for m in v["mesa"])
    return next(m["cargo"] for m in v["mesa"] if m["ano"] == ult)


def salario_de(v, sal):
    if not sal:
        return None
    c = (cargo_atual(v) or "").lower()
    if c == "presidente":
        return sal["mesa"][0][1]
    if c.startswith("primeiro-secret") or c.startswith("1º secret") or c.startswith("1º(ª) secret"):
        return sal["mesa"][1][1]
    return sal["valor"]


def anel(pct, cor="#283C59"):
    if pct is None:
        return '<div class="anel vazio"><b>—</b></div>'
    r = 30
    c = 2 * 3.14159 * r
    cls = ' class="cheio"' if round(pct) >= 100 else ""
    return (f'<div class="anel"><svg viewBox="0 0 76 76" width="76" height="76" aria-hidden="true">'
            f'<circle cx="38" cy="38" r="{r}" fill="none" stroke="#E7E1D4" stroke-width="9"/>'
            f'<circle cx="38" cy="38" r="{r}" fill="none" stroke="{cor}" stroke-width="9" stroke-dasharray="{c * pct / 100:.1f} {c:.1f}" '
            f'transform="rotate(-90 38 38)"/></svg><b{cls}>{pct:.0f}%</b></div>')


def cracha(i, v, d, sal, fotos):
    pr = v["presenca"]
    rp = v["resumo_propostas"]
    grupos = d["grupos"]
    tot = sum(rp.values())
    f = fotos[i]
    foto_html = f'<img src="{e(f)}" alt="Foto de {e(v["nome"])}" loading="lazy">' if f else '<span class="sem-foto"></span>'
    cargo = cargo_atual(v)
    pills = f'<span class="pill escuro">{e(v["partido"] or "sem partido")}</span>'
    if cargo:
        pills += f'<span class="pill claro">{e(cargo)} da Câmara</span>'
    if not v["titular"]:
        ini = v["periodos"][0][0] if v.get("periodos") else ""
        pills += f'<span class="pill claro">Suplente · assumiu em {data_br(ini)}</span>' if ini else '<span class="pill claro">Suplente</span>'
    nome_comp = v.get("nome_completo") or ""
    nome_comp = f'<small>{e(nome_comp)}</small>' if nome_comp and nome_comp.upper() != v["nome"].upper() else ""

    if pr["sessoes_consideradas"]:
        presenca = (f'<div class="pres">{anel(pr["percentual"])}<div><p><b>{pr["presente"]} de {pr["sessoes_consideradas"]}</b> sessões até agora</p>'
                    f'<small>{pr["justificada"]} {"ausência justificada" if pr["justificada"] == 1 else "ausências justificadas"} · '
                    f'<span class="{"falta" if pr["ausente"] else ""}">{pr["ausente"]} sem justificativa</span></small>'
                    + (f'<small>{sum(a["sessoes"] for a in pr["periodos_afastamento"])} sessões fora da conta (afastamento)</small>' if pr["periodos_afastamento"] else "")
                    + '</div></div>')
    else:
        presenca = '<div class="pres">' + anel(None) + '<div><p>Sem presença registrada no período</p></div></div>'

    s = salario_de(v, sal)
    caixas = ""
    if s:
        caixas += f'<div class="caixa"><b>{brl(s)}</b><span>salário por mês</span></div>'
    caixas += f'<div class="caixa"><b>{num(tot)}</b><span>propostas até agora</span></div>'

    barra = "".join(f'<span style="width:{rp[g] / (tot or 1) * 100:.2f}%;background:{CORES_GRUPO[g]}"></span>' for g in grupos if rp[g])
    linhas = "".join(
        f'<a class="lin" href="{e(v["slug"])}/#propostas"><i style="background:{CORES_GRUPO[g]}"></i>{e(n)}<b>{num(rp[g])}</b><em>›</em></a>'
        for g, n in grupos.items())

    rv = v.get("resumo_votos") or {}
    sim = rv.get("Sim", 0)
    nao = sum(n for k, n in rv.items() if k != "Sim")
    votos = (f'<div class="votos"><div class="caixa sim"><b>{num(sim)}</b><span>vezes sim</span></div>'
             f'<div class="caixa nao"><b>{num(nao)}</b><span>{"não ou abstenção" if nao != rv.get("Não", 0) else "vezes não"}</span></div></div>')

    fundo = FUNDOS_CRACHA[i % len(FUNDOS_CRACHA)]
    pct = pr["percentual"] if pr["percentual"] is not None else 999
    return f"""<article class="cracha" data-nome="{e(v['nome'])}" data-partido="{e(v['partido'] or '')}" data-pres="{pct}" data-lei="{rp['lei']}" data-hom="{rp['homenagem']}" data-mel="{rp['melhoria']}" data-tot="{tot}" data-nao="{nao}">
<header style="background:{fundo}"><span class="furo"></span>
<div class="quem">{foto_html}<div><h3><a href="{e(v['slug'])}/">{e(v['nome'])}</a></h3>{nome_comp}</div></div>
<div class="pills">{pills}</div></header>
<div class="corpo">
{presenca}
<div class="caixas">{caixas}</div>
<h4>O que propôs até agora</h4>
<div class="barra">{barra}</div>
<div class="linhas">{linhas}</div>
<h4>Como votou até agora</h4>
{votos}
<p class="links"><a href="{e(v['slug'])}/">Ver página completa →</a><a href="{e(v['fonte'])}" target="_blank" rel="noopener">Ficha oficial na Câmara ↗</a></p>
</div></article>"""


def gerar_cidade(cid, d):
    pasta = pasta_cidade(cid)
    pasta.mkdir(parents=True, exist_ok=True)
    R = subir(cid)
    leg = d["legislatura"]
    atualizado = data_hora_br(d["coletado_em"]) if d.get("coletado_em") else ""
    fotos = [foto(cid, v, R) for v in d["vereadores"]]
    todas, pedidos, rep = montar_pedidos(cid, d, fotos)
    conta = {g: sum(1 for p in todas if p["grupo"] == g) for g in d["grupos"]}
    sal = SALARIOS.get(cid)

    # sexo vem do cadastro oficial (para "vereador"/"vereadora" na mensagem de cobrança)
    sexo = {}
    arq_parl = RAIZ / "dados" / "bruto" / cid / "parlamentares.json"
    if arq_parl.exists():
        sexo = {p["id"]: p.get("sexo") or "" for p in json.loads(arq_parl.read_text(encoding="utf-8"))}
    # Contato: só o e-mail publicado pela Câmara. Telefones do cadastro ficam de
    # fora porque não dá para garantir que não sejam números pessoais.
    ver_js = [{"s": v["slug"], "n": v["nome"], "p": v["partido"] or "", "f": fotos[i], "e": v.get("email") or "",
               "x": sexo.get(v["id"], "")} for i, v in enumerate(d["vereadores"])]
    dados_js = {"pedidos": pedidos, "rep": rep, "ver": ver_js}
    bloco_sal = ""
    if sal:
        mensal = salario_mensal(sal)
        dados_js["sal"] = {"mensal": mensal, "posse": leg["inicio"]}
        mesa = " e ".join(f"{n.lower()} {brl(v)}" for n, v in sal["mesa"])
        bloco_sal = f"""<div class="salario">
<p>Salário pago aos {sal['cadeiras']} vereadores desde a posse</p>
<strong id="contador">{brl(0)}</strong>
<small>e subindo agora · estimativa: {sal['cadeiras']} salários por mês ({brl(sal['valor'])} cada; {mesa}) desde {data_br(leg['inicio'])}. Valor bruto da <a href="{e(sal['fonte'])}" target="_blank" rel="noopener">tabela oficial da Câmara</a>, sem 13º nem verba indenizatória.</small>
</div>"""
    (pasta / "dados.js").write_text("window.RADAR=" + json.dumps(dados_js, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

    cont_b = {}
    for p in pedidos:
        for b in p["b"]:
            cont_b[b] = cont_b.get(b, 0) + 1
    atalhos = "".join(f'<button type="button" class="chip" data-q="{e(b)}">{e(b)}</button>'
                      for b, _ in sorted(cont_b.items(), key=lambda x: -x[1])[:10])

    total = sum(conta.values()) or 1
    barra_cidade = "".join(f'<span style="width:{conta[g] / total * 100:.2f}%;background:{CORES_GRUPO[g]}"></span>' for g in d["grupos"] if conta[g])
    cartoes_grupo = "".join(
        f'<div class="grupo" style="background:{FUNDO_GRUPO[g]};--cor:{CORES_GRUPO[g]}"><strong>{num(conta[g])}</strong>'
        f'<p><b>{e(n)}</b> até agora</p><small>{e(DESCR_GRUPO[g])}</small></div>'
        for g, n in d["grupos"].items() if conta[g])

    partidos = sorted({v["partido"] for v in d["vereadores"] if v["partido"]})
    ordem = sorted(range(len(d["vereadores"])), key=lambda i: d["vereadores"][i]["nome"])
    crachas = "".join(cracha(i, d["vereadores"][i], d, sal, fotos) for i in ordem)
    sv = d["sessoes"]
    n_ver = len(d["vereadores"])

    corpo = f"""
<p class="aovivo">Dados oficiais · última conferência na Câmara em {e(atualizado)}</p>
<h1 class="titulo">Radar <span>{e(d['cidade'])}</span></h1>
<p class="lead"><b>Raio-X da Câmara de {e(d['cidade'])}-{e(d['uf'])}.</b> O que cada vereador fez desde a posse, contado a partir do sistema oficial da Câmara.</p>
{bloco_sal}
<div class="stats">
<div><strong>{num(len(todas))}</strong><span>propostas até agora</span></div>
<div style="--cor:{CORES_GRUPO['melhoria']}"><strong>{num(conta['melhoria'])}</strong><span>pedidos de melhoria até agora</span></div>
<div style="--cor:{CORES_GRUPO['homenagem']}"><strong>{num(conta['homenagem'])}</strong><span>homenagens até agora</span></div>
<div style="--cor:{CORES_GRUPO['lei']}"><strong>{num(conta['lei'])}</strong><span>propostas de lei até agora</span></div>
</div>

<section id="bairro">
<p class="olho">Comece por aqui</p>
<h2>O que pediram pelo seu bairro?</h2>
<p class="sub">Digite o bairro ou a rua. Sem nada digitado, você vê a cidade inteira.</p>
<label class="caixa-busca">{icone('busca')}<input id="busca" type="search" placeholder="Digite seu bairro ou sua rua" autocomplete="off"></label>
<div class="chips">{atalhos}</div>
<div id="resultado" class="painel"><noscript><p>A busca precisa de JavaScript ligado. A lista completa de propostas está na página de cada vereador.</p></noscript></div>
</section>

<section id="repetidos">
<p class="olho">Só aqui</p>
<h2>O problema que não some</h2>
<p class="sub">Quando o mesmo pedido volta várias vezes para a mesma rua, é sinal de que o problema continua lá. O site da Câmara não mostra isso: nós cruzamos os pedidos um por um.</p>
<div id="lista-rep" class="grade-rep"></div>
<p class="nota">Pedido repetido não prova que a Prefeitura ignorou: pode ser outro trecho da mesma rua. Abra o cartão e leia os pedidos. Rua, bairro e tema são lidos automaticamente do texto oficial e podem falhar em textos confusos.</p>
</section>

<section id="homenagem">
<p class="olho">O trabalho da Câmara</p>
<h2>Homenagem ou trabalho?</h2>
<p class="sub">São {num(len(todas))} propostas até agora, cada uma contada uma vez, separadas pelo tipo e pelas palavras do texto oficial, com a mesma regra para todos.</p>
<div class="barra grossa">{barra_cidade}</div>
<div class="grupos">{cartoes_grupo}</div>
</section>

<section id="vereadores">
<p class="olho">Um por um</p>
<h2>Os {n_ver} vereadores</h2>
<p class="sub">{sum(1 for v in d['vereadores'] if v['titular'])} titulares e {sum(1 for v in d['vereadores'] if not v['titular'])} suplentes que assumiram em algum momento. Das {num(sv['votacoes'])} votações, só {num(sv['votacoes_nominais'])} registram o voto de cada um, e nelas houve {num(sv['votos_nominais'].get('Não', 0))} votos “não” em {num(sum(sv['votos_nominais'].values()))}.</p>
<div class="filtros">
<label>Buscar por nome<input id="nome" type="search" placeholder="Ex.: Socorro, Bruno" autocomplete="off"></label>
<label>Partido<select id="partido"><option value="">Todos</option>{''.join(f'<option>{e(p)}</option>' for p in partidos)}</select></label>
<label>Ordenar por<select id="ordem">
<option value="nome">Nome (A–Z)</option>
<option value="pres">Menor presença</option>
<option value="lei">Mais propostas de lei</option>
<option value="hom">Mais homenagens</option>
<option value="mel">Mais pedidos de melhoria</option>
<option value="tot">Mais propostas no total</option>
<option value="nao">Mais votos “não”</option>
</select></label>
</div>
<p class="nota" id="mostrando">Mostrando os {n_ver} vereadores.</p>
<div class="crachas" id="cards">{crachas}</div>
</section>

<section id="transparencia">
<p class="olho">Transparência</p>
<h2>De onde vêm os números</h2>
<div class="transp">
<div><h3>Tudo oficial</h3><p>Tudo sai do sistema da própria Câmara Municipal (<a href="{e(d['fonte'])}" target="_blank" rel="noopener">{e(d['fonte'].replace('https://', ''))}</a>). Nada é digitado à mão, e a regra é a mesma para todos os vereadores, de todos os partidos.</p></div>
<div><h3>Presença</h3><p>Juntamos as três listas oficiais da Câmara: abertura da sessão, Ordem do Dia e ata. Sessão sem nenhum registro não entra na conta. A Câmara não registra licenças; quando um suplente do mesmo partido assume, o período sai da conta do titular.</p></div>
<div><h3>Pedido não é obra feita</h3><p>Um pedido de melhoria é só um pedido. O sistema da Câmara não informa se a Prefeitura atendeu.</p></div>
{f'<div><h3>Salário</h3><p>O valor vem da <a href="{e(sal["fonte"])}" target="_blank" rel="noopener">{e(sal["documento"])}</a>: {brl(sal["valor"])} por mês para cada vereador; a presidência recebe {brl(sal["mesa"][0][1])} e a 1ª secretaria {brl(sal["mesa"][1][1])}. Valor bruto, sem descontos. O contador do topo é estimativa e usa a tabela de 2026 para todo o período.</p></div>' if sal else ''}
<div><h3>Votos</h3><p>Só entram as votações em que o sistema registra o voto de cada um: {num(sv['votacoes_nominais'])} de {num(sv['votacoes'])}. As outras são simbólicas.</p></div>
<div><h3>Achou um erro?</h3><p>Abra a ficha oficial pelo link do crachá e compare. Se a Câmara corrigir o registro, o número daqui muda na atualização seguinte. <a href="como-funciona/">Veja todas as regras</a>.</p></div>
</div>
</section>
<dialog id="folha" class="folha" aria-labelledby="folha-titulo"><div class="folha-in">
<button type="button" class="fechar" aria-label="Fechar">×</button>
<div id="folha-corpo"></div></div></dialog>
<script>window.CIDADE={json.dumps(d["cidade"])};</script>
<script src="dados.js"></script>
<script src="{R}radar.js"></script>
"""
    (pasta / "index.html").write_text(pagina(f"Radar {d['cidade']}-{d['uf']} — vereadores — Prévias", corpo,
        f"O que cada vereador de {d['cidade']}-{d['uf']} fez desde a posse: pedidos por bairro, presença, propostas e votos, só com dados oficiais.", raiz=R), encoding="utf-8")

    for v in d["vereadores"]:
        gerar_vereador(cid, d, v)
    gerar_como_funciona(cid, d)


def gerar_vereador(cid, d, v):
    pasta = pasta_cidade(cid) / v["slug"]
    pasta.mkdir(parents=True, exist_ok=True)
    pr = v["presenca"]
    grupos = d["grupos"]
    f = foto(cid, v, subir(cid, 1))
    foto_html = f'<img class="foto" src="{e(f)}" alt="Foto de {e(v["nome"])}">' if f else ""
    email = f'<br><small>E-mail do gabinete: <a href="mailto:{e(v["email"])}">{e(v["email"])}</a></small>' if v["email"] else ""
    sup = "Titular" if v["titular"] else "Suplente que assumiu o mandato"

    # presença
    if pr["sessoes_consideradas"]:
        pct = f"{pr['percentual']:.0f}%"
        def li(x):
            motivo = f" — <b>{e(x['motivo'])}</b>" if x.get("motivo") else ""
            return f'<li>{data_br(x["data"])} — {e(x["nome"])}{motivo}<small><a href="{e(x["fonte"])}" target="_blank" rel="noopener">ver sessão no site da Câmara</a></small></li>'
        aus = [x for x in reversed(pr["sessoes"]) if x["situacao"] == "ausente"]
        jus = [x for x in reversed(pr["sessoes"]) if x["situacao"] == "justificada"]
        afast = ""
        if pr["periodos_afastamento"]:
            itens_af = "".join(
                f'<li>{data_br(a["de"])} a {"hoje" if a["ate"].startswith("9999") else data_br(a["ate"])} ({a["sessoes"]} sessões) — {e(a["motivo"])}</li>'
                for a in pr["periodos_afastamento"])
            afast = f"""<div class="aviso"><b>Períodos fora da conta.</b> A Câmara não registra licenças no sistema. Quando um suplente do mesmo partido está em exercício, as sessões em que o titular não aparece não são contadas como falta (e vice-versa quando o titular volta):<ul>{itens_af}</ul></div>"""
        bloco_pres = f"""
<div class="numeros">
<div class="numero"><strong>{pct}</strong><span>de presença*</span></div>
<div class="numero"><strong>{pr['presente']}</strong><span>sessões presente, de {pr['sessoes_consideradas']}</span></div>
<div class="numero"><strong>{pr['justificada']}</strong><span>ausências justificadas</span></div>
<div class="numero"><strong>{pr['ausente']}</strong><span>ausências sem justificativa registrada</span></div>
</div>
<p class="sub" style="font-size:14px">* Conta do Prévias: sessões presente ÷ sessões consideradas. Juntamos as três listas de presença oficiais da Câmara (abertura da sessão, Ordem do Dia e ata). <a href="../como-funciona/">Entenda</a>.</p>
{afast}
<details><summary>Ausências justificadas <small>({len(jus)})</small></summary><ul class="itens">{''.join(li(x) for x in jus) or '<li>Nenhuma.</li>'}</ul></details>
<details><summary>Ausências sem justificativa registrada <small>({len(aus)})</small></summary><ul class="itens">{''.join(li(x) for x in aus) or '<li>Nenhuma.</li>'}</ul></details>
"""
    else:
        bloco_pres = '<p>A Câmara não registrou presença em sessões durante o período deste mandato.</p>'

    # propostas
    blocos = []
    for g, nome_g in grupos.items():
        itens = [p for p in v["propostas"] if p["grupo"] == g]
        lis = "".join(
            f'<li><span class="tag">{e(p["tipo"])} nº {p["numero"]}/{p["ano"]}</span>{data_br(p["data"])}'
            f'{" · com mais " + str(p["coautores"]) + " autor(es)" if p["coautores"] else ""}<br>{e(ementa_legivel(p["ementa"]))}'
            f'<small><a href="{e(p["fonte"])}" target="_blank" rel="noopener">ver no site da Câmara</a></small></li>'
            for p in itens)
        blocos.append(f'<details><summary>{e(nome_g)} <small>({num(len(itens))})</small></summary><ul class="itens">{lis or "<li>Nenhuma.</li>"}</ul></details>')
    resumo = "".join(f'<div class="numero"><strong>{num(v["resumo_propostas"][g])}</strong><span>{e(n)}</span></div>' for g, n in grupos.items())

    # votos
    sv = d["sessoes"]
    contexto = (f'De {num(sv["votacoes"])} votações nesta legislatura, só {num(sv["votacoes_nominais"])} registram o voto de cada vereador — as demais são simbólicas. '
                f'Nessas {num(sv["votacoes_nominais"])}, a Câmara registrou {num(sv["votos_nominais"].get("Sim", 0))} votos "sim" e {num(sv["votos_nominais"].get("Não", 0))} "não": quase tudo é aprovado por unanimidade.')
    if v["votos"]:
        linhas = "".join(
            f'<li>{data_br(x["data"])} — <span class="{"v-sim" if x["voto"] == "Sim" else "v-nao" if x["voto"] == "Não" else ""}">{e(x["voto"])}</span> · {e(x["materia"])}'
            f'<br>{e(ementa_legivel(x["ementa"]))}<small>Placar: {x["placar"]["sim"]} sim, {x["placar"]["nao"]} não, {x["placar"]["abstencao"]} abstenções · '
            f'<a href="{e(x["fonte"])}" target="_blank" rel="noopener">ver matéria</a> · <a href="{e(x["fonte_sessao"])}" target="_blank" rel="noopener">ver sessão</a></small></li>' for x in v["votos"])
        rv = ", ".join(f'{n} "{k.lower()}"' for k, n in sorted(v["resumo_votos"].items(), key=lambda kv: -kv[1]))
        bloco_votos = f'<p class="sub">{e(contexto)}</p><p>{e(v["nome"])} tem {num(len(v["votos"]))} votos registrados um a um ({e(rv)}).</p><details><summary>Ver todos os votos <small>({num(len(v["votos"]))})</small></summary><ul class="itens">{linhas}</ul></details>'
    else:
        bloco_votos = f'<p class="sub">{e(contexto)}</p><p>Não há votos de {e(v["nome"])} registrados um a um nesta legislatura.</p>'

    corpo = f"""
<div class="perfil">{foto_html}<div><h1>{e(v['nome'])}</h1><p class="sub">{e(v['partido'] or 'Partido não informado')} · {sup}{email}</p></div></div>
<p class="sub"><a href="{e(v['fonte'])}" target="_blank" rel="noopener">Ficha oficial no site da {e(d['camara'])}</a></p>
<h2>Presença nas sessões</h2>
{bloco_pres}
<h2 id="propostas">Propostas apresentadas</h2>
<p class="sub">{num(len(v['propostas']))} documentos desde {data_br(d['legislatura']['inicio'])}, separados em grupos. <a href="../como-funciona/">Veja a regra</a>.</p>
<div class="numeros">{resumo}</div>
{''.join(blocos)}
<h2>Como votou</h2>
{bloco_votos}
"""
    (pasta / "index.html").write_text(pagina(f"{v['nome']} — vereador(a) de {d['cidade']}-{d['uf']} — Radar Prévias", corpo,
        f"Presença, propostas e votos de {v['nome']}, vereador(a) de {d['cidade']}-{d['uf']}.", raiz=subir(cid, 1),
        voltar=("../", f"Todos os vereadores de {d['cidade']}")), encoding="utf-8")


def gerar_como_funciona(cid, d):
    pasta = pasta_cidade(cid) / "como-funciona"
    pasta.mkdir(parents=True, exist_ok=True)
    regras = "".join(f"<tr><th>{e(g)}</th><td>{e(r)}</td></tr>" for g, r in d["regras_classificacao"])
    sem = d["sessoes"]["sem_registro_presenca"]
    lista_sem = "".join(f'<li>{data_br(s["data"])} — {e(s["nome"])} <small><a href="{e(s["fonte"])}" target="_blank" rel="noopener">ver sessão</a></small></li>' for s in sem)
    corpo = f"""
<h1>Como os números são calculados</h1>
<p>Todos os dados vêm do sistema oficial da {e(d['camara'])} (<a href="{e(d['fonte'])}" target="_blank" rel="noopener">{e(d['fonte'].replace('https://', ''))}</a>), baixados automaticamente. Usamos a mesma regra para todos os vereadores, de todos os partidos.</p>
<h2>Presença</h2>
<p>A Câmara publica a presença em três lugares: a lista de abertura da sessão, a lista da Ordem do Dia e a lista que sai na ata da sessão (PDF). Elas nem sempre batem — em algumas sessões a ata tem nomes que não estão nas outras listas. <b>Juntamos as três</b>: se o vereador aparece em qualquer uma, conta como presente. Conferência: todos os {num(d['sessoes']['votacoes_nominais'])} registros de votação nominal são de vereadores que constam como presentes.</p>
<p>Só contam as sessões em que a Câmara registrou a presença de pelo menos um vereador ({d['sessoes']['com_registro_presenca']} sessões) e que aconteceram durante o mandato. <b>Dado ausente não é falta:</b> sessão sem nenhum registro não entra na conta.</p>
<p><b>Ausência justificada</b> é a que a Câmara registrou com motivo (saúde, viagem, missão oficial etc.), no sistema ou na ata. Ela aparece separada, mas a porcentagem de presença considera só as sessões em que o vereador esteve presente.</p>
<p><b>Licenças:</b> a Câmara não registra licenças no sistema. Como o suplente é sempre do mesmo partido do titular que substitui, quando um suplente está em exercício e o titular do mesmo partido não aparece em nenhuma sessão do período, tratamos esse período como provável afastamento e ele sai da conta — e o mesmo vale para o suplente depois que o titular volta. Isso é uma dedução do Prévias e está escrito na página de cada vereador afetado.</p>
<details><summary>Sessões sem nenhum registro de presença <small>({len(sem)})</small></summary><ul class="itens">{lista_sem or '<li>Nenhuma.</li>'}</ul></details>
<h2>Grupos de propostas</h2>
<p>Cada documento cai em um grupo pelo seu tipo e por palavras do resumo (ementa). A regra é automática e pode errar em casos de texto ambíguo — por isso cada item tem o link para o documento original.</p>
<p><b>Texto dos documentos.</b> Muitos resumos oficiais vêm todos em letras maiúsculas. Para facilitar a leitura, o site mostra o texto com maiúsculas e minúsculas, sem mudar nenhuma palavra. A grafia original está no link de cada documento.</p>
<table>{regras}</table>
<p>Ficam de fora atas, pareceres de comissão e atos da Mesa, que não são propostas de um vereador. Documentos com mais de um autor contam para todos os autores.</p>
<h2>Votos</h2>
<p>Mostramos só as votações em que o sistema registrou o voto de cada vereador (votação nominal): {num(d['sessoes']['votacoes_nominais'])} de {num(d['sessoes']['votacoes'])} votações nesta legislatura. As demais são simbólicas e não têm esse registro. A data é a da sessão em que a votação aconteceu.</p>
"""
    (pasta / "index.html").write_text(pagina(f"Como funciona — Radar {d['cidade']}", corpo, raiz=subir(cid, 1),
        voltar=("../", f"Vereadores de {d['cidade']}")), encoding="utf-8")


def gerar_inicio(cidades):
    cards = "".join(f'<a class="card" href="{CAMINHO.get(c, c)}/"><span><b>{e(d["cidade"])}-{e(d["uf"])}</b><small>{len(d["vereadores"])} vereadores · dados até {data_hora_br(d["coletado_em"])}</small></span></a>' for c, d in cidades.items())
    corpo = f"""
<h1>Radar dos vereadores do Amapá</h1>
<p class="sub">O que cada vereador faz, só com dados oficiais das Câmaras: presença, propostas e votos. Sem nota e sem opinião.</p>
<div class="cards">{cards}</div>
<div class="aviso">Começamos pelas Câmaras que publicam os dados num sistema aberto. Outras cidades do Amapá entram assim que for possível coletar os dados oficiais.</div>
"""
    (BASE / "index.html").write_text(pagina("Radar Prévias — vereadores do Amapá", corpo, raiz=""), encoding="utf-8")


def main(lista):
    if PUBLICO.exists():
        shutil.rmtree(PUBLICO)          # sempre do zero: nada velho fica para trás
    BASE.mkdir(parents=True)
    (BASE / "estilo.css").write_text(ESTILO.strip() + "\n", encoding="utf-8")
    shutil.copy(RAIZ / "site" / "radar.js", BASE / "radar.js")
    if (RAIZ / "site" / "fotos").exists():
        shutil.copytree(RAIZ / "site" / "fotos", BASE / "fotos", ignore=shutil.ignore_patterns("originais"))
    # raiz do GitHub Pages: leva para o endereço oficial
    (PUBLICO / "index.html").write_text(
        f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={SITE_URL}">'
        f'<link rel="canonical" href="{SITE_URL}"><title>Radar Prévias</title><a href="{SITE_URL}">Radar Prévias</a>\n', encoding="utf-8")
    (PUBLICO / ".nojekyll").write_text("", encoding="utf-8")
    for arq in ("favicon.png", "logo-previas.png"):
        if (RAIZ / "site" / arq).exists():
            shutil.copy(RAIZ / "site" / arq, BASE / arq)
    cidades = {}
    for cid in lista:
        d = json.loads((RAIZ / "dados" / "site" / f"{cid}.json").read_text(encoding="utf-8"))
        gerar_cidade(cid, d)
        cidades[cid] = d
    gerar_inicio(cidades)
    print("site gerado em", PUBLICO)


if __name__ == "__main__":
    main(sys.argv[1:] or ["santana"])
