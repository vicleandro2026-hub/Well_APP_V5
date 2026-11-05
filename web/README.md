# Well Studio Web V5

Editor de marca d'água Well Imóveis para navegador. Versão independente dos aplicativos Windows e macOS do repositório.

## Usar

1. Adicione fotos JPG, PNG ou WebP, ou arraste os arquivos para o editor.
2. Misture fotos verticais e horizontais: o logo correspondente é selecionado automaticamente. Fotos quadradas usam o logo horizontal.
3. Escolha o padrão Well, uma das nove posições ou arraste o logo na prévia. Os ajustes de posição proporcional, tamanho, margem e opacidade valem para todo o lote.
4. Use a roda do mouse para zoom, a ferramenta Navegar ou Espaço + arrastar para pan. Home ajusta a foto inteira. Setas movem o logo; Shift aumenta o passo.
5. Baixe uma foto diretamente ou várias fotos em ZIP. O navegador escolhe o destino do download, normalmente a pasta Downloads.

Em telas de toque, arraste o logo e use dois dedos para aproximar e navegar. Os ajustes ficam abaixo da prévia em celulares.

## Privacidade e limites

- As fotos são processadas na memória do navegador. O app não envia fotos a servidores, não possui conta, telemetria ou armazenamento de fotos.
- Fechar ou atualizar a página encerra o lote. Os arquivos originais não são alterados.
- Até 200 fotos por lote, 100 MB e 80 megapixels por foto. O ZIP tem limite de 512 MB. A capacidade real depende da memória do aparelho.
- A exportação preserva as dimensões em pixels e respeita a orientação da foto, mas reencoda a imagem. Não preserva EXIF, GPS, perfis ICC ou outros metadados originais. JPG usa qualidade 95%.
- JPG, PNG e WebP estáticos. HEIC, RAW e animações não são suportados. Converta esses arquivos antes de adicionar.
- Navegadores modernos: Chrome, Edge, Firefox e Safari. Se o navegador não exportar o formato escolhido, selecione JPG ou PNG.
- O botão Cancelar interrompe o lote após a foto em processamento; nenhum arquivo parcial é baixado.

## Desenvolvimento

Requer Node.js 22.12 ou superior (recomendado 24).

```sh
npm ci
npm run dev
npm run build
```

O build estático fica em `dist/`. Sem variáveis de ambiente, banco de dados ou backend. Fontes e logos são servidos pelo próprio site.

## Vercel

Importar `vicleandro2026-hub/Well_APP_V5`, branch `main`, diretório raiz `web`, framework Vite. O arquivo `web/vercel.json` define o build e os cabeçalhos. Os próximos pushes à branch principal atualizam a publicação pela integração Git da Vercel.

Os aplicativos nativos permanecem independentes desta pasta. Não adicionar credenciais, arquivos `.env`, cache ou `node_modules` ao repositório.
