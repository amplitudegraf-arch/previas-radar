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
CAMINHO = {"santana": "santana/radar", "porto-grande": "porto-grande/radar"}
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


DESCRICAO_PADRAO = "O que cada vereador faz, só com dados oficiais das Câmaras: presença, propostas e votos. Sem nota e sem opinião."


NOMES_CIDADES = {}   # cid -> nome, preenchido em main(); usado no "Outras cidades"


def trilha(raiz, cid=None, nivel=0, atual=None):
    """Amapá › Cidade › Página, e atalho para as outras cidades com Radar.
    nivel: 0 = página da cidade, 1 = subpágina (vereador, como funciona)."""
    partes = [f'<a href="{raiz}">Amapá</a>']
    if cid:
        nome = NOMES_CIDADES.get(cid, cid)
        partes.append(f'<a href="{"../" if nivel else "./"}">{e(nome)}</a>' if atual else f'<span aria-current="page">{e(nome)}</span>')
    if atual:
        partes.append(f'<span aria-current="page">{e(atual)}</span>')
    outras = "".join(f'<a href="{raiz}{CAMINHO.get(c, c)}/">{e(n)}</a>' for c, n in NOMES_CIDADES.items() if c != cid)
    outras = f'<span class="outras">Outra cidade: {outras}</span>' if cid and outras else ""
    return f'<nav class="trilha" aria-label="Você está em">{" <i>›</i> ".join(partes)}{outras}</nav>'


def pagina(titulo, corpo, descricao="", raiz="../", voltar=None, onde=None, imagem="og/ap.png"):
    return _links_locais(_pagina(titulo, corpo, descricao, raiz, voltar, onde, imagem))


def _pagina(titulo, corpo, descricao="", raiz="../", voltar=None, onde=None, imagem="og/ap.png"):
    if isinstance(voltar, str):
        volta = voltar                     # trilha pronta
    else:
        volta = f'<a class="voltar" href="{e(voltar[0])}">← {e(voltar[1])}</a>' if voltar else ""
    descricao = descricao or DESCRICAO_PADRAO
    rel = "" if onde is None else onde.relative_to(BASE).as_posix()
    url = SITE_URL + (rel + "/" if rel and rel != "." else "")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Prévias — Radar">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{SITE_URL}{imagem}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
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
<p><a href="{raiz}#como">Como coletamos os dados</a> · <a href="https://www.previas26.com.br/">Prévias — transparência política para todos</a></p>
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
.perfil>div{min-width:0}
main a,main small,main p{overflow-wrap:anywhere}
.perfil .foto{width:88px;height:88px}
.numeros{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(150px,100%),1fr));gap:10px;margin:12px 0}
@media (max-width:420px){.numeros{grid-template-columns:repeat(2,minmax(0,1fr))}}
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
.rank .trilho .pilha{display:flex;background:none;border-radius:3px;overflow:hidden}
.rank .trilho .pilha i{display:block;height:100%}
.legenda-q{display:flex;flex-wrap:wrap;gap:4px 14px;margin:-2px 0 8px;font-size:12px;color:var(--sub)}
.legenda-q span{display:inline-flex;align-items:center;gap:6px}
.legenda-q i{width:10px;height:10px;border-radius:2px;display:inline-block}
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
.rodape{max-width:1040px;box-sizing:border-box}
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
.rank .trilho .pilha{background:none}
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
.vazio-rep{background:var(--card,#fff);border:1px dashed #d8cfbf;border-radius:14px;padding:18px;color:var(--sub)}
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
.crachas{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:18px;margin-top:10px}
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
.obs-voto{font-size:12px;color:var(--sub);margin:-6px 0 12px}
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

/* início do Radar AP */
.busca-ver{margin:20px 0 8px}
.busca-ver label{display:block;font-weight:700;margin-bottom:6px}
.busca-ver input{width:100%;box-sizing:border-box;font:inherit;padding:14px 16px;border:1.5px solid #1E2C42;border-radius:12px;background:#fff}
.r-ver{list-style:none;margin:6px 0 0;padding:0}
.r-ver a{display:flex;gap:12px;align-items:center;padding:8px 10px;border-radius:10px;text-decoration:none;color:inherit}
.r-ver a:hover,.r-ver a:focus{background:#F5EFE3}
.r-ver img{width:40px;height:40px;border-radius:50%;object-fit:cover}
.r-ver b{display:block}.r-ver small{color:var(--sub)}
.r-ver .nada{padding:8px 10px;color:var(--sub)}
.cidades{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:14px;margin:12px 0 8px}
.cidade{display:flex;flex-direction:column;gap:12px;padding:18px;border-radius:16px;background:#283C59;color:#F5EFE3;text-decoration:none}
.cidade:hover,.cidade:focus{background:#1E2C42}
.cid-nome{font:900 28px/1 Archivo,sans-serif;text-transform:uppercase;color:#fff}
.cid-nome small{font-size:16px;color:#B8860B;text-transform:none}
.cid-num{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.cid-num span{font-size:12px;line-height:1.3;opacity:.85}
.cid-num b{display:block;font:800 22px/1.1 Archivo,sans-serif;color:#fff;opacity:1}
.cid-data{font-size:12px;opacity:.7}
.cid-ir{font-weight:700;color:#E8C46A}
.faltam{list-style:none;padding:0;margin:8px 0;display:flex;flex-wrap:wrap;gap:8px}
.faltam li{padding:6px 12px;border-radius:999px;background:#EFEBE3;color:#6B6458;font-size:14px}

.pres2 p{margin:0 0 6px;font-size:15px}.pres2 p b{font:800 26px/1 Archivo,sans-serif}
.barra-pres{height:8px;border-radius:999px;background:#ECE6DA;overflow:hidden;margin-bottom:6px}
.barra-pres span{display:block;height:100%;background:#283C59;border-radius:999px}
.pres2 small{display:block;color:var(--sub);font-size:13px}
.selo-poucas{display:inline-block;margin-left:6px;padding:2px 8px;border-radius:999px;background:#FBF1D6;color:#8A6400;font-size:12px;font-weight:700;vertical-align:middle}
.total-prop{margin:14px 0 4px;font-size:15px}.total-prop b{font:800 22px Archivo,sans-serif}
.total-prop .destaque:not(:empty){display:block;color:var(--sub);font-size:13px}

.trilha{display:flex;flex-wrap:wrap;align-items:center;gap:6px;font-size:14px;margin:4px 0 10px;color:var(--sub)}
.trilha a{color:var(--ink,#1E2C42);font-weight:600}
.trilha i{font-style:normal;opacity:.6}
.trilha [aria-current]{color:var(--sub)}
.trilha .outras{margin-left:auto;display:flex;gap:8px;align-items:center}
.trilha .outras a{padding:3px 10px;border:1px solid #d8cfbf;border-radius:999px;text-decoration:none;font-size:13px}
@media (max-width:520px){.trilha .outras{margin-left:0;width:100%}}
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
        "mesa": [["Presidência", 18064], ["1ª Secretaria", 13548]],
        "documento": "Tabela Padrão Remuneratório Vereadores — vigente para o exercício de 2026",
        "fonte": "https://www.santana.ap.leg.br/transparencia-old/gestao-de-pessoas/folha-de-pagamento-servidores/padrao-remuneratorio/tabela-remuneratoria-vereadores",
        "rotulo": "tabela oficial da Câmara",
        "nota": "O contador do topo é estimativa e usa a tabela de 2026 para todo o período.",
    },
    "porto-grande": {
        "cadeiras": 11,
        "valor": 5500,
        "mesa": [],
        "documento": "Lei Municipal nº 584/2024, que fixa o subsídio dos vereadores para 2025–2028",
        "fonte": "https://sapl.portogrande.ap.leg.br/media/sapl/public/normajuridica/2024/492/lei_584_2024_-_fixa_o_subsidio_do_prefeito_vice-prefeito_vereadores....pdf",
        "rotulo": "lei que fixa o salário",
        "nota": ("A lei não prevê valor maior para a presidência. A partir de 2026 o valor é corrigido todo ano "
                 "pela inflação (INPC), e a Câmara não publica o valor corrigido; por isso o contador usa "
                 "R$ 5.500 e fica um pouco abaixo do valor real."),
    },
}


def salario_mensal(sal):
    """Soma do mês: vereadores comuns + cargos da Mesa com acréscimo."""
    return (sal["cadeiras"] - len(sal["mesa"])) * sal["valor"] + sum(v for _, v in sal["mesa"])


def texto_cadeiras(d, sal):
    tit = sum(1 for v in d["vereadores"] if v["titular"])
    sup = len(d["vereadores"]) - tit
    cad = sal["cadeiras"] if sal else tit
    if not sup:
        return f"São {cad} cadeiras, todas ocupadas pelos titulares desde a posse."
    return (f"São {cad} cadeiras, e {len(d['vereadores'])} pessoas já ocuparam alguma: {tit} titulares e "
            f"{sup} {'suplente que assumiu' if sup == 1 else 'suplentes que assumiram'} em algum momento.")


def texto_votos(sv):
    simb = sv["votacoes"] - sv["votacoes_nominais"]
    vn = sv["votos_nominais"]
    return (f"Em {num(simb)} das {num(sv['votacoes'])} votações, a votação foi simbólica, sem voto individual registrado. "
            f"Nas {num(sv['votacoes_nominais'])} restantes, só {num(vn.get('Não', 0))} votos foram “não”{abst_txt(vn)}.")


def abst_txt(vn):
    a = vn.get("Abstenção", 0)
    nv = sum(n for k, n in vn.items() if k not in ("Sim", "Não", "Abstenção"))
    partes = ([f'{num(a)} abstenções'] if a else []) + ([f'{num(nv)} sem voto (inclui a presidência, que só vota para desempatar)'] if nv else [])
    return (", além de " + " e ".join(partes)) if partes else ""


def mesa_txt(sal):
    if len(sal["mesa"]) < 2:
        return ""
    return f"; a presidência recebe {brl(sal['mesa'][0][1])} e a 1ª secretaria {brl(sal['mesa'][1][1])}"


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


def nome_cargo(cargo, sexo=""):
    """Grafia única para os cargos da Mesa (o SAPL escreve de vários jeitos)."""
    t = re.sub(r"\s+", " ", (cargo or "").upper().replace("-", " ")).strip()
    f = (sexo or "").upper().startswith("F")
    o = "ª" if f else "º"
    n = "1" if re.search(r"\b(PRIMEIR[OA]|1)", t) else "2" if re.search(r"\b(SEGUND[OA]|2)", t) else "3" if re.search(r"\b(TERCEIR[OA]|3)", t) else ""
    if "VICE" in t:
        return f"{n}{o} Vice-presidente" if n else "Vice-presidente"
    if "SECRET" in t:
        base = "Secretária" if f else "Secretário"
        return f"{n}{o} {base}" if n else base
    if "PRESIDENTE" in t:
        return "Presidente"
    return (cargo or "").strip()


def preparar_mesa(cid, d):
    """Marca o cargo de cada vereador na Mesa do ano mais recente da Câmara.
    Cargo de anos anteriores não é cargo atual (ex.: 2º vice em 2025 que não continuou em 2026)."""
    sexo = {}
    arq = RAIZ / "dados" / "bruto" / cid / "parlamentares.json"
    if arq.exists():
        sexo = {p["id"]: p.get("sexo") or "" for p in json.loads(arq.read_text(encoding="utf-8"))}
    anos = [m["ano"] for v in d["vereadores"] for m in v.get("mesa") or []]
    ult = max(anos) if anos else None
    for v in d["vereadores"]:
        sx = sexo.get(v["id"], "")
        hist = {}
        for m in v.get("mesa") or []:
            hist.setdefault(m["ano"], nome_cargo(m["cargo"], sx))
        v["mesa_hist"] = sorted(hist.items())
        v["cargo_atual"] = hist.get(ult)
    d["ano_mesa"] = ult


def cargo_atual(v):
    return v.get("cargo_atual")


def salario_de(v, sal):
    if not sal:
        return None
    c = cargo_atual(v) or ""
    if c == "Presidente" and sal["mesa"]:
        return sal["mesa"][0][1]
    if len(sal["mesa"]) > 1 and c in ("1º Secretário", "1ª Secretária"):
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


POUCAS_SESSOES = 30   # abaixo disso o percentual de presença ganha o selo "poucas sessões"


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
        p_ = pr["percentual"]
        selo = (f'<span class="selo-poucas" title="Percentual calculado sobre poucas sessões">poucas sessões</span>'
                if pr["sessoes_consideradas"] < POUCAS_SESSOES else "")
        presenca = (f'<div class="pres2"><p><b>{p_:.0f}%</b> de presença {selo}</p>'
                    f'<div class="barra-pres"><span style="width:{p_:.1f}%"></span></div>'
                    f'<small>{pr["presente"]} de {pr["sessoes_consideradas"]} sessões · {pr["justificada"]} '
                    f'{"falta justificada" if pr["justificada"] == 1 else "faltas justificadas"} · '
                    f'<span class="{"falta" if pr["ausente"] else ""}">{pr["ausente"]} sem justificativa</span></small>'
                    + (f'<small>{sum(a["sessoes"] for a in pr["periodos_afastamento"])} sessões fora da conta (afastamento)</small>' if pr["periodos_afastamento"] else "")
                    + '</div>')
    else:
        presenca = '<div class="pres2"><p>Sem presença registrada no período</p></div>'
    fundo = FUNDOS_CRACHA[i % len(FUNDOS_CRACHA)]
    pct = pr["percentual"] if pr["percentual"] is not None else 999
    poucas = 1 if pr["sessoes_consideradas"] < POUCAS_SESSOES else 0
    nao = (v.get("resumo_votos") or {}).get("Não", 0)
    return f"""<article class="cracha" data-nome="{e(v['nome'])}" data-partido="{e(v['partido'] or '')}" data-pres="{pct}" data-poucas="{poucas}" data-lei="{rp['lei']}" data-hom="{rp['homenagem']}" data-mel="{rp['melhoria']}" data-tot="{tot}">
<header style="background:{fundo}"><span class="furo"></span>
<div class="quem">{foto_html}<div><h3><a href="{e(v['slug'])}/">{e(v['nome'])}</a></h3>{nome_comp}</div></div>
<div class="pills">{pills}</div></header>
<div class="corpo">
{presenca}
<div class="total-prop"><b>{num(tot)}</b> propostas até agora<span class="destaque" data-lei="{num(rp['lei'])} propostas de lei" data-hom="{num(rp['homenagem'])} homenagens" data-mel="{num(rp['melhoria'])} pedidos de melhoria"></span></div>
<p class="links"><a href="{e(v['slug'])}/">Ver página →</a><a href="{e(v['fonte'])}" target="_blank" rel="noopener">Ficha na Câmara ↗</a></p>
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
    dados_js = {"pedidos": pedidos, "rep": rep, "ver": ver_js,
                "grupos": [{"g": k, "n": d["grupos"][k], "c": CORES_GRUPO[k]} for k in ("melhoria", "cobranca")]}
    bloco_sal = ""
    if sal:
        mensal = salario_mensal(sal)
        dados_js["sal"] = {"mensal": mensal, "posse": leg["inicio"]}
        mesa = "".join(f"; {n.lower()} {brl(v)}" for n, v in sal["mesa"])
        bloco_sal = f"""<div class="salario">
<p>Salário pago às {sal['cadeiras']} cadeiras da Câmara desde a posse</p>
<strong id="contador">{brl(0)}</strong>
<small>e subindo agora · estimativa: {sal['cadeiras']} salários por mês ({brl(sal['valor'])} cada{mesa}) desde {data_br(leg['inicio'])}. Valor bruto da <a href="{e(sal['fonte'])}" target="_blank" rel="noopener">{e(sal['rotulo'])}</a>, sem 13º nem verba indenizatória.</small>
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
{'<div id="lista-rep" class="grade-rep"></div>' if rep else '<p class="vazio-rep">Até agora, nenhuma rua recebeu o mesmo tipo de pedido 3 vezes ou mais. Quando isso acontecer, o caso aparece aqui.</p>'}
<p class="nota">Pedido repetido não prova que a Prefeitura ignorou: pode ser outro trecho da mesma rua. Abra o cartão e leia os pedidos. Rua, bairro e tema são lidos automaticamente do texto oficial e podem falhar em textos confusos.</p>
</section>

<section id="homenagem">
<p class="olho">O trabalho da Câmara</p>
<h2>Que tipo de proposta?</h2>
<p class="sub">São {num(len(todas))} propostas até agora, cada uma contada uma vez, separadas pelo tipo e pelas palavras do texto oficial, com a mesma regra para todos.</p>
<div class="barra grossa">{barra_cidade}</div>
<div class="grupos">{cartoes_grupo}</div>
</section>

<section id="vereadores">
<p class="olho">Um por um</p>
<h2>Os {n_ver} vereadores</h2>
<p class="sub">{texto_cadeiras(d, sal)} {texto_votos(sv)}</p>
<div class="filtros">
<label>Buscar por nome<input id="nome" type="search" placeholder="Ex.: Socorro, Bruno" autocomplete="off"></label>
<label>Partido<select id="partido"><option value="">Todos</option>{''.join(f'<option>{e(p)}</option>' for p in partidos)}</select></label>
<label>Ordenar por<select id="ordem">
<option value="nome">Nome (A–Z)</option>
<option value="pres_mais">Maior presença</option>
<option value="pres">Menor presença</option>
<option value="lei">Mais propostas de lei</option>
<option value="hom">Mais homenagens</option>
<option value="mel">Mais pedidos de melhoria</option>
<option value="tot">Mais propostas no total</option>
</select></label>
</div>
<p class="nota" id="mostrando">Mostrando os {n_ver} vereadores.</p>
<p class="nota" id="aviso-poucas" hidden>Quem tem menos de {POUCAS_SESSOES} sessões na conta (em geral suplentes) vai para o fim: o percentual sobre poucas sessões não dá para comparar.</p>
<div class="crachas" id="cards">{crachas}</div>
</section>

<section id="transparencia">
<p class="olho">Transparência</p>
<h2>De onde vêm os números</h2>
<div class="transp">
<div><h3>Tudo oficial</h3><p>Tudo sai do sistema da própria Câmara Municipal (<a href="{e(d['fonte'])}" target="_blank" rel="noopener">{e(d['fonte'].replace('https://', ''))}</a>). Nada é digitado à mão, e a regra é a mesma para todos os vereadores, de todos os partidos.</p></div>
<div><h3>Presença</h3><p>Juntamos as listas oficiais da Câmara (abertura da sessão, Ordem do Dia e ata) e a lista de oradores da ata: quem discursou estava lá. Sessão sem nenhum registro não entra na conta. A Câmara não registra licenças; quando um suplente do mesmo partido assume, o período sai da conta do titular.</p></div>
<div><h3>Pedido não é obra feita</h3><p>Um pedido de melhoria é só um pedido. O sistema da Câmara não informa se a Prefeitura atendeu.</p></div>
{f'<div><h3>Salário</h3><p>O valor vem da <a href="{e(sal["fonte"])}" target="_blank" rel="noopener">{e(sal["documento"])}</a>: {brl(sal["valor"])} por mês para cada vereador{mesa_txt(sal)}. Valor bruto, sem descontos. {e(sal["nota"])}</p></div>' if sal else ''}
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
        f"O que cada vereador de {d['cidade']}-{d['uf']} fez desde a posse: pedidos por bairro, presença, propostas e votos, só com dados oficiais.", raiz=R,
        voltar=trilha(R, cid), onde=pasta, imagem=f"og/{cid}.png"), encoding="utf-8")

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
    if cargo_atual(v):
        sup += f" · {cargo_atual(v)} da Câmara"
    passados = [(a, c) for a, c in v.get("mesa_hist", []) if a != d.get("ano_mesa")]
    mesa_html = (f'<p class="sub">Mesa Diretora em anos anteriores: ' + "; ".join(f"{e(c)} em {a}" for a, c in passados) + ".</p>") if passados else ""
    sal = SALARIOS.get(cid)
    sv_ = salario_de(v, sal)
    sal_html = (f'<p class="sub">Salário: <b>{brl(sv_)} por mês</b>, valor bruto da <a href="{e(sal["fonte"])}" target="_blank" rel="noopener">{e(sal["rotulo"])}</a>.</p>'
                if sv_ else "")

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
<p class="sub" style="font-size:14px">* Conta do Prévias: sessões presente ÷ sessões consideradas. Juntamos as listas de presença oficiais da Câmara (abertura da sessão, Ordem do Dia e ata) e os oradores registrados na ata. <a href="../como-funciona/">Entenda</a>.</p>
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
    contexto = texto_votos(sv)
    if v["votos"]:
        linhas = "".join(
            f'<li>{data_br(x["data"])} — <span class="{"v-sim" if x["voto"] == "Sim" else "v-nao" if x["voto"] == "Não" else ""}">{e(x["voto"])}</span> · {e(x["materia"])}'
            f'<br>{e(ementa_legivel(x["ementa"]))}<small>Placar: {x["placar"]["sim"]} sim, {x["placar"]["nao"]} não, {x["placar"]["abstencao"]} abstenções · '
            f'<a href="{e(x["fonte"])}" target="_blank" rel="noopener">ver matéria</a> · <a href="{e(x["fonte_sessao"])}" target="_blank" rel="noopener">ver sessão</a></small></li>' for x in v["votos"])
        rv = ", ".join(f'{n} "{k.lower()}"' for k, n in sorted(v["resumo_votos"].items(), key=lambda kv: -kv[1]))
        obs_pres = (" Na presidência, só se vota para desempatar; por isso tantos registros sem voto."
                    if cargo_atual(v) == "Presidente" and (v.get("resumo_votos") or {}).get("Não Votou") else "")
        bloco_votos = f'<p class="sub">{e(contexto)}</p><p>{e(v["nome"])} tem {num(len(v["votos"]))} votos registrados um a um ({e(rv)}).{obs_pres}</p><details><summary>Ver todos os votos <small>({num(len(v["votos"]))})</small></summary><ul class="itens">{linhas}</ul></details>'
    else:
        bloco_votos = f'<p class="sub">{e(contexto)}</p><p>Não há votos de {e(v["nome"])} registrados um a um nesta legislatura.</p>'

    corpo = f"""
<div class="perfil">{foto_html}<div><h1>{e(v['nome'])}</h1><p class="sub">{e(v['partido'] or 'Partido não informado')} · {sup}{email}</p></div></div>
<p class="sub"><a href="{e(v['fonte'])}" target="_blank" rel="noopener">Ficha oficial no site da {e(d['camara'])}</a></p>
{sal_html}
{mesa_html}
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
        voltar=trilha(subir(cid, 1), cid, 1, v["nome"]), onde=pasta, imagem=f"og/{cid}.png"), encoding="utf-8")


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
<p>A Câmara publica a presença em três lugares: a lista de abertura da sessão, a lista da Ordem do Dia e a lista que sai na ata da sessão (PDF). Elas nem sempre batem — em algumas sessões a ata tem nomes que não estão nas outras listas. <b>Juntamos as três</b>: se o vereador aparece em qualquer uma, conta como presente. Também conta como presente quem a ata registra como orador da sessão — houve casos de vereador que discursou mas não estava na lista de presença ({num(d["sessoes"].get("presencas_so_por_oradores", 0))} nesta legislatura). Conferência: todos os {num(d['sessoes']['votacoes_nominais'])} registros de votação nominal são de vereadores que constam como presentes.</p>
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
        voltar=trilha(subir(cid, 1), cid, 1, "Como funciona"), onde=pasta, imagem=f"og/{cid}.png",
        descricao=f"Como o Radar Prévias conta presença, propostas e votos dos vereadores de {d['cidade']}-{d['uf']}."), encoding="utf-8")


# Os 16 municípios do Amapá. Os que não estão em CAMINHO aparecem como "ainda sem dados abertos".
MUNICIPIOS_AP = ["Macapá", "Santana", "Laranjal do Jari", "Oiapoque", "Mazagão", "Porto Grande", "Tartarugalzinho",
                 "Vitória do Jari", "Pedra Branca do Amapari", "Calçoene", "Amapá", "Ferreira Gomes", "Cutias",
                 "Itaubal", "Serra do Navio", "Pracuúba"]


def presenca_media(d):
    pres = sum(v["presenca"]["presente"] for v in d["vereadores"])
    cons = sum(v["presenca"]["sessoes_consideradas"] for v in d["vereadores"])
    return round(100 * pres / cons) if cons else None


def gerar_inicio(cidades):
    cards, busca = [], []
    for c, d in cidades.items():
        cam = CAMINHO.get(c, c)
        props = len({p["id"] for v in d["vereadores"] for p in v["propostas"]})
        pm = presenca_media(d)
        cards.append(
            f'<a class="cidade" href="{cam}/" aria-label="Ver o Radar de {e(d["cidade"])}">'
            f'<span class="cid-nome">{e(d["cidade"])}<small>-{e(d["uf"])}</small></span>'
            f'<span class="cid-num"><span><b>{len(d["vereadores"])}</b>vereadores</span>'
            f'<span><b>{pm}%</b>presença média</span><span><b>{num(props)}</b>propostas</span></span>'
            f'<span class="cid-data">Dados oficiais até {data_hora_br(d["coletado_em"])}</span>'
            f'<span class="cid-ir">Ver vereadores →</span></a>')
        for v in d["vereadores"]:
            busca.append({"n": v["nome"], "c": v.get("nome_completo") or "", "p": v["partido"] or "",
                          "m": d["cidade"], "u": f'{cam}/{v["slug"]}/', "f": foto(c, v, "")})
    tem = {d["cidade"] for d in cidades.values()}
    faltam = "".join(f'<li>{e(m)}</li>' for m in MUNICIPIOS_AP if m not in tem)
    como = "".join(f'<li><a href="{CAMINHO.get(c, c)}/como-funciona/">Como contamos em {e(d["cidade"])}</a> · '
                   f'<a href="{e(d["fonte"])}" target="_blank" rel="noopener">sistema oficial da Câmara ↗</a></li>'
                   for c, d in cidades.items())
    total = sum(len(d["vereadores"]) for d in cidades.values())
    corpo = f"""
<h1>Radar dos vereadores do Amapá</h1>
<p class="sub">O que cada vereador faz, só com dados oficiais das Câmaras: presença, propostas e votos. Sem nota e sem opinião.</p>

<div class="busca-ver">
<label for="q-ver">Encontre seu vereador</label>
<input id="q-ver" type="search" placeholder="Digite o nome, apelido ou partido" autocomplete="off">
<ul id="r-ver" class="r-ver" aria-live="polite"></ul>
</div>

<h2>Cidades com Radar</h2>
<div class="cidades">{"".join(cards)}</div>

<h2>As outras {len(MUNICIPIOS_AP) - len(tem)} cidades do Amapá</h2>
<p class="sub">Entram no Radar quando a Câmara publicar presença, propostas e votos num sistema aberto, que dê para conferir todo dia.</p>
<ul class="faltam">{faltam}</ul>

<h2 id="como">Como coletamos os dados</h2>
<p>Todo dia um robô lê o sistema oficial de cada Câmara, confere os números (presença contra votos, propostas sem repetição) e só publica se tudo bater. Cada número no site tem link para o documento original.</p>
<ul class="itens">{como}</ul>
<script>
(function () {{
  var V = {json.dumps(busca, ensure_ascii=False, separators=(",", ":"))};
  var q = document.getElementById("q-ver"), r = document.getElementById("r-ver");
  function norm(t) {{ return (t || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); }}
  q.addEventListener("input", function () {{
    var t = norm(q.value.trim()); r.innerHTML = "";
    if (t.length < 2) return;
    var achou = V.filter(function (v) {{ return norm(v.n + " " + v.c + " " + v.p + " " + v.m).indexOf(t) >= 0; }}).slice(0, 8);
    if (!achou.length) {{ var li = document.createElement("li"); li.className = "nada"; li.textContent = "Nenhum vereador encontrado nas {total} cadeiras com Radar."; r.appendChild(li); return; }}
    achou.forEach(function (v) {{
      var li = document.createElement("li"), a = document.createElement("a"); a.href = v.u;
      if (v.f) {{ var im = document.createElement("img"); im.src = v.f; im.alt = ""; im.width = 40; im.height = 40; a.appendChild(im); }}
      var s = document.createElement("span"), b = document.createElement("b"); b.textContent = v.n; s.appendChild(b);
      var sm = document.createElement("small"); sm.textContent = (v.p ? v.p + " · " : "") + v.m; s.appendChild(sm);
      a.appendChild(s); li.appendChild(a); r.appendChild(li);
    }});
  }});
}})();
</script>
"""
    (BASE / "index.html").write_text(pagina("Radar Prévias — vereadores do Amapá", corpo,
        f"Presença, propostas e votos dos {total} vereadores de " + " e ".join(d["cidade"] for d in cidades.values()) +
        ", só com dados oficiais das Câmaras. Sem nota e sem opinião.", raiz="", onde=BASE), encoding="utf-8")


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
    if (RAIZ / "site" / "og").exists():
        shutil.copytree(RAIZ / "site" / "og", BASE / "og")
    for arq in ("favicon.png", "logo-previas.png"):
        if (RAIZ / "site" / arq).exists():
            shutil.copy(RAIZ / "site" / arq, BASE / arq)
    cidades = {}
    for cid in lista:
        d = json.loads((RAIZ / "dados" / "site" / f"{cid}.json").read_text(encoding="utf-8"))
        preparar_mesa(cid, d)
        cidades[cid] = d
        NOMES_CIDADES[cid] = d["cidade"]
    for cid, d in cidades.items():
        gerar_cidade(cid, d)
    gerar_inicio(cidades)
    print("site gerado em", PUBLICO)


if __name__ == "__main__":
    main(sys.argv[1:] or ["santana"])
