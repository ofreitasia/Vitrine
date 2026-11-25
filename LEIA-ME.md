# Vitrine de achados (link da bio)

Uma página no estilo do perfil (violeta escuro). Cada cartão tem a foto, o nome, o vídeo de origem, uma descrição e o preço. Um toque leva direto ao produto pelo seu link de afiliado.

## Arquivos
- `index.html`: a página.
- `produtos.json`: os produtos e os textos do topo (selo, título, linha). É o arquivo que vale.
- `produtos.js`: gerado automaticamente a partir do .json. Não edite.
- `img/`: as fotos, quadradas, em 800 px. Ficam guardadas aqui, então não somem se a loja trocar a foto.
- `adicionar.py`: coloca, edita e tira produtos.

## Colocar um produto
```
python adicionar.py "LINK-DE-AFILIADO" --categoria "Setup" --video "Nome do vídeo"
```
O script segue o link curto até a página do produto e pega sozinho a foto, o nome, a descrição e o preço.
Algumas lojas, principalmente a Shopee, não mostram esses dados para programas. Nesse caso, complete à mão:
`--nome "..." --preco "R$ 89,90" --imagem foto.jpg`

Outros comandos:
- `python adicionar.py --listar`
- `python adicionar.py --editar luminaria-vi --link "NOVO-LINK" --preco "R$ 79,90"`
- `python adicionar.py --remover luminaria-vi`: só desativa. Para voltar, use `--editar luminaria-vi --ativo sim`.

Campos opcionais: `--etiqueta "NO VÍDEO"` (selo rosa na foto), `--destaque` (vai para o topo), `--loja "SHOPEE"`.

Também dá para só mandar o link no chat que o Claude coloca na vitrine.

## Ver no computador
Abra o `index.html` no navegador.

## Aviso
O rodapé tem o aviso de #publi e de link de afiliado, que o CONAR exige.
