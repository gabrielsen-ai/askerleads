# Supabase Setup Guide

## 1. Sett opp Supabase-prosjekt

1. Gå til [supabase.com](https://supabase.com) og logg inn
2. Opprett et nytt prosjekt
3. Kopier **Project URL** og **anon public key** fra Project Settings → API

## 2. Kjør SQL i Supabase

1. Gå til SQL Editor i Supabase
2. Lim inn SQL-koden (den jeg ga deg tidligere) og kjør den
3. Dette oppretter `leads`-tabellen med alle nødvendige felter

## 3. Legg til Supabase-keys i .env

Åpne `.env` og legg til (hvis du ikke har gjort det allerede):

```env
# Frontend (React/Vite)
VITE_SUPABASE_URL=https://ditt-prosjekt.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend (Python-skript) - trengs kun for import
SUPABASE_URL=https://ditt-prosjekt.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

> ⚠️ **Service Role Key** finner du under Project Settings → API → service_role. Hold denne hemmelig!

## 4. Installer Python-pakke for import

```bash
pip install supabase
```

## 5. Importer eksisterende leads til Supabase

```bash
python import_to_supabase.py
```

Dette importerer alle leads fra `public/leads.json` og `public/leads-baerum.json` til Supabase.

## 6. Restart dev-serveren

```bash
npm run dev
```

## 7. Test at det fungerer

- Åpne appen i nettleseren
- Leads skal nå lastes fra Supabase
- Trykk "Godta" eller "Avslå" på et lead
- Refresh siden - statusen skal være lagret!

## Hva er endret?

### Nye filer:
- `src/lib/supabaseClient.ts` - Supabase-klient
- `import_to_supabase.py` - Importskript

### Oppdaterte filer:
- `src/types/Lead.ts` - La til status-felter
- `src/hooks/useLeads.ts` - Henter nå fra Supabase
- `src/components/dashboard/Dashboard.tsx` - Oppdaterer status i Supabase
- `requirements.txt` - La til `supabase`-pakke

## Troubleshooting

### "Mangler Supabase-miljøvariabler"
- Sjekk at `.env` har `VITE_SUPABASE_URL` og `VITE_SUPABASE_ANON_KEY`
- Restart dev-serveren etter endringer i `.env`

### "Row Level Security (RLS) blokkerer spørringen"
I Supabase, gå til Authentication → Policies, og lag policies for `leads`-tabellen:

**Enable RLS** først, deretter:

```sql
-- Tillat alle å lese leads
create policy "Allow public read access"
on public.leads for select
to anon
using (true);

-- Tillat alle å oppdatere leads
create policy "Allow public update access"
on public.leads for update
to anon
using (true);
```

### Leads vises ikke
- Sjekk at du har kjørt `import_to_supabase.py`
- Åpne Supabase Table Editor og se om `leads`-tabellen har data
- Sjekk console i nettleseren for feilmeldinger
