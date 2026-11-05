---
name: Well Studio Web
description: Editor de fotos com a identidade original Well V5, carvão e ouro velho.
colors:
  bg: "#141513"
  surface: "#1c1d1a"
  surface-raised: "#24251f"
  ink: "#eee8dc"
  muted: "#b4afa4"
  gold: "#b69a61"
  gold-hover: "#cbb17b"
  gold-soft: "#393122"
  line: "#3c3d33"
  success: "#a3c7a2"
  error: "#f09d8e"
typography:
  display:
    fontFamily: "Manrope, sans-serif"
    fontSize: "25px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Manrope, sans-serif"
    fontSize: "clamp(20px, 2.2vw, 29px)"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Manrope, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Manrope, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Manrope, sans-serif"
    fontSize: "12px"
    fontWeight: 600
rounded:
  control: "4px"
  button: "5px"
  preview: "7px"
  dialog: "10px"
spacing:
  compact: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  section: "24px"
components:
  button-primary:
    backgroundColor: "{colors.gold}"
    textColor: "#171812"
    typography: "{typography.label}"
    rounded: "{rounded.button}"
    padding: "10px 16px"
  button-primary-hover:
    backgroundColor: "{colors.gold-hover}"
  button-secondary:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "10px 16px"
  button-subtle:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    rounded: "{rounded.button}"
    padding: "10px 16px"
  coordinate-input:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "8px 7px"
  position-preset:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    padding: "6px 3px"
    height: "37px"
  photo-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    rounded: "{rounded.button}"
    padding: "4px"
    width: "117px"
  preview-toolbar:
    backgroundColor: "{colors.surface}"
    height: "47px"
    padding: "5px 8px"
---

# Design System: Well Studio Web

## Overview

**Creative North Star: "Identidade V5 da Well"**

Expansão para navegador da identidade V5 fornecida pelo usuário: fundo original Well, marca real, carvão e ouro velho. Esses recursos são a autoridade visual; os aplicativos nativos V3, V4 e V5 permanecem preservados.

A interface oferece uma moldura escura e discreta para as fotos de imóveis. Superfícies tonais, divisórias finas e ferramentas compactas sustentam a operação. O ouro orienta ações e seleção sem competir com a foto.

**Key Characteristics:**
- Fundo e logos originais da Well.
- Carvão em camadas, texto quente e ouro velho.
- Densidade de ferramenta, com foto como conteúdo principal.
- Estados explícitos e foco visível.

## Colors

Os tokens do frontmatter correspondem às variáveis de `src/styles.css` e são normativos.

### Primary
- **Ouro velho** (`gold`): ações principais, seleção, ranges e detalhes da marca.
- **Ouro iluminado** (`gold-hover`): hover das ações e foco de teclado.
- **Ouro sombreado** (`gold-soft`): fundo das ferramentas e posições selecionadas.

### Neutral
- **Carvão de fundo** (`bg`): ambiente geral e campos numéricos.
- **Carvão de painel** (`surface`): cabeçalho, ajustes e ferramentas.
- **Carvão elevado** (`surface-raised`): botões secundários e hover discreto.
- **Marfim quente** (`ink`): texto principal.
- **Cinza quente** (`muted`): instruções e texto secundário.
- **Divisória mineral** (`line`): limites entre grupos, campos e painéis.

`success` e `error` comunicam resultado e falha; não são novos acentos de marca. O popup do select nativo é controlado pelo sistema operacional.

**The Selection Rule.** Seleção combina ouro com contorno, fundo e estado acessível; não depende apenas da cor.

## Typography

Manrope local em pesos 400, 500, 600 e 700, com fallback sans-serif. A marca tipográfica combina “Well” em negrito e “Studio” regular. Números de zoom e coordenadas usam algarismos tabulares.

A escala do frontmatter descreve marca, convite do estado vazio, títulos de painel, corpo da ajuda e ações principais. Até 800 px, a marca usa 21 px, o convite 24 px e o nome da foto 16 px. Rótulos auxiliares existentes abaixo dessa escala não estabelecem uma recomendação para novos textos. Ícones Lucide usam traço fino e dimensões usuais de 16–18 px.

## Layout

A composição da superfície está em `.impeccable/surfaces/editor.md`: foto à esquerda, ferramentas acima, faixa de fotos abaixo e ajustes à direita. No desktop, o aplicativo usa altura de viewport, cabeçalho de 88 px, rodapé de 34 px e altura mínima de 700 px. A coluna de ajustes rola internamente e mantém o bloco de download separado.

A coluna mede 330 px no desktop padrão, 300 px até 1100 px e 360 px a partir de 1650 px. Ajustes usam divisórias e espaçamento vertical. Até 800 px, o fluxo é vertical, com foto e lote antes dos ajustes e duas colunas internas de campos. Até 520 px, os ajustes ficam em uma coluna. A faixa de fotos tem rolagem horizontal própria. O controle 1:1 é ocultado até 1100 px. A página não deve exigir rolagem horizontal.

## Elevation & Depth

Painéis e controles se distinguem principalmente por tons e bordas. Sombras suaves são reservadas à foto dentro do canvas e ao diálogo de ajuda. O diálogo usa backdrop escuro. O fundo original Well aparece na área de prévia sob uma camada escura.

**The Frame Rule.** A moldura da interface mantém seu contraste discreto para a fotografia continuar sendo o destaque.

## Shapes

Controles têm cantos levemente arredondados, com raios distintos para campos, botões, prévia e diálogo. Bordas finas de um pixel delimitam superfícies e estados. Grupos de ajustes não ganham elevação decorativa individual.

## Components

### Buttons

Ouro sólido marca adicionar e baixar fotos. O secundário usa superfície elevada; o sutil é transparente com texto secundário. Hover muda os tons sem deslocar o controle. Foco usa contorno dourado de 2 px afastado 4 px. Botões desabilitados reduzem opacidade e indicam indisponibilidade.

### Inputs / Fields

Coordenadas usam campos escuros com unidade de porcentagem visível; a borda muda para ouro no foco. Ranges mantém o acento dourado e valor junto ao rótulo. O select nativo compartilha fundo, borda e raio dos campos. Erros aparecem em texto junto ao campo.

### Navigation

A barra de prévia agrupa mover logo, navegar e zoom. Ferramenta ativa usa fundo ouro sombreado e `aria-pressed`. O canvas tem foco e permite operação por teclado. A seleção dourada pertence apenas à prévia.

### Position Presets

A grade de nove posições usa símbolos geométricos e nomes curtos. Padrão Well e posição livre são ações largas da mesma família. Seleção usa borda, texto e fundo dourados e estado `aria-pressed`.

### Photo Cards

A faixa de fotos apresenta miniatura, nome truncado e orientação. A foto selecionada ganha borda dourada e fundo de seleção. Exportação e erro aparecem com símbolo e rótulo acessível. O app só mostra fotos realmente adicionadas ao lote.

### Help Dialog

Diálogo nativo com três etapas, atalhos e nota de processamento local. Usa fundo de painel, cantos suaves e sombra difusa. Escape fecha a ajuda; o diálogo nativo contém foco e o devolve ao acionador. O botão de ajuda tem nome acessível mesmo quando seu texto visual é ocultado no mobile.

Transições de cor são curtas; carregamento usa indicador animado. A implementação respeita movimento reduzido e cores forçadas. Durante importação e exportação, alterações do lote e dos ajustes são bloqueadas; navegação da prévia permanece disponível quando possível.

## Do's and Don'ts

### Do:
- **Do** preservar fundo, marca e logos originais da Well.
- **Do** usar ouro para ações, seleção e foco dentro da paleta existente.
- **Do** combinar texto, ícone e estado acessível para comunicar seleção e resultado.
- **Do** priorizar a leitura da foto e a previsibilidade dos ajustes globais.

### Don't:
- **Don't** substituir a identidade V5 por novas cores de marca ou logos inventados.
- **Don't** inserir fotos fictícias no lote real do usuário.
- **Don't** exportar a moldura ou a seleção que só existe na prévia.
- **Don't** tratar zoom e pan da prévia como alterações da resolução de exportação.
