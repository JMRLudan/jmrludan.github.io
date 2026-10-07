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

DNS for `jmrludan.com`, `joshludan.com` and `raccoon.baby` is managed on Cloudflare (registrar stays Squarespace; only the nameservers point at Cloudflare). `tools/cloudflare_dns.py` is the source of truth for the records and is safe to re-run:

```
export CLOUDFLARE_API_TOKEN=...     # or set it in the Claude Code environment settings
python3 tools/cloudflare_dns.py --check      # show current records
python3 tools/cloudflare_dns.py --dry-run    # show what would change
python3 tools/cloudflare_dns.py              # apply
```

What it enforces:

- `jmrludan.com`: GitHub Pages `A`/`AAAA` records on the apex and `www` CNAME to `jmrludan.github.io`, all DNS-only (grey cloud) so GitHub issues the HTTPS certificate itself. `CNAME` in this repo tells Pages the domain.
- `joshludan.com` and `raccoon.baby`: a proxied placeholder record plus a Cloudflare redirect rule that 301s every URL to the same path on `https://jmrludan.com`.
- It never touches MX, TXT or other email-related records.

The token needs `Zone > Zone > Read`, `Zone > DNS > Edit` and `Zone > Dynamic Redirect > Edit` on those three zones.

After the records are in place, enable **Enforce HTTPS** in the repo's Pages settings once GitHub shows the certificate as issued.
