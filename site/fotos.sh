#!/bin/sh
# Gera as miniaturas dos vereadores (quadrado centrado no rosto) a partir das
# fotos oficiais. Roda no Mac (usa o reconhecimento de rosto do macOS);
# as miniaturas ficam salvas em site/fotos/<cidade>/ e vão junto no repositório.
# Uso: sh site/fotos.sh santana
set -e
CID=${1:-santana}
cd "$(dirname "$0")/.."
TMP=$(mktemp -d)
swiftc -O site/recortar_rosto.swift -o "$TMP/recortar"
mkdir -p "site/fotos/$CID"
python3 -c "
import json
for v in json.load(open('dados/site/$CID.json'))['vereadores']: print(v['slug'], v['foto'] or '')" | while read slug url; do
  [ -z "$url" ] && continue
  # Foto melhor enviada à mão (site/fotos/originais/<cidade>/<slug>.jpg) tem prioridade sobre a do SAPL.
  if [ -f "site/fotos/originais/$CID/$slug.jpg" ]; then
    printf "%-28s (original local) " "$slug" && "$TMP/recortar" "site/fotos/originais/$CID/$slug.jpg" "site/fotos/$CID/$slug.jpg" 320
    continue
  fi
  curl -sf -A "PreviasRadar/0.1" "$url" -o "$TMP/$slug" && printf "%-28s " "$slug" && "$TMP/recortar" "$TMP/$slug" "site/fotos/$CID/$slug.jpg" 320
  sleep 0.3
done
rm -rf "$TMP"
