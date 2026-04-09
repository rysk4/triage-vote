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
