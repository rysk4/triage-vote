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
