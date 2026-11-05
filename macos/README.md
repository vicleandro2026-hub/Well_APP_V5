# Well Studio V5 para macOS

Código adaptado da V5 do Windows. Este projeto gera um aplicativo macOS real em um runner Mac, com versões separadas para Apple Silicon (`arm64`) e Intel (`x86_64`). As versões Windows permanecem intactas.

**Estado desta preparação:** o código e o workflow estão prontos. Ainda não existe `.app`, `.dmg` ou ZIP de aplicativo compilado nesta pasta: é necessário executar o build em macOS. O arquivo `Well_V5_macOS_codigo.zip` contém código-fonte, não o aplicativo pronto.

## Compilação pelo GitHub Actions

A edição macOS fica na pasta `macos/` do repositório `Well_APP_V5`, com o workflow na pasta `.github/workflows/` da raiz. A integração GitHub precisa ter acesso a esse repositório.

O envio dos arquivos para `main`, `master` ou `macos-build` inicia a compilação automaticamente. Também é possível abrir **Actions → Compilar Well Studio V5 para macOS → Run workflow**.

O fluxo gera dois conjuntos de arquivos:

- `Well_Studio_V5_macOS_arm64.zip` e `.dmg`: Apple Silicon.
- `Well_Studio_V5_macOS_x86_64.zip` e `.dmg`: Intel.
- Manifesto de compilação e hashes SHA-256 por arquitetura.

Os arquivos ficam em **Artifacts**, na execução da compilação, por 14 dias. O ZIP preserva o bundle `Well_app.app` e seus arquivos executáveis. O DMG permite copiar o aplicativo para Applications. Não há execução de testes funcionais nem abertura do app no workflow, conforme o fluxo solicitado.

O build usa runners macOS e Python nativo por arquitetura. Não inclui ou tenta converter um executável Windows. A configuração usa assinatura local ad-hoc, sem certificado Apple Developer ID e sem notarização Apple; isso é registrado no manifesto.

## Compilação diretamente em um Mac

Com Python 3.14 e tkinter disponíveis:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos.txt
.venv/bin/python build_macos.py
```

O resultado fica em `dist`. O script interrompe a execução em Windows para não apresentar um binário de outro sistema como um aplicativo Mac.

## Adaptações para Mac

- Abertura da pasta de saída no Finder.
- Fonte Helvetica Neue.
- Command+O, Command+Return, Command+A e Command+Q.
- Tecla de apagar do Mac para remover fotos do lote.
- Normalização da roda/trackpad e navegação com clique secundário.
- Bundle `.app`, ícone ICNS e suporte a Retina.
- Preservação do tema dark, ouro velho, fundo fornecido, logos automáticos, posições livres, zoom e pan.

## Fontes técnicas

- [Runners GitHub macOS](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)
- [Bundles macOS no PyInstaller](https://pyinstaller.org/en/stable/spec-files.html#spec-file-options-for-a-macos-bundle)
- [Arquiteturas macOS e assinatura no PyInstaller](https://pyinstaller.org/en/stable/feature-notes.html#macos-multi-arch-support)
