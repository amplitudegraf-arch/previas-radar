// Radar Prévias — busca por bairro, pedidos repetidos, contador e filtros.
// Usa só os dados de window.RADAR (gerados a partir do sistema oficial da Câmara).
(function () {
  var R = window.RADAR;
  if (!R) return;
  var MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

  // Selo de cada tipo de demanda: cor do texto, cor de fundo e ícone.
  var P = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"';
  var TEMA = {
    "Iluminação": ["#8A6400", "#FBF1D6", '<path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.1V17h6v-.2c0-.8.4-1.6 1-2.1A7 7 0 0 0 12 2z"/>'],
    "Asfalto e buracos": ["#4A5568", "#ECEEF2", '<path d="M4 22 8 2M20 22 16 2M12 6v2M12 12v2M12 18v2"/>'],
    "Limpeza e poda": ["#2F7D5B", "#E5F2EA", '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10z"/><path d="M2 21c0-3 1.9-5.4 5.1-6"/>'],
    "Pontes e passarelas": ["#7A5230", "#F3EADF", '<path d="M2 16h20M4 16V9M20 16V9M2 9c4 0 6-4 10-4s6 4 10 4M8 16v-5M12 16v-6M16 16v-5"/>'],
    "Drenagem e canais": ["#1F6E8C", "#E2F0F5", '<path d="M2 7c2-2 4-2 6 0s4 2 6 0 4-2 6 0M2 12c2-2 4-2 6 0s4 2 6 0 4-2 6 0M2 17c2-2 4-2 6 0s4 2 6 0 4-2 6 0"/>'],
    "Água e esgoto": ["#2F5B9A", "#E9EFF8", '<path d="M12 2.7S6 9.4 6 14a6 6 0 0 0 12 0c0-4.6-6-11.3-6-11.3z"/>'],
    "Trânsito": ["#B9472E", "#F8E7E3", '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01"/>'],
    "Saúde": ["#A4456A", "#F8E9EF", '<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>'],
    "Educação": ["#5B4B9A", "#ECE9F6", '<path d="M2 4h7a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H2zM22 4h-7a3 3 0 0 0-3 3v14a2 2 0 0 1 2-2h8z"/>'],
    "Praças, esporte e lazer": ["#3C7A3A", "#E8F2E3", '<circle cx="12" cy="12" r="9"/><path d="M12 3a15 15 0 0 0 0 18M3 12h18"/>'],
    "Agricultura e produção rural": ["#5E7A1F", "#EEF3E0", '<path d="M12 22V10M12 10c0-4 3-7 7-7 0 4-3 7-7 7zM12 14c0-3-2.5-5.5-6-5.5 0 3.5 2.5 5.5 6 5.5z"/>'],
    "Segurança": ["#283C59", "#E8EEF6", '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'],
    "Outros pedidos": ["#5D6676", "#EEF0F3", '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>'],
    "Cobrança": ["#B9722A", "#FBF1E4", '<path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.5 8.5 0 0 1-3.8-.9L3 21l1.9-5.2A8.4 8.4 0 1 1 21 11.5z"/><path d="M9.5 9a2.5 2.5 0 0 1 4.9.8c0 1.7-2.4 2.2-2.4 3.2M12 16h.01"/>']
  };
  var PIN = '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>';

  function svg(d) { return '<svg viewBox="0 0 24 24" ' + P + ' aria-hidden="true">' + d + "</svg>"; }
  function temaDe(p) { return p.g === "cobranca" ? "Cobrança" : p.m; }
  function norm(t) {
    return (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toUpperCase().replace(/\s+/g, " ").trim();
  }
  function data(iso) { var p = iso.split("-"); return +p[2] + " " + MES[+p[1] - 1] + " " + p[0]; }
  function mesAno(iso) { var p = iso.split("-"); return MES[+p[1] - 1] + " " + p[0]; }
  function fmt(n) { return n.toLocaleString("pt-BR"); }
  function el(tag, cls, txt) {
    var x = document.createElement(tag);
    if (cls) x.className = cls;
    if (txt != null) x.textContent = txt;
    return x;
  }
  function pintar(x, t) {
    var m = TEMA[t] || TEMA["Outros pedidos"];
    x.style.setProperty("--c", m[0]); x.style.setProperty("--f", m[1]);
    x.innerHTML = svg(m[2]);
    return x;
  }
  function icone(t) { return pintar(el("span", "ic"), t); }
  function selo(t) {
    var x = pintar(el("span", "selo"), t);
    x.appendChild(document.createTextNode(t));
    return x;
  }
  function avatar(v) {
    if (v.f) { var i = el("img", "av"); i.src = v.f; i.alt = ""; i.loading = "lazy"; return i; }
    return el("span", "av");
  }

  // ---------- contador do salário (estimativa) ----------
  var cont = document.getElementById("contador");
  if (cont && R.sal) {
    var posse = new Date(R.sal.posse + "T00:00:00-03:00").getTime();
    var porMs = R.sal.mensal * 12 / (365.25 * 864e5);
    var moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
    var tick = function () { cont.textContent = moeda.format((Date.now() - posse) * porMs); };
    tick();
    if (!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) setInterval(tick, 150);
  }

  R.pedidos.forEach(function (p) { p._t = norm(p.e + " " + p.b.join(" ") + " " + p.r.join(" ")); });
  var porId = {};
  R.pedidos.forEach(function (p) { porId[p.i] = p; });

  function cartaoPedido(p) {
    var c = el("div", "pedido");
    c.appendChild(icone(temaDe(p)));
    var dir = el("div");
    dir.appendChild(el("div", "txt", p.e));
    var meta = el("div", "meta");
    meta.appendChild(selo(temaDe(p)));
    meta.appendChild(el("span", null, data(p.d)));
    meta.appendChild(el("span", null, p.t));
    if (p.b.length) meta.appendChild(el("span", null, p.b.join(", ")));
    dir.appendChild(meta);
    c.appendChild(dir);
    var rod = el("div", "rodape-ped");
    var au = el("div", "autores");
    p.a.slice(0, 3).forEach(function (i) {
      var v = R.ver[i], s = el("span");
      s.appendChild(avatar(v)); s.appendChild(document.createTextNode(v.n));
      au.appendChild(s);
    });
    if (p.a.length > 3) au.appendChild(el("span", null, "+" + (p.a.length - 3)));
    rod.appendChild(au);
    var a = el("a", "abrir", "Abrir na Câmara ↗");
    a.href = p.f; a.target = "_blank"; a.rel = "noopener";
    rod.appendChild(a);
    c.appendChild(rod);
    return c;
  }

  function contar(lista, chave) {
    var c = {};
    lista.forEach(function (p) { chave(p).forEach(function (k) { c[k] = (c[k] || 0) + 1; }); });
    return Object.keys(c).map(function (k) { return [k, c[k]]; }).sort(function (a, b) { return b[1] - a[1]; });
  }

  function bloco(titulo, linhas, comBarra, legenda) {
    var b = el("div", "bloco");
    b.appendChild(el("h3", null, titulo));
    if (legenda) b.appendChild(legenda);
    var max = linhas.length ? linhas[0].n : 1;
    linhas.forEach(function (L) {
      var r = el(L.tag || "div", "rank");
      if (L.href) r.href = L.href;
      if (L.click) { r.type = "button"; r.onclick = L.click; }
      r.appendChild(L.esq);
      r.appendChild(L.nome);
      r.appendChild(el("b", null, fmt(L.n)));
      if (comBarra) {
        var tr = el("span", "trilho"), f = el("span");
        f.style.width = (L.n / max * 100).toFixed(1) + "%";
        if (L.partes) {
          // barra dividida pelo tipo de pedido, nas mesmas cores de "Que tipo de proposta?"
          f.className = "pilha";
          L.partes.forEach(function (P) {
            if (!P.n) return;
            var s = el("i");
            s.style.width = (P.n / L.n * 100).toFixed(1) + "%";
            s.style.background = P.c;
            s.title = P.nome + ": " + fmt(P.n);
            f.appendChild(s);
          });
          r.title = L.partes.filter(function (P) { return P.n; }).map(function (P) { return P.nome + ": " + fmt(P.n); }).join(" · ");
        }
        tr.appendChild(f); r.appendChild(tr);
      }
      b.appendChild(r);
    });
    return b;
  }

  // ---------- busca por bairro / rua ----------
  var busca = document.getElementById("busca");
  var res = document.getElementById("resultado");
  var chips = document.querySelectorAll(".chip");
  var timer;

  function buscar(txt) { busca.value = txt; mostrar(); busca.scrollIntoView({ behavior: "smooth", block: "center" }); }

  function mostrar() {
    var q = norm(busca.value);
    chips.forEach(function (c) { c.classList.toggle("ativo", !!q && norm(c.dataset.q) === q); });
    var lista = q ? R.pedidos.filter(function (p) { return p._t.indexOf(q) >= 0; }) : R.pedidos;
    res.innerHTML = "";

    var tot = el("div", "total");
    tot.appendChild(el("strong", null, fmt(lista.length)));
    var rot = el("span");
    rot.appendChild(document.createTextNode(lista.length === 1 ? "pedido " : "pedidos "));
    if (q) { rot.appendChild(document.createTextNode("com ")); rot.appendChild(el("b", null, "“" + busca.value.trim() + "”")); }
    else { rot.appendChild(document.createTextNode("para a ")); rot.appendChild(el("b", null, "cidade inteira")); rot.appendChild(document.createTextNode(" até agora")); }
    tot.appendChild(rot);
    res.appendChild(tot);
    if (!lista.length) {
      res.appendChild(el("p", "nota", "Nenhum pedido encontrado. Tente só uma parte do nome (por exemplo, “Provedor” em vez de “Provedor I”) ou o nome da rua sem “Rua” ou “Avenida”."));
      return;
    }

    var col = el("div", "colunas");
    var quem = contar(lista, function (p) { return p.a.map(String); }).slice(0, 5).map(function (x) {
      var v = R.ver[+x[0]], nome = el("span", "nome");
      nome.appendChild(document.createTextNode(v.n));
      if (v.p) nome.appendChild(el("small", null, " · " + v.p));
      var partes = (R.grupos || []).map(function (G) {
        return { nome: G.n, c: G.c, n: lista.filter(function (p) { return p.g === G.g && p.a.map(String).indexOf(x[0]) >= 0; }).length };
      });
      return { tag: "a", href: v.s + (location.protocol === "file:" ? "/index.html" : "/"), esq: avatar(v), nome: nome, n: x[1], partes: R.grupos ? partes : null };
    });
    var leg = null;
    if (R.grupos) {
      leg = el("div", "legenda-q");
      R.grupos.forEach(function (G) {
        var it = el("span"), q = el("i");
        q.style.background = G.c;
        it.appendChild(q); it.appendChild(document.createTextNode(G.n));
        leg.appendChild(it);
      });
    }
    col.appendChild(bloco("Quem mais propôs", quem, true, leg));
    var oque = contar(lista, function (p) { return [temaDe(p)]; }).slice(0, 6).map(function (x) {
      return { esq: icone(x[0]), nome: el("span", "nome", x[0]), n: x[1] };
    });
    col.appendChild(bloco("O que mais pedem", oque, false));
    var lug = (q ? contar(lista, function (p) { return p.r.slice(0, 1); }) : contar(lista, function (p) { return p.b; })).slice(0, 6);
    if (lug.length) {
      col.appendChild(bloco(q ? "Ruas mais citadas" : "Bairros mais citados", lug.map(function (x) {
        var pin = el("span", "ic");
        pin.style.setProperty("--c", "#283C59"); pin.style.setProperty("--f", "#E8EEF6"); pin.innerHTML = svg(PIN);
        var alvo = x[0].replace(/^(Rua|Avenida|Travessa|Alameda|Passagem|Ramal|Estrada|Rodovia) /, "");
        return { tag: "button", click: function () { buscar(alvo); }, esq: pin, nome: el("span", "nome", x[0]), n: x[1] };
      }), false));
    }
    res.appendChild(col);

    var b = el("div", "bloco");
    b.appendChild(el("h3", null, q ? "Os pedidos mais recentes" : "Os pedidos mais recentes da cidade"));
    res.appendChild(b);
    var mostrados = 0;
    var botao = el("button", "mais");
    function mais() {
      lista.slice(mostrados, mostrados + 6).forEach(function (p) { b.insertBefore(cartaoPedido(p), botao.parentNode ? botao : null); });
      mostrados += 6;
      var resta = lista.length - mostrados;
      if (resta > 0) { botao.textContent = "Mostrar mais " + Math.min(6, resta) + " de " + fmt(resta); b.appendChild(botao); }
      else if (botao.parentNode) botao.remove();
    }
    botao.onclick = mais;
    mais();
  }
  if (busca) {
    busca.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(mostrar, 200); });
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        busca.value = norm(busca.value) === norm(c.dataset.q) ? "" : c.dataset.q;
        mostrar();
      });
    });
    mostrar();
  }

  // ---------- pedidos repetidos + "cobre uma resposta" ----------
  var PEDIDO_DE = {
    "Iluminação": "iluminação", "Asfalto e buracos": "asfalto e conserto de buracos", "Limpeza e poda": "limpeza e poda",
    "Pontes e passarelas": "conserto de ponte ou passarela", "Drenagem e canais": "drenagem", "Água e esgoto": "conserto de água e esgoto",
    "Trânsito": "melhoria no trânsito", "Saúde": "melhoria na saúde", "Educação": "melhoria em escola",
    "Praças, esporte e lazer": "melhoria em praça e área de lazer", "Segurança": "segurança",
    "Agricultura e produção rural": "apoio à produção rural"
  };
  var SITE = /^https?:/.test(location.protocol) ? location.origin + location.pathname : "";
  var folha = document.getElementById("folha");
  var corpoFolha = document.getElementById("folha-corpo");
  if (folha) {
    folha.querySelector(".fechar").onclick = function () { folha.close(); };
    folha.addEventListener("click", function (ev) { if (ev.target === folha) folha.close(); });
  }
  function artigo(rua) { return /^(Ramal|Beco)\b/.test(rua) ? "no " : "na "; }

  function abrirRep(r) {
    if (!folha) return;
    var itens = r.ids.map(function (i) { return porId[i]; }).sort(function (a, b) { return a.d < b.d ? 1 : -1; });
    var cnt = {};
    itens.forEach(function (p) { p.a.forEach(function (a) { cnt[a] = (cnt[a] || 0) + 1; }); });
    var quem = Object.keys(cnt).map(Number).sort(function (a, b) { return cnt[b] - cnt[a] || R.ver[a].n.localeCompare(R.ver[b].n, "pt-BR"); });

    corpoFolha.innerHTML = "";
    var topo = el("div", "folha-topo");
    topo.appendChild(icone(r.m));
    var tt = el("div");
    var h = el("h2", null, r.r); h.id = "folha-titulo"; tt.appendChild(h);
    tt.appendChild(el("p", null, r.m + " · pedido " + r.n + " vezes até agora" + (r.b ? " · " + r.b : "")));
    topo.appendChild(tt);
    corpoFolha.appendChild(topo);

    var cob = el("div", "cob");
    cob.appendChild(el("h3", null, "Cobre uma resposta"));
    cob.appendChild(el("p", null, "A mensagem já vem pronta. Escolha o vereador, ajuste o texto se quiser e envie."));
    var l1 = el("label", "campo", "Para quem");
    var sel = el("select");
    quem.forEach(function (a) {
      var o = el("option", null, R.ver[a].n + " (" + cnt[a] + (cnt[a] === 1 ? " pedido" : " pedidos") + " para esta rua)");
      o.value = a; sel.appendChild(o);
    });
    l1.appendChild(sel); cob.appendChild(l1);
    var l2 = el("label", "campo", "Mensagem");
    var ta = el("textarea");
    l2.appendChild(ta); cob.appendChild(l2);
    var acoes = el("div", "acoes"), contato = el("div", "contato");
    cob.appendChild(acoes); cob.appendChild(contato);
    corpoFolha.appendChild(cob);

    function mensagem(a) {
      var v = R.ver[a], k = cnt[a];
      var trat = v.x === "F" ? "vereadora " : v.x === "M" ? "vereador " : "";
      return "Olá, " + trat + v.n + ". Moro em " + (window.CIDADE || "Santana") + ". A Câmara já recebeu " + r.n + " pedidos de " +
        (PEDIDO_DE[r.m] || "melhoria") + " " + artigo(r.r) + r.r + (r.b ? ", " + r.b : "") + ", desde " + mesAno(r.d0) + ". " +
        (k === 1 ? "Um deles saiu" : k + " deles saíram") + " do seu gabinete. O problema continua? O que a Prefeitura respondeu? O que ainda dá para fazer?" +
        (SITE ? "\n\nFonte: " + SITE : "");
    }
    function links() {
      var v = R.ver[+sel.value], t = encodeURIComponent(ta.value);
      acoes.innerHTML = "";
      if (v.e) {
        var m = el("a", "btn", "Enviar por e-mail");
        m.href = "mailto:" + v.e + "?subject=" + encodeURIComponent(r.r + ": pedido repetido " + r.n + " vezes") + "&body=" + t;
        acoes.appendChild(m);
      }
      var w = el("a", "btn wa", "Mandar no grupo do bairro");
      w.href = "https://wa.me/?text=" + t; w.target = "_blank"; w.rel = "noopener";
      acoes.appendChild(w);
      var c = el("button", "btn claro", "Copiar mensagem"); c.type = "button";
      c.onclick = function () {
        var ok = function () { c.textContent = "Copiado"; };
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(ta.value).then(ok, function () { ta.select(); c.textContent = "Selecionado: copie com Ctrl+C"; });
        else { ta.select(); c.textContent = "Selecionado: copie com Ctrl+C"; }
      };
      acoes.appendChild(c);
      contato.textContent = "";
      if (v.e) { contato.appendChild(document.createTextNode("E-mail oficial: ")); contato.appendChild(el("b", null, v.e)); }
      else contato.appendChild(document.createTextNode("A Câmara não divulga e-mail deste gabinete."));
      contato.appendChild(el("br"));
      contato.appendChild(document.createTextNode("A Câmara não divulga WhatsApp deste gabinete."));
    }
    function preencher() { ta.value = mensagem(+sel.value); links(); }
    sel.onchange = preencher;
    ta.oninput = links;
    preencher();

    corpoFolha.appendChild(el("h4", null, "Os " + r.n + " pedidos, do mais recente ao mais antigo"));
    itens.forEach(function (p) { corpoFolha.appendChild(cartaoPedido(p)); });
    folha.showModal();
    folha.scrollTop = 0;
  }

  var caixaRep = document.getElementById("lista-rep");
  if (caixaRep) {
    var vistos = 0;
    var botaoRep = el("button", "mais");
    botaoRep.style.gridColumn = "1/-1";
    function maisRep() {
      R.rep.slice(vistos, vistos + 9).forEach(function (r) {
        var d = el("button", "rep");
        d.type = "button";
        var vz = el("div", "vezes", String(r.n)); vz.appendChild(el("small", null, "VEZES"));
        var onde = el("div", "onde");
        onde.appendChild(el("b", null, r.r));
        if (r.b) onde.appendChild(el("small", null, r.b));
        var meta = el("div", "meta");
        meta.appendChild(selo(r.m));
        meta.appendChild(el("span", null, r.a + (r.a === 1 ? " vereador pediu" : " vereadores pediram")));
        meta.appendChild(el("span", null, "de " + mesAno(r.d0) + " a " + mesAno(r.d1)));
        onde.appendChild(meta);
        onde.appendChild(el("span", "cobrar", "Ver pedidos e cobrar →"));
        d.appendChild(vz); d.appendChild(onde);
        d.onclick = function () { abrirRep(r); };
        caixaRep.insertBefore(d, botaoRep.parentNode ? botaoRep : null);
      });
      vistos += 9;
      var resta = R.rep.length - vistos;
      if (resta > 0) { botaoRep.textContent = "Mostrar mais ruas (" + resta + " na fila)"; caixaRep.appendChild(botaoRep); }
      else if (botaoRep.parentNode) botaoRep.remove();
    }
    botaoRep.onclick = maisRep;
    maisRep();
  }

  // ---------- filtros dos crachás ----------
  var cards = document.getElementById("cards");
  if (cards) {
    var nome = document.getElementById("nome"), partido = document.getElementById("partido"), ordem = document.getElementById("ordem");
    var mostrando = document.getElementById("mostrando");
    var todos = Array.prototype.slice.call(cards.children);
    function aplicar() {
      var q = norm(nome.value), pt = partido.value, o = ordem.value, n = 0;
      var lista = todos.slice().sort(function (a, b) {
        if (o === "nome") return a.dataset.nome.localeCompare(b.dataset.nome, "pt-BR");
        if (o === "pres" || o === "pres_mais") {
          // percentual sobre poucas sessões não se compara: vai para o fim
          var dp = (+a.dataset.poucas) - (+b.dataset.poucas);
          if (dp) return dp;
          var d = parseFloat(a.dataset.pres) - parseFloat(b.dataset.pres);
          return (o === "pres" ? d : -d) || a.dataset.nome.localeCompare(b.dataset.nome, "pt-BR");
        }
        return (+b.dataset[o]) - (+a.dataset[o]) || a.dataset.nome.localeCompare(b.dataset.nome, "pt-BR");
      });
      var aviso = document.getElementById("aviso-poucas");
      if (aviso) aviso.hidden = !((o === "pres" || o === "pres_mais") && todos.some(function (c) { return c.dataset.poucas === "1"; }));
      lista.forEach(function (c) {
        var dz = c.querySelector(".destaque");
        if (dz) dz.textContent = dz.dataset[o] ? "· " + dz.dataset[o] : "";
        c.hidden = !((!q || norm(c.dataset.nome).indexOf(q) >= 0) && (!pt || c.dataset.partido === pt));
        if (!c.hidden) n++;
        cards.appendChild(c);
      });
      if (mostrando) mostrando.textContent = n === todos.length ? "Mostrando os " + n + " vereadores." : "Mostrando " + n + " de " + todos.length + " vereadores.";
    }
    [nome, partido, ordem].forEach(function (x) { x.addEventListener("input", aplicar); });
  }
})();
