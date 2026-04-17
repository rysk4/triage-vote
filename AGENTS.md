# Triage Vote — AGENTS.md

Jednoduchá hlasovací webappka pro výběr návrhů z obrázků. Kola + hlasy + medaile.

## TL;DR

- **Frontend:** single `index.html` (vanilla JS + CSS, ~1600 řádků, mobile-first)
- **Backend:** Supabase projekt **`opravime`** (`kwkqqwpipsfzweopipoa`)
- **Hosting primární:** Vercel org `sixwave` (fra1), projekt `triage_vote` → **https://triage.sixwave.net**
- **Hosting záloha:** GitHub Pages → https://rysk4.github.io/triage-vote/
- **Repo:** https://github.com/rysk4/triage-vote (public)

## URL routing

| URL                           | Mode    | Co se stane                                                |
| ----------------------------- | ------- | ---------------------------------------------------------- |
| `/`                           | admin   | Password gate → round picker + správa kol                  |
| `/<slug>`                     | public  | Single-round landing (Hlasovat / Vyhodnotit)               |
| `/<slug>` kde locked          | public  | Rovnou evaluate grid + banner `🔒 Hlasování uzavřeno`     |
| `/#<slug>`                    | public  | Legacy hash fallback (stále funguje)                       |

Rewrite je v `vercel.json`: `/:slug([a-z0-9][a-z0-9-]*)` → `/index.html`. JS pak čte `location.pathname` přes `detectSlug()`.

## Admin heslo

- Default plaintext: **`napajedla-triage-2026`**
- SHA-256 hash je v `ADMIN_PASSWORD_SHA256` konstantě v `index.html`
- Změna: `printf '%s' 'NOVE_HESLO' | shasum -a 256` → paste do kódu
- Session flag v `sessionStorage['triage_admin_ok']`
- Je to jen UX gate — RLS v Supabase je otevřené pro anon, takže F12 to obejde

## Databáze (Supabase `opravime`)

| Tabulka                | Co                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------ |
| `triage_rounds`        | kola (id uuid, slug UNIQUE, name, max_pos, max_neg, `locked` bool, created_at)       |
| `triage_proposals`     | obrázky v kole (round_id, proposal_number, image_url, storage_path)                  |
| `triage_votes`         | hlasy (voter_name, round_id, proposal_number, vote ∈ {-1,1}; UNIQUE na trojici)     |
| `triage_votes_log`     | append-only audit log (trigger na INSERT/UPDATE)                                    |

**RLS policies:** open pro anon (SELECT/INSERT/UPDATE/DELETE). Prototyp, ne production-grade.

**Triggery:**
- `trg_log_vote` — kopíruje insert/update do `triage_votes_log`
- `triage_votes_lock_guard` — BEFORE INSERT/UPDATE, vyhodí `P0001` pokud je kolo locked

**Storage bucket:** `triage-images` (public, 10 MB limit, jpg/png/webp/gif), path pattern `{slug}/{uuid}.{ext}`.

## Deploy

```bash
# Lokální dev: prostě otevři index.html v prohlížeči (ale Supabase fetch vyžaduje HTTP)
python3 -m http.server 8080

# Production
vercel --prod --yes

# Kontrola
curl -sI https://triage.sixwave.net/
```

GitHub Pages deploy je automatický při pushi do `main` (backup).

## Konvence pro editaci

1. **Diakritika:** všechny uživatelské texty v češtině **s diakritikou**. Žádné "pristup" / "prihlasit" / "vysledky" (viz 2026-04-17 sweep).
2. **XSS:** `innerHTML` je v kódu minimálně, kdekoli s uživatelským vstupem použij `esc()` helper nebo `createElement` + `textContent`.
3. **Supabase REST:** všechny volání přes `sbRest()` helper. Pro INSERT bulk posílej pole objektů; pro upsert přidej `Prefer: resolution=merge-duplicates`.
4. **Tiché PATCH fail:** vždy po UPDATE/PATCH ověřit `Array.isArray(res) && res.length > 0`, jinak je to pravděpodobně missing RLS policy.
5. **Schema změny:** přes Supabase MCP `apply_migration` s `snake_case` názvem. Vždy přidat RLS policy pro všechny CRUD operace, které klient používá.
6. **Nové screens:** přidej do HTML s `class="screen"`, naviguj přes `showScreen(id)`. Back tlačítka používají `data-back="home"` (v public módu se při bootu přepisují na `publicHome`).

## Edge cases / gotchas

- **Locked kolo v public módu** → skip `publicHome`, jdi rovnou na evaluate. Viz `bootPublic()`.
- **Zdroje-01 obrázky** jsou v repu kvůli legacy defaultnímu kolu (`merch-munchen-01`). Nová kola uploadují do Supabase Storage.
- **Wildcard DNS** `*.sixwave.net` na Cloudflare → Vercel (DNS-only, šedý mrak). Nové subdomény stačí `vercel domains add`.
- **Kolo slug** musí být `[a-z0-9][a-z0-9-]*`, jinak rewrite na Vercelu nezabere a přistanete na 404.

## Reference

- Supabase project ID: `kwkqqwpipsfzweopipoa`
- Vercel org: `sixwave`, projekt `triage_vote`
- DNS provider: Cloudflare (sixwave.net zone)
- Kontakt / maintenance: viz `DEV-LOG.md`
