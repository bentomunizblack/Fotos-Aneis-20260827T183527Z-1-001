# Zappa — Refação das fotos de alianças com IA

Processo para transformar as fotos originais (aliança sobre pedra) em foto de catálogo premium com fundo branco, **sem alterar a peça**. Validado na ALI-BAS-001 em 05/10/2026.

## Fontes

| O quê | Onde |
|---|---|
| Fotos leves (entrada do pipeline) | `github.com/bentomunizblack/Fotos-Aneis-20260827T183527Z-1-001` — público, 195 arquivos `ALI-<linha>-<nº>.jpg`, 2000×2000 |
| Fotos originais pesadas | Drive do Bento → pasta "Fotos Aneis" (só se a leve perder detalhe) |
| URL direta de cada foto | `https://raw.githubusercontent.com/bentomunizblack/Fotos-Aneis-20260827T183527Z-1-001/main/<ARQUIVO>.jpg` |

Linhas: ELI 34 · 3G 29 · 5G 28 · BAS 26 · 4G 16 · BOD 16 · 68 10 · 1218 9 · CPD 9 · FOS 9 · PRA 9.

## Por que a referência precisa ser limpa

As fotos foram feitas com a aliança sobre ametista, pedra preta ou expositor marrom. Ouro polido é espelho: a pedra aparece refletida na banda. A IA lê esse reflexo como parte da peça e reproduz uma **linha escura** na foto final. Corrigir por prompt ou por edição da imagem gerada **não resolve** (testado: o reflexo volta). A solução é tirar o reflexo **da referência**, antes da IA.

## Etapa 0 — Agrupar por peça (antes de gastar crédito)

Há várias fotos da mesma aliança em ângulos diferentes (ex.: BAS-002 e BAS-003 são a mesma peça). Montar a planilha de controle com uma linha por **peça**, escolhendo o melhor ângulo. Só a foto escolhida entra no pipeline.

## Etapa 1 — Importar e recortar (Higgsfield)

1. `media_import_url` com a URL raw do GitHub → `media_id` da original.
2. `remove_background` nesse `media_id` → PNG com fundo transparente (recorte).

## Etapas 2 e 3 — Máscara + limpeza do reflexo (sandbox do Higgsfield)

Tudo num comando só, com `etapa2_3.sh` (chama o `limpar_referencia.py`):

```bash
./etapa2_3.sh <URL_DO_RECORTE_PNG> <URL_RAW_DA_ORIGINAL> ALI-XXX-NNN_ref_limpa.jpg [--forca 0.55] [--prata]
```

O que acontece por dentro:

1. **Máscara sem ilhas.** O recorte às vezes deixa um pedaço da pedra grudado no furo do anel. O script mantém só o maior bloco (erosão → maior componente → dilatação).
2. **Fechamento de "dentes".** Onde a pedra cobria a banda, o recorte fica com falhas. Sem tapar, a IA entende a falha como **aliança aberta/ajustável** (aconteceu no teste). O script fecha falhas pequenas na máscara.
3. **Cor da foto original.** A cor vem da original (o recorte zera a cor no que achou que era fundo), e a máscara define o contorno.
4. **Limpeza do reflexo** (`limpar_referencia.py`). Dentro da peça: troca tons roxos/azuis pelo tom do ouro, clareia só as sombras escuras (brilhos intactos), devolve cor de ouro às sombras clareadas e **não mexe nas pedras**. Depois coloca a peça em fundo branco.

| Parâmetro | Padrão | Quando mudar |
|---|---|---|
| `--forca` | 0.55 | Ainda aparece faixa escura → 0.65–0.70. Ouro "chapado", sem volume → 0.45 |
| `--limite` | 0.60 | Faixa média continua escura → 0.70 |
| `--prata` | — | Obrigatório na linha PRA (não puxa para dourado) |
| Ilha de pedra que não sai | `Erode Disk:12` | Subir para 16 e `Dilate` para 20 no `etapa2_3.sh` |

**Conferência obrigatória (sem gastar crédito):** abrir a referência limpa lado a lado com a original. Mesmo desenho, mesmas pedras, nenhum reflexo roxo ou preto. Se ficou ruim, ajustar os parâmetros e rodar de novo.

## Etapa 4 — Upload da referência limpa

`media_upload` → `curl -X PUT` (com os headers `Content-Type: image/jpeg` **e** `If-None-Match: *`, senão dá 403) → `media_confirm`. O PUT tem que rodar no mesmo comando do sandbox que gerou o arquivo (o sandbox apaga os arquivos segundos depois).

## Etapa 5 — Gerar (Higgsfield, Nano Banana Pro, 1:1, count 2)

Usar **só** a referência limpa (nunca a original com pedra). Prompt base:

> Professional luxury jewelry e-commerce packshot shot inside a pure white jewelry light tent. Use the exact gold ring from the reference image (already isolated on white). Place it standing slightly tilted on a seamless pure white background (#FFFFFF), ring filling about 60% of the frame. It is a SOLID CLOSED wedding band: the band is continuous all the way around with no gap, split, seam, cut or opening anywhere (it is NOT an open or adjustable ring). The environment is entirely white, so every reflection on the polished gold is bright warm gold or soft white: NO black, dark grey, brown or purple reflection lines anywhere — not on the outer band, not on the inner surface, not at the contact point with the floor. Evenly lit gold all around, gentle gradients only. Very faint soft contact shadow under the ring. Sharp focus on the whole piece. CRITICAL product fidelity: same [descrever o desenho da peça], same stones with the same count and placement as the reference ([N] on each side), same band width and thickness, same yellow gold tone. Do not redesign or add details. No text, no props.

Trocar os colchetes pela descrição da peça. Linha prata: trocar "gold/yellow gold tone" por "silver / sterling silver tone".

## Etapa 6 — Controle de qualidade (antes de aprovar)

- [ ] Nenhuma linha ou mancha escura na banda (zoom no lado interno)
- [ ] Desenho idêntico ao original (cruzado, frisos, textura, fosco × polido)
- [ ] **Mesma quantidade de pedras** de cada lado
- [ ] Mesma largura de banda e mesmo tom de metal
- [ ] Aliança **fechada** (sem corte ou emenda na banda — a IA às vezes inventa aliança ajustável)
- [ ] Fundo branco puro, sem objetos

Reprovou por linha escura em ponto isolado → **plano B**: retoque local na imagem final. Reprovou por fidelidade → nova geração (nunca publicar peça diferente da real; risco de propaganda enganosa — CDC art. 37).

## Etapa 7 — Saída e controle (GitHub)

Cada imagem aprovada vai direto para este repo pela API do GitHub (rodando no sandbox do Higgsfield): PNG convertido para JPG 2000×2000, qualidade 90 (~150 KB), em `premium/ALI-<linha>/ALI-<linha>-<nº>_<posição>.jpg` (1 = em pé, 2 = deitada, 3 = close). Cada envio atualiza `premium/controle.csv`. **Antes de começar qualquer lote, ler o controle.csv** para não repetir peça.

Acesso: token fine-grained do Bento, só este repo, Contents read/write, válido até 04/11/2026; apagar ao fim do projeto.


- Nome: `ALI-<linha>-<nº>_premium.jpg`
- Planilha: linha por peça, com arquivo original, fotos agrupadas, `media_id` da referência limpa, job do Higgsfield aprovado, status (pendente / gerado / aprovado / refazer) e observação.

## Histórico de testes (ALI-BAS-001)

1. Geração direto da original → linha escura no meio da banda (reflexo da ametista).
2. Edição da imagem gerada pedindo para remover a linha → a linha voltou.
3. Prompt de "tenda de luz branca" com a original → melhorou, mas o reflexo continuou no lado interno.
4. Referência limpa v1 + prompt de tenda de luz → reflexo resolvido, mas a IA criou um **corte na banda** (aliança aberta), por causa de uma falha no recorte onde a pedra cobria a peça.
5. **Referência limpa v2 (com fechamento de falhas) + prompt "solid closed band"** → aprovada no controle interno: sem linha escura, banda fechada, 5 pedras de cada lado. Job escolhido: `7199383b-afc3-4e65-a46a-ab526709b206`.

IDs úteis desta peça: original importada `185475b3-2f76-4dcb-a482-644e4dffe018` · recorte `120c44fd-6f69-4673-9ab3-54f97f255aa6` · referência limpa v2 `766829e5-27c5-48b0-84f0-461849244d13`.
