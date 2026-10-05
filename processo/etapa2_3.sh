#!/bin/bash
# Uso: ./etapa2_3.sh <URL_RECORTE_PNG> <URL_ORIGINAL_JPG> <SAIDA.jpg> [args extras do limpar_referencia.py]
# Roda no sandbox do Higgsfield (precisa de ImageMagick 6 + python3/numpy/Pillow).
set -e
REC="$1"; ORIG="$2"; OUT="$3"; shift 3
curl -sfo recorte.png "$REC"
curl -sfo original.jpg "$ORIG"
# Máscara: só o maior bloco (tira ilhas da pedra) + fechamento (tapa "dentes" na banda,
# senão a IA entende a falha como aliança aberta/ajustável).
convert recorte.png -alpha extract -threshold 50% -resize 50% m0.png
convert m0.png -morphology Erode Disk:12 \
  -define connected-components:keep-top=1 -define connected-components:mean-color=true \
  -connected-components 8 -morphology Dilate Disk:16 m1.png
convert m0.png m1.png -compose Multiply -composite \
  -morphology Close Disk:12 -resize 200% -threshold 50% -blur 0x1.5 mascara.png
# Cor vem da foto original (o recorte zera a cor no que ele achou que era fundo).
convert original.jpg mascara.png -alpha off -compose CopyOpacity -composite base.png
python3 limpar_referencia.py base.png "$OUT" "$@"
