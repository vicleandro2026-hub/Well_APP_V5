# Well Studio Web

Versão web V5 do editor de marcas d'água Well Imóveis. Público principal: usuário com pouca experiência técnica, que prepara fotos de imóveis em lote. Sucesso é adicionar fotos, conferir a marca e baixar o resultado sem instalar nada.

A interface e as instruções são em português do Brasil. O app é público, sem login. As fotos são processadas no navegador; não há upload, conta, banco de dados nem persistência do lote após atualizar a página.

Recursos essenciais: orientação automática para dois logos, padrão de geometria da versão nativa, nove posições, movimento livre proporcional entre fotos, tamanho, opacidade, margem, zoom/pan, original sem marca e download individual/ZIP nas dimensões originais. Todos os ajustes da assinatura são globais para o lote. Zoom e pan são apenas de visualização.

Preservar os aplicativos nativos V3, V4 e V5 e seu código. A implementação web ocupa apenas `web/` no GitHub. Fonte de identidade: fundo, marca e logos fornecidos pelo usuário na versão V5. A exportação web reencoda a imagem e não preserva os metadados do arquivo nativo.
