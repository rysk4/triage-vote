# Triage Vote — DEV LOG

## 2026-04-09 — Init

### Co to je
Jednoduchá hlasovaci webappka pro vyber navrhů. Uzivatele prochazeji obrazky a kazdy ma 3 pozitivni a 3 negativni hlasy. Vysledky se zobrazuji jako zebricek.

### Tech stack
- **Frontend:** Single HTML file (vanilla JS + CSS), mobile-first
- **Backend:** Supabase (projekt `opravime`, tabulka `triage_votes`)
- **Hosting:** GitHub Pages — https://rysk4.github.io/triage-vote/
- **Repo:** https://github.com/rysk4/triage-vote (public, kvuli Pages)

### Databaze (Supabase — projekt opravime)
- `triage_votes` — hlavni tabulka hlasu (UNIQUE na voter_name + proposal_number)
- `triage_votes_log` — append-only audit log (trigger na INSERT/UPDATE), zaloha

### Prvni sada dat
- 36 obrazku: `merch_munchen-02.jpg` az `merch_munchen-37.jpg` (slozka `zdroje-01/`)
- Navrhy cislovany #1–#36

### Jak to funguje
1. Uzivatel zada jmeno
2. Zobrazi se pravidla (3x like, 3x dislike)
3. Prochazi navrhy, hlasuje +/- nebo preskoci
4. Na konci odesle hlasy (UPSERT — bezpecne, zadne mazani)
5. Zobrazi se vysledky ze vsech hlasujicich

### Klicova rozhodnuti
- UPSERT misto delete+insert — bezpecnejsi, zadna ztrata dat
- Audit log tabulka s triggerem — paralelni zaloha kazdeho hlasu
- Supabase anon key v klientu — OK pro tento use case (RLS policies)
- GitHub Pages vyzadoval public repo
- Klavesova navigace (sipky) pro desktop

### Stav hlasovani (snapshot 2026-04-09)
- 3 hlasujici: Matyas, ondrej, Janek
- 13 hlasu celkem
- Vede navrh #16 (+2)

## 2026-04-17 — Multi-round + upload/delete + vyhodnoceni grid

### Co je nove
- **Homepage** prepracovana: round-picker + 3 buttony (Hlasovat / Vyhodnotit / Nove hlasovani)
- **Vyhodnotit** — nova obrazovka s grid galerii:
  - Obrazky serazene dle score, s cervenym boxem (+score, pos/neg) pres obrazek
  - Top 3 maji medaile 🥇🥈🥉, #1 oznacen jako "VITEZ"
  - Toggle "Zobrazit i navrhy bez hlasu"
  - Toggle "Upravovat" → zobrazi delete button + add card
- **Nove hlasovani** — drag-and-drop upload 2–100 obrazků, nazev + max pos/neg, vytvori kolo

### Schema zmeny (migrace: `triage_vote_rounds_and_proposals`)
- `triage_rounds (id uuid, slug, name, max_pos, max_neg, created_at)` — kola
- `triage_proposals (id uuid, round_id, proposal_number, image_url, storage_path, UNIQUE(round_id, proposal_number))`
- `triage_votes` rozsirene o `round_id uuid NOT NULL`
- Stary UNIQUE `(voter_name, proposal_number)` → `(voter_name, round_id, proposal_number)`
- Check proposal_number rozsiren na 1..999
- Default kolo `merch-munchen-01` nasazeno, 36 puvodnich proposals + 35 starych hlasu backfillnuty

### Supabase Storage
- Bucket `triage-images` (public, 10 MB limit, jpg/png/webp/gif)
- Path pattern: `{round_slug}/{uuid}.{ext}`
- RLS policies: public read, anon insert, anon delete

### Security / XSS
- Prechod z innerHTML+template literals na `document.createElement` + `textContent` (security hook vzneseny)
- Zbytek innerHTML pouziva `esc()` helper nebo predpripravene bezpecne hodnoty

### Behavior notes
- Voter hlasy jsou per-round nezavisle (stejne jmeno muze hlasovat v ruznych kolech)
- Delete proposalu smaze i vsechny jeho hlasy v danem kole
- Rollback pri selhani create-round: smaze rozepsane kolo + uploadovane files

## 2026-04-17 (pozdeji) — Admin gate + public per-round URL + delete round

### Co je nove
- **Admin** je na `/` pod heslem (SHA-256 hash v `ADMIN_PASSWORD_SHA256`, session storage flag)
  - Default heslo: `napajedla-triage-2026` (zmena: `printf '%s' 'NOVE' | shasum -a 256`)
  - Odhlaseni pres badge vpravo nahore
- **Public kolo** ma vlastni odkaz `/#slug` (hashchange → reload)
  - Otevre se minimalisticky `#publicHome` screen s 2 buttony (Hlasovat / Vyhodnotit)
  - Bez admin pickru, bez new-round, bez delete
  - Back buttony v dalsich screens redirectuji na `publicHome` (prepisovany `data-back`)
- **Smazat kolo** — button vedle share linku v admin home
  - Confirm dialog ukazuje pocet navrhů + pocet hlasů
  - DB delete cascade (triage_rounds → proposals → votes) + Promise.allSettled storage cleanup
- **Sdilet odkaz** — navigator.clipboard.writeText s fallback na prompt()
- **Po vytvoreni kola** se odkaz automaticky kopiruje + toast notifikace

### Security poznamka
- Password gate je klient-only (je to prototyp) — kdokoli s F12 muze bypassnout
- RLS policies v Supabase jsou otevrene pro anon → admin gate neni bezpecnost, jen UX
- Pokud se to casem zacne zneuzivat: nasadit edge function + signed JWT

## 2026-04-17 (pozdeji II) — Zamknout kolo + name input screen

### Co je nove
- **Zamknout/odemknout kolo** — novy button `🔒 Zamknout` / `🔓 Odemknout` v admin home
  - Column `triage_rounds.locked BOOLEAN NOT NULL DEFAULT false`
  - DB trigger `triage_votes_lock_guard` BEFORE INSERT/UPDATE — vyhodi `P0001` chybu pokud je kolo zamcene (bezpecnost na urovni DB, ne jen klient)
  - Public i admin home ukazou banner `🔒 Hlasovani bylo uzavreno` + disabled Hlasovat button
  - `Vyhodnotit` button funguje stejne (lze se podivat na vysledky)
- **Name input screen** — nahrazeni `prompt()` za hezky `#nameScreen` ve stejnem stylu jako zbytek UI
  - Input + Pokracovat button, Enter submit, predvyplneno z sessionStorage
  - Back button → predchozi screen (home nebo publicHome dle mode)
  - Pred tim user videl nativni browser prompt, ted vlastni UI

### Files
- Migrace: `triage_vote_lock_rounds`
- JS: startVoting refactor do 2 kroku (nameScreen → submitNameAndStart)

## 2026-04-17 (pozdeji III) — Polish: locked routing, RLS fix, diakritika

### Locked public → rovnou evaluate (commit cc904b3)
- Zamcene kolo otevrene pres `/slug` preskoci publicHome a pristane rovnou na evaluate gridu
- Banner `🔒 Hlasovani bylo uzavreno — Toto je finalni vyhodnoceni` nahore
- Back button skryty (neni kam), edit-mode toggle skryty v public mode

### RLS UPDATE policy pro rounds (fix 95245bc)
- Pri prvnim pokusu zamknout kolo PATCH tise selhal (HTTP 200, ale 0 rows affected)
- Priciny: chybela `UPDATE` policy na `triage_rounds` (mel jsem jen SELECT/INSERT/DELETE)
- Migrace: `triage_rounds_update_policy` pridala `CREATE POLICY "rounds update" FOR UPDATE USING (true) WITH CHECK (true)`
- Klient ted detekuje prazdnou odpoved (`res.length === 0`) a vyhodi chybu → tise nenapadne PATCH uz neproleze

### Diakritika sweep (commit b4c56b3)
- Python skript (batch replace) ~95 oprav napric celou appkou
- Home, public home, rules, voting, results, evaluate, new-round, login, name, toasts
- Poznamka do pristich sezeni: psat CZ text s diakritikou od zacatku (feedback memory)

## 2026-04-17 (pozdeji IV) — Migrace na Vercel + clean path URLs

### Hosting migrace GH Pages → Vercel
- Projekt nasazen jako `triage_vote` v Vercel org `sixwave` (fra1 region)
- Custom domena: **https://triage.sixwave.net**
- Wildcard DNS `*.sixwave.net CNAME cname.vercel-dns.com` (DNS-only, Cloudflare) → stacil `vercel domains add`
- `vercel.json` s `regions: ["fra1"]` (konvence sixwave projektu)
- GitHub Pages stale bezi paralelne na `rysk4.github.io/triage-vote` (backup, sdili Supabase)

### Clean path URLs (commit a29e7fa)
- `vercel.json` rewrite `/:slug([a-z0-9][a-z0-9-]*)` → `/index.html` (SPA fallback)
- JS: `detectSlug()` cte nejdriv `location.pathname`, fallback na `location.hash`
- `shareLinkFor()` generuje `https://triage.sixwave.net/slug` (bez `#`)
- Stare hash-linky (`/#slug`) dal funguji — zpetna kompatibilita
- `popstate` listener → reload pri browser back/forward (mode se muze zmenit)

### Aktualni URL struktura
- `/` — admin (heslo `napajedla-triage-2026`)
- `/<slug>` — public single-round (Hlasovat / Vyhodnotit, nebo rovnou Vyhodnotit pokud locked)
- `/#<slug>` — legacy, stale funguje

## 2026-04-18 — Klient-side komprese obrázků pred uploadem

### Proc
Supabase bucket `triage-images` ma limit 10 MB; telefonni fotky casto 8–30 MB padaji pri uploadu. Zaroven zbytecne bobtna storage i load pro hlasujici.

### Implementace (`compressImage()` v `index.html`)
- `createImageBitmap(file)` → canvas resize na max **2048 px** delsi strana → `canvas.toBlob('image/jpeg', 0.82)`
- Vraci novy `File` s priponou `.jpg`; puvodni `name` stem zachovan
- **Skip** pro `image/gif` (animace) a `image/svg+xml` (vektor)
- **Fallback**: pokud `createImageBitmap` selze (HEIC v Chrome), nahraje original a logne warning
- **No-op**: pokud komprimovany blob ≥ original, vrati original

### Napojeni
- Upload pri zakladani kola (uvnitr `createRoundBtn` handler): status `Komprimuji X/Y...` → `Nahravam X/Y...`
- Eval "Pridat obrazky" (`evalAddInput` change handler): stejny pattern
- 10 MB+ fotka se v prohlizeci dekoduje OK, po kompresi typicky **200–800 KB**
