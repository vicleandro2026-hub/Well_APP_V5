# Estado da edição macOS

Esta pasta é uma cópia independente da V5. Os executáveis e os arquivos das versões v3, v4 e v5 para Windows não foram modificados.

`theme.py` continua sendo a fonte canônica das cores. A família tipográfica vem de `platform_support.FONT_FAMILY`, que seleciona Helvetica Neue no macOS e Segoe UI no Windows. Isso adapta o projeto à plataforma sem alterar a direção dark e ouro velho.

O código do aplicativo continua em `well_app.py`, a navegação da prévia em `preview.py` e a composição/exportação em `watermark.py`. `platform_support.py` centraliza a abertura da pasta e a normalização da roda/trackpad. O bundle macOS é definido em `Well_app_macos.spec`.

`build_macos.py` exige macOS, gera o ícone ICNS, compila o aplicativo, verifica a estrutura e a assinatura local do bundle e produz ZIP, DMG e hashes. Essa verificação faz parte do empacotamento; não há testes funcionais nem inspeção da interface.

O workflow `.github/workflows/build-macos.yml` foi preparado para Intel e Apple Silicon. Antes de sua execução, a conta GitHub deve permitir acesso ao repositório escolhido. Um ZIP desta pasta contém somente os fontes e a configuração; não equivale a um build macOS concluído.
