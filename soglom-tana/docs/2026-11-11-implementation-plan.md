# Sog'lom Tana — implementation plan

Date: 2026-11-11 · Status: awaiting approval · Based on: [design spec](./2026-11-11-design.md)

## How each phase runs

1. At the start of the phase I break it into small tasks, tests first where
   the code is logic (health engine, AI wrapper, rating rules).
2. One small commit per completed step, all inside `soglom-tana/`.
3. Before calling the phase done: `pnpm typecheck`, `pnpm lint`, `pnpm test`,
   plus the phase's own checks below. I show you the output.
4. I push, write a short summary (what was done, what I chose where the brief
   was ambiguous, what is left), and stop for your go-ahead on the next phase.

I ask before adding any paid service and before any destructive database change.

## Phase 1 — Foundation

- Scaffold Next.js 16 + TypeScript strict in `soglom-tana/`; pnpm, ESLint,
  Prettier, Vitest, Playwright config; `.env.example`; env validation with Zod.
- Tailwind 4, shadcn/ui base components, light/dark theme.
- next-intl with `messages/uz.json` and `messages/ru.json`, language switcher.
- Supabase clients (server, browser, admin), `proxy.ts` session refresh, CSP
  and security headers.
- Auth: email + password, Google, callback route, sign-out, protected routes.
- Migrations: full schema from the spec, RLS policies, `is_admin()`, indexes,
  `pg_trgm`, storage buckets and policies. Generated types.
- App shell: bottom tab bar on mobile (Bosh sahifa, Ovqat, Mashq, Natija,
  Murabbiy), side navigation on desktop, placeholder pages.
- GitHub Actions workflow: typecheck, lint, unit tests, database tests.

**Checks:** migrations apply cleanly to a fresh local Postgres; RLS SQL tests
pass (user A cannot touch user B; non-admin cannot write the catalog); app
builds; login page renders in uz and ru.

## Phase 2 — Health engine and onboarding

- `lib/health`: bmr, tdee, bmi, calorieTarget, macros, timeline, ageGate,
  shouldRecalculate, exerciseKcal, stepsKcal — written test-first.
- Onboarding flow (React Hook Form + Zod), 5 activity levels with Uzbek
  descriptions, under-18 screen, BMI < 18.5 path.
- Summary screen with the explanation and any `adjustments` in plain words.
- Saves `profiles` and the first `goals` version. Profile settings and
  "recalculate plan".

**Checks:** unit tests cover floors (1500 / 1200), the 25% and 1%-per-week
caps, BMI < 18.5, age 17 / 18 boundary, very high BMI adjusted weight.

## Phase 3 — Food logging (manual)

- Seed: about 150 foods with portions, uz/ru names, aliases, `source: 'estimate'`.
- Search RPC (trigram), food detail with portion picker.
- Dashboard: calorie ring, macro bars, meals by type, water, steps and
  exercise placeholders wired to real totals.
- Add, edit and delete log entries with optimistic updates; nutrition snapshot
  stored on the log.
- Favorites, recents, repeat yesterday's meal, custom foods, recipes.
- Water tracker.

**Checks:** search finds "plov", "osh" and "palov" as the same dish; editing a
catalog food does not change an existing log; seed contains no pork or alcohol.

## Phase 4 — AI food

- `lib/ai/client.ts` wrapper: kill-switch, limits, cache, timeout, retries,
  Zod validation, clamps, `ai_requests` logging.
- Rate limiter interface with Upstash and Postgres implementations.
- `parseFoodText` with versioned prompt and Uzbek few-shots; catalog matching.
- `recognizeFoodPhoto`: client-side compression, server-side type and size
  validation, upload to the private bucket.
- Editable draft sheet shared by text and photo; confidence shown per item.
- Friendly messages for limit reached, AI off and AI failure; manual entry
  always available.

**Checks:** unit tests with a fake Gemini client for retry, timeout, invalid
JSON, cache hit (second identical input makes no API call), limit exceeded,
kill-switch; an injection fixture ("ignore the rules…" inside the text) still
yields only schema-valid, clamped items. A live call to Gemini needs your
`GEMINI_API_KEY`; without it I verify against the fake client only and say so.

## Phase 5 — Recommendations

- `rateFood` rules with tests; label, reason and swap on catalog and logged
  foods; uz/ru copy that never shames.
- "Nima yesam bo'ladi?": rule-based picker of 3 meals for the remaining kcal
  and macros, AI sentence with template fallback.

**Checks:** rating tests for representative foods (chicken breast 🟢, osh 🟡,
sweet soda 🔴); suggestions never exceed the remaining calories.

## Phase 6 — Workouts

- Seed: exercise catalog with MET, muscle groups, difficulty, Uzbek
  instructions; three ready plans with weekly progression rules.
- Start a plan, log sets × reps × weight or cardio duration, MET calories.
- Rest timer, history, streaks, progressive overload suggestion from the
  previous session.
- Manual steps via `StepSource`; steps and exercise feed the dashboard.

**Checks:** unit tests for streak calculation, overload suggestion and kcal.

## Phase 7 — Progress

- Weight log, chart with 7-day moving average and a note on daily fluctuation;
  automatic target recalculation on a ≥ 2 kg change (new `goals` version).
- Measurements with charts; private progress photos with signed URLs.
- Weekly summary: numbers in code, AI encouragement and tip.

**Checks:** moving-average and weekly-aggregate unit tests; a photo URL from
one user is not readable by another (storage policy test).

## Phase 8 — AI coach

- Coach prompt, context builder (profile, targets, 7-day summary), streaming
  route, persisted threads, rolling summary of old messages.
- `lib/ai/safety.ts`: disordered-eating screen, medical-symptom screen,
  below-floor check on replies. Disclaimer in the UI.

**Checks:** unit tests for the screens in Uzbek and Russian; care mode returns
no numbers; context stays under a fixed token budget.

## Phase 9 — PWA, admin, data rights, hardening

- Manifest, icons, Serwist service worker with offline shell, install prompt.
- Web Push reminders (meal, water, workout), settings UI, cron route.
- Admin: food catalog CRUD, AI usage and cost by day, users and DAU.
- Export (JSON and CSV) and full account deletion.
- Sentry; performance pass (lazy charts, image optimization, bundle check,
  Lighthouse mobile target 90+); accessibility pass (keyboard, contrast, labels).
- Playwright e2e: onboarding → log food by text → dashboard updates.
- README: setup, env vars, Supabase setup, seeding, Vercel deploy.

**Checks:** Lighthouse run on the production build; e2e in GitHub Actions;
deletion leaves no rows or storage objects for the user.

## What I need from you, and when

| When | What |
|---|---|
| Now | Approval of the spec and this plan, or changes |
| Phase 1, to try the app yourself | A Supabase project (URL, anon key, service-role key) and Google OAuth credentials, set in your own `.env.local` and Vercel — never sent in chat |
| Phase 4 | A Gemini API key, set the same way |
| Phase 9 | Optional: Sentry DSN, Upstash credentials, VAPID keys |
