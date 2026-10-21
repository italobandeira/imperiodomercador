# Site do Império do Mercador

Site estático do jogo, em português (raiz), inglês (`en/`) e espanhol (`es/`): apresentação, Política de
Privacidade, Termos de Uso e Contato. HTML e CSS puros, sem framework, sem JavaScript e sem CDN.

## Gerar

As páginas saem de `tools/build_site.py` (Python 3 com Pillow). Os textos ficam em `tools/content_pt.py`,
`content_en.py` e `content_es.py`, com a mesma estrutura: ao mudar um texto, mude os três.

```powershell
python tools/build_site.py              # páginas + arte copiada do jogo
python tools/build_site.py --no-assets  # só as páginas
```

A arte vem do repositório do jogo (`../imperio-do-mercador`, ou a variável `GAME_DIR`):

- sprites e animações de `assets/gfx/` (as animações viram CSS `steps()`, com o tempo de cada quadro do jogo);
- o logo de cada idioma, exportado pelo próprio jogo em fundo transparente (`lovec . --logo <idioma>`; o caminho do
  `lovec.exe` vem da variável `LOVEC`);
- as capturas e a imagem de destaque de `build/store/<idioma>/` (rode antes `node tools/build_store.mjs` no jogo);
  as capturas viram WebP de 540x960.

## Visualizar

```powershell
python -m http.server 4180
```

Abra `http://localhost:4180/`.

## Publicar

O endereço público entra em `canonical`, `hreflang`, `og:url`, `og:image` e no `sitemap.xml`. O padrão é
`https://italobandeira.github.io/imperiodomercador/`; para outro endereço, gere de novo com a variável:

```powershell
$env:SITE_BASE = "https://seu-endereco/"; python tools/build_site.py --no-assets
```

No GitHub Pages: crie um repositório **público** (o Pages gratuito não publica repositórios privados), envie esta
pasta e ative Settings > Pages > Deploy from a branch (`main`, raiz). O `.nojekyll` já está aqui.

Na Play Console, use:

- **Site:** a página inicial (ex.: `https://italobandeira.github.io/imperiodomercador/`);
- **Política de privacidade:** `.../privacy.html` (a Play aceita uma URL; as versões em inglês e espanhol estão
  ligadas no topo de cada página).

## app-ads.txt

O `app-ads.txt` precisa ficar na **raiz do domínio** do site informado na Play Console, não numa subpasta. Com o
site em `italobandeira.github.io/imperiodomercador/`, o arquivo vai em `https://italobandeira.github.io/app-ads.txt`,
ou seja, no repositório `italobandeira.github.io`. Copie as linhas exatas do painel do LevelPlay (Setup >
app-ads.txt) e junte com as dos outros apps que usam o mesmo domínio.

## Estrutura

- `index.html`, `privacy.html`, `terms.html`, `contact.html` (e as mesmas em `en/` e `es/`): geradas, não edite à mão.
- `style.css`: estilo único. Usa as peças 9-slice da interface do jogo (`ui_parchment`, `ui_wood`, `ui_btn_*`) como
  `border-image`, a fonte Jersey 10 do jogo (SIL OFL, em `assets/fonts/`) e a paleta de `art/palette.px.js`.
- `assets/img/`: arte copiada do jogo pelo build.
- `sitemap.xml` e `robots.txt`: gerados com o endereço público.

Com `prefers-reduced-motion`, as animações param e os heróis ficam parados na rua.
