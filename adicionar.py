"""adicionar.py — coloca um produto na vitrine a partir do link de afiliado.

Lê a página do produto (segue os redirecionamentos do link curto), pega a foto, o nome, a descrição e o preço
pelas etiquetas da página (og:image, og:title…), baixa a foto para img/ e atualiza produtos.json + produtos.js.

Uso (na pasta vitrine):
  python adicionar.py "<link de afiliado>"                       # tenta reconhecer tudo sozinho
  python adicionar.py "<link>" --nome "Luminária VI" --preco "R$ 89,90" --categoria "Setup" --video "E se o GTA 6 saísse da tela?"
  python adicionar.py "<link>" --imagem foto.jpg                 # quando a loja não deixa ler a foto (ex.: algumas páginas da Shopee)
  python adicionar.py --editar luminaria-vi --preco "R$ 79,90"   # muda um campo de um produto
  python adicionar.py --listar
  python adicionar.py --remover luminaria-vi                     # tira da vitrine (só desativa; volta com --editar ID --ativo sim)
"""
import argparse, html, io, json, os, re, sys, unicodedata, urllib.request, urllib.parse
from html.parser import HTMLParser

try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__))
DB, JS, IMG = os.path.join(HERE, 'produtos.json'), os.path.join(HERE, 'produtos.js'), os.path.join(HERE, 'img')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
LOJAS = {'shopee': 'SHOPEE', 'mercadolivre': 'MERCADO LIVRE', 'mercadolibre': 'MERCADO LIVRE', 'meli.la': 'MERCADO LIVRE', 'amazon': 'AMAZON', 'amzn': 'AMAZON',
         'aliexpress': 'ALIEXPRESS', 'magazineluiza': 'MAGALU', 'magalu': 'MAGALU', 'shein': 'SHEIN', 'temu': 'TEMU', 'kabum': 'KABUM', 'americanas': 'AMERICANAS', 'tiktok': 'TIKTOK SHOP'}


def carregar():
    if os.path.exists(DB): return json.load(open(DB, encoding='utf-8'))
    return {'vitrine': {}, 'produtos': []}


def salvar(d):
    json.dump(d, open(DB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(JS, 'w', encoding='utf-8') as f:   # a página lê este arquivo (funciona até abrindo direto do computador)
        f.write('// gerado por adicionar.py a partir de produtos.json — edite o .json (ou use o script), não este arquivo\n')
        f.write('window.VITRINE = ' + json.dumps(d.get('vitrine', {}), ensure_ascii=False) + ';\n')
        f.write('window.PRODUTOS = ' + json.dumps(d['produtos'], ensure_ascii=False, indent=1) + ';\n')


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:40] or 'produto'


class Meta(HTMLParser):
    def __init__(s): super().__init__(); s.m = {}; s.title = ''; s._t = False
    def handle_starttag(s, tag, a):
        a = dict(a)
        if tag == 'meta':
            k = (a.get('property') or a.get('name') or a.get('itemprop') or '').lower()
            if k and a.get('content') and k not in s.m: s.m[k] = html.unescape(a['content']).strip()
        if tag == 'title': s._t = True
    def handle_endtag(s, tag):
        if tag == 'title': s._t = False
    def handle_data(s, d):
        if s._t: s.title += d


def ler_pagina(link):
    req = urllib.request.Request(link, headers={'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
    with urllib.request.urlopen(req, timeout=25) as r:
        final = r.geturl(); raw = r.read(3_000_000)
    p = Meta(); p.feed(raw.decode('utf-8', 'ignore'))
    m = p.m
    preco = m.get('product:price:amount') or m.get('og:price:amount') or m.get('price')
    if preco:
        try: preco = 'R$ ' + f"{float(preco.replace(',', '.')):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except ValueError: preco = None
    return {'final': final, 'nome': m.get('og:title') or m.get('twitter:title') or p.title.strip(),
            'info': m.get('og:description') or m.get('description') or '', 'imagem': m.get('og:image') or m.get('twitter:image') or m.get('image'), 'preco': preco}


def loja_de(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    return next((v for k, v in LOJAS.items() if k in host), host.replace('www.', '').split('.')[0].upper())


def baixar_foto(src, pid):
    from PIL import Image
    if re.match(r'(https?|file)://', src or ''):
        req = urllib.request.Request(src, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=25) as r: im = Image.open(io.BytesIO(r.read(15_000_000)))
    else:
        im = Image.open(src)
    im = im.convert('RGB'); w, h = im.size; s = min(w, h)   # quadrada, recortada no centro, 800 px
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((800, 800), Image.LANCZOS)
    os.makedirs(IMG, exist_ok=True); out = os.path.join(IMG, pid + '.jpg'); im.save(out, quality=86, optimize=True)
    return 'img/' + pid + '.jpg'


def curto(s, n):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 1].rsplit(' ', 1)[0] + '…'


def main():
    ap = argparse.ArgumentParser(description='Coloca um produto de afiliado na vitrine.')
    ap.add_argument('link', nargs='?')
    for k in ('nome', 'info', 'preco', 'categoria', 'video', 'etiqueta', 'loja', 'imagem', 'id', 'ativo'): ap.add_argument('--' + k)
    ap.add_argument('--destaque', action='store_true'); ap.add_argument('--editar'); ap.add_argument('--remover'); ap.add_argument('--listar', action='store_true')
    a = ap.parse_args(); d = carregar(); P = d['produtos']
    if a.listar:
        for p in P: print(('  ' if p.get('ativo', True) else '× ') + f"{p['id']:<28} {p.get('preco') or '':<12} {p['nome']}  →  {p['link']}")
        return
    if a.remover:
        p = next((p for p in P if p['id'] == a.remover), None)
        if not p: sys.exit(f'não achei {a.remover}')
        p['ativo'] = False; salvar(d); print('desativado:', p['nome']); return
    if a.editar:
        p = next((p for p in P if p['id'] == a.editar), None)
        if not p: sys.exit(f'não achei {a.editar}')
        for k in ('nome', 'info', 'preco', 'categoria', 'video', 'etiqueta', 'loja'):
            if getattr(a, k) is not None: p[k] = getattr(a, k)
        if a.link: p['link'] = a.link
        if a.ativo is not None: p['ativo'] = a.ativo.lower() in ('sim', 's', 'true', '1')
        if a.destaque: p['destaque'] = True
        if a.imagem: p['imagem'] = baixar_foto(a.imagem, p['id'])
        salvar(d); print('atualizado:', p['nome']); return
    if not a.link: ap.print_help(); return

    info = {'final': a.link, 'nome': '', 'info': '', 'imagem': None, 'preco': None}
    try:
        info = ler_pagina(a.link); print('página lida:', info['final'][:90])
    except Exception as e:
        print('⚠ não consegui ler a página da loja:', e)
    nome = a.nome or curto(info['nome'], 70)
    if not nome: sys.exit('⚠ a loja não mostrou o nome: rode de novo com --nome "..." (e --imagem foto.jpg se precisar)')
    pid = a.id or slug(nome)
    if any(p['id'] == pid for p in P): pid += '-' + str(len(P) + 1)
    src = a.imagem or info['imagem']
    if not src: sys.exit('⚠ a loja não mostrou a foto: rode de novo com --imagem <arquivo ou endereço da foto>')
    try: img = baixar_foto(src, pid)
    except Exception as e: sys.exit(f'⚠ não consegui baixar a foto ({e}): use --imagem <arquivo>')
    p = {'id': pid, 'nome': nome, 'info': a.info if a.info is not None else curto(info['info'], 160), 'preco': a.preco or info['preco'] or '',
         'imagem': img, 'link': a.link, 'loja': a.loja or loja_de(info['final']), 'categoria': a.categoria or '', 'video': a.video or '',
         'etiqueta': a.etiqueta or '', 'destaque': bool(a.destaque), 'ativo': True}
    P.insert(0, p); salvar(d)
    print(f"✓ na vitrine: {p['nome']} · {p['preco'] or 'sem preço'} · {p['loja']} · {img}")


if __name__ == '__main__':
    main()
