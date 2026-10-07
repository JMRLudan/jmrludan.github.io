# jmrludan.com

Source for [jmrludan.com](https://jmrludan.com), hosted on GitHub Pages from the `main` branch of this repo. Plain static HTML, no build step: edit a file, commit, push, and the site updates within a minute or two.

## Layout

| Path | What it is |
| --- | --- |
| `index.html` | Home: bio and experience |
| `highlights/index.html` | Publications and class projects |
| `resume/index.html` | Embeds `assets/pdf/Josh-Ludan-Resume.pdf` |
| `demos/index.html` | Demos, vibelets and the Claude Code Corner hub (formerly the root of jmrludan.github.io) |
| `dice-reader.html`, `dice*Model*/` | In-browser D&D dice reader demo and its TensorFlow.js models |
| `vibelets/` | Built React vibelets (crochet-pattern, poemscroll, embedscroller) |
| `assets/site.css` | Shared stylesheet for the main pages |
| `assets/img/` | Photo, owl logo, paper figures |
| `assets/pdf/` | Resume and project reports |
| `404.html` | Custom not-found page |
| `CNAME` | Tells GitHub Pages the custom domain (`jmrludan.com`) |

## Common edits

- **Update the resume:** replace `assets/pdf/Josh-Ludan-Resume.pdf` and bump the label in `resume/index.html`.
- **Add a publication or project:** copy one of the `<article class="pub">` or `<article class="project">` blocks in `highlights/index.html`.
- **Add a demo:** drop its files in the repo and add a card in `demos/index.html`.

## Domain / DNS

`CNAME` points GitHub Pages at the apex domain. DNS for `jmrludan.com` must have:

- `A` records on the apex for `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- `AAAA` records on the apex for `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153` (optional but recommended)
- `CNAME` on `www` pointing to `jmrludan.github.io`

GitHub then serves both `jmrludan.com` and `www.jmrludan.com` (the latter redirects to the apex). Enable **Enforce HTTPS** in the repo's Pages settings once the certificate has been issued.
