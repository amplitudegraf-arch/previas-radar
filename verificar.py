"""Confere os dados antes de publicar. Se algo estiver errado, sai com erro
e o robô NÃO publica (o site continua com a versão anterior).

Uso: python3 verificar.py santana
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MINIMOS = {
    "santana": {"vereadores": 15, "sessoes": 100, "propostas": 3000, "votacoes_nominais": 200},
    "porto-grande": {"vereadores": 11, "sessoes": 60, "propostas": 800, "votacoes_nominais": 90},
}


def main(cid):
    d = json.loads((RAIZ / "dados" / "site" / f"{cid}.json").read_text(encoding="utf-8"))
    m = MINIMOS[cid]
    s = d["sessoes"]
    propostas = len({p["id"] for v in d["vereadores"] for p in v["propostas"]})
    erros = []
    if len(d["vereadores"]) < m["vereadores"]:
        erros.append(f"só {len(d['vereadores'])} vereadores")
    if s["com_registro_presenca"] < m["sessoes"]:
        erros.append(f"só {s['com_registro_presenca']} sessões com presença")
    if propostas < m["propostas"]:
        erros.append(f"só {propostas} propostas")
    if s["votacoes_nominais"] < m["votacoes_nominais"]:
        erros.append(f"só {s['votacoes_nominais']} votações nominais")
    if s.get("votos_de_quem_nao_consta_presente", 0) != 0:
        erros.append(f"{s['votos_de_quem_nao_consta_presente']} votos de quem não consta como presente (presença incompleta)")
    for v in d["vereadores"]:
        ids = [p["id"] for p in v["propostas"]]
        if len(ids) != len(set(ids)):
            erros.append(f"{v['nome']}: propostas repetidas")
    if erros:
        print("NÃO PUBLICAR —", "; ".join(erros))
        sys.exit(1)
    print(f"ok: {len(d['vereadores'])} vereadores, {s['com_registro_presenca']} sessões, {propostas} propostas, "
          f"{s['votacoes_nominais']} votações nominais, conferência de presença x votos sem divergência")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "santana")
