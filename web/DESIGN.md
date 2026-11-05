# Well Studio Web: sistema visual

## Autoridade

Expansão da identidade V5 para navegador. Manter o fundo original Well, carvão e ouro velho solicitados pelo usuário. Não substituir logos, introduzir cores comerciais novas ou alterar as versões nativas. Superfície principal: editor, modo **Operate**. O canvas ocupa o destaque visual, com ferramentas compactas e ações de download previsíveis.

## Tokens implementados

Definidos em `src/styles.css`, seletor `:root`:

| Papel | Valor |
| --- | --- |
| Fundo | `#141513` |
| Superfície | `#1c1d1a` |
| Superfície elevada | `#24251f` |
| Texto principal | `#eee8dc` |
| Texto secundário | `#b4afa4` |
| Ouro velho / ação principal | `#b69a61` |
| Ouro em hover e foco | `#cbb17b` |
| Seleção de fundo | `#393122` |
| Divisória | `#3c3d33` |
| Sucesso | `#a3c7a2` |
| Erro | `#f09d8e` |

Tipografia Manrope local, pesos 400/500/600/700. Títulos de painel 18 px, controles de desktop 10–12 px e título de marca 25 px. Raios de 4–7 px, espaços principais 8/12/16/24 px. Ícones Lucide de 16–18 px com traço fino. Todas as fontes e imagens são locais ao site.

## Layout e componentes canônicos

- Cabeçalho com marca, ajuda e Adicionar fotos; o botão usa ouro sólido e texto escuro.
- Desktop: canvas à esquerda, ajustes em coluna de 330 px à direita, faixa de fotos abaixo do canvas. Ajustes rolam dentro da coluna; download fica no rodapé da coluna.
- Até 800 px: fluxo vertical com canvas antes dos ajustes. Até 520 px: ajustes em uma coluna. Não exigir rolagem horizontal da página; a faixa de fotos tem sua própria rolagem.
- Botões, presets, campos numéricos, ranges e select nativo compartilham cores e foco dourado. O popup do select é controlado pelo sistema operacional.
- A posição selecionada usa borda e texto dourados; seleção não depende apenas de cor (`aria-pressed`). Não há sistema paralelo de componentes.
- Estado vazio real: convite para adicionar fotos. Estado carregando sobre o canvas, erros por arquivo e status de exportação com progresso e cancelamento.
- Faixa de fotos: miniatura, nome, orientação e sinal de erro/exportação. Não usar imagens fictícias como fotos do lote.

## Interações

Canvas com foco de teclado, arraste do logo e pan, zoom na posição do cursor e pinch em telas de toque. A seleção dourada aparece só na prévia, nunca no arquivo exportado. Setas deslocam o logo por 1 pixel; Shift por 10. O grupo de ferramentas usa `aria-pressed` e rótulos visíveis. Campos X/Y mostram o centro efetivo do logo em porcentagem da foto.

Os ajustes valem para todas as fotos. Durante importação/exportação, alterações no lote e nos ajustes ficam desabilitadas. A exportação oferece cancelamento, mantém as fotos no lote e permite corrigir/repetir. A prévia não altera a resolução exportada.

Diálogo nativo de ajuda com fechamento por Escape, foco contido e retorno ao botão. Erros em texto, estado anunciado em região `aria-live`, elementos rotulados, link de pular para o editor. Movimento reduzido e cores forçadas respeitados. Fotos são conteúdo do usuário e nunca enviadas pelo app.
