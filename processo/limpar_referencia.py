#!/usr/bin/env python3
"""
ETAPA 2 do pipeline Zappa — limpar a foto de referência antes da IA.

Problema que resolve:
  As fotos originais foram feitas com a aliança em cima de pedras escuras
  (ametista, pedra preta, expositor marrom). O ouro polido reflete a pedra,
  e a IA copia esse reflexo como se fosse parte da peça (linha preta na banda).

O que faz:
  1. Recebe o recorte da aliança (PNG com fundo transparente, gerado pelo
     "remove background" do Higgsfield na etapa 1).
  2. Dentro da aliança:
     - troca tons roxos/azulados (reflexo de ametista) pelo tom do ouro;
     - clareia só as sombras escuras do metal (curva de levantamento de
       sombras), sem mexer nos brilhos;
     - NÃO mexe nas pedras (pixels claros e pouco saturados = zircônia/brilhante).
  3. Remove resíduo semitransparente da pedra e aplica a aliança sobre
     fundo branco puro.

Uso:
  python3 limpar_referencia.py recorte.png saida.jpg [--forca 0.55] [--limite 0.60]

Parâmetros:
  --forca   quanto clarear as sombras (0 = nada, 1 = máximo). Padrão 0.55.
  --limite  até que brilho (0–1) um pixel é considerado "sombra". Padrão 0.60.
  Linha prata (ALI-PRA): use --prata (não força o tom para dourado).
"""
import argparse
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("entrada")
ap.add_argument("saida")
ap.add_argument("--forca", type=float, default=0.55)
ap.add_argument("--limite", type=float, default=0.60)
ap.add_argument("--prata", action="store_true")
ap.add_argument("--mascara", help="PNG P&B só com a peça (gerado pelo ImageMagick, ver PROCESSO.md)")
a = ap.parse_args()

rgba = Image.open(a.entrada).convert("RGBA")
alpha = np.asarray(rgba.split()[3]).astype(np.float32) / 255.0
if a.mascara:
    # Remove "ilhas" que o remove-background deixou (pedaços da pedra no furo do anel).
    m = np.asarray(Image.open(a.mascara).convert("L")) > 127
    alpha = np.where(m, alpha, 0.0)
hsv = np.asarray(rgba.convert("RGB").convert("HSV")).astype(np.float32) / 255.0
H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]

# Máscara da peça: só o que o remove-background marcou com segurança.
peca = alpha > 0.8

# Pedras da aliança: claras e pouco saturadas -> protegidas.
pedra = (S < 0.25) & (V > 0.50)
metal = peca & ~pedra

if not a.prata:
    # Tom de referência do ouro = mediana dos pixels de metal bem iluminados.
    ref = metal & (V > 0.55) & (S > 0.35)
    h_ouro = float(np.median(H[ref]))
    s_ouro = float(np.median(S[ref]))
    # Reflexo de ametista: matizes fora da faixa do ouro (roxo/azul/verde).
    dist = np.minimum(np.abs(H - h_ouro), 1 - np.abs(H - h_ouro))
    fora = metal & (dist > 0.06)
    H = np.where(fora, h_ouro, H)
    S = np.where(fora, np.maximum(S, s_ouro * 0.8), S)
else:
    # Prata: o "reflexo" aparece como cor; neutraliza dessaturando.
    S = np.where(metal, S * 0.3, S)

# Levantar sombras só no metal: quanto mais escuro, mais sobe; brilhos intactos.
peso = np.clip(1 - V / a.limite, 0, 1)
V = np.where(metal, V + a.forca * (1 - V) * peso, V)
if not a.prata:
    # Sombra clareada fica "cáqui"; devolve matiz e saturação do ouro na mesma proporção.
    H = np.where(metal, H + (h_ouro - H) * peso, H)
    S = np.where(metal, S + (s_ouro - S) * peso * 0.9, S)

rgb = Image.fromarray((np.dstack([H, S, V]).clip(0, 1) * 255).astype(np.uint8), "HSV").convert("RGB")
rgb = np.asarray(rgb).astype(np.float32)

# Alfa: descarta o "fantasma" semitransparente da pedra, mantém borda suave.
af = np.clip((alpha - 0.45) / 0.35, 0, 1)[..., None]
branco = np.full_like(rgb, 255.0)
out = (rgb * af + branco * (1 - af)).astype(np.uint8)
Image.fromarray(out).save(a.saida, quality=95)
print("ok", a.saida)
