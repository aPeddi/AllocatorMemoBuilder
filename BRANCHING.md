# Branching & release model

A right-sized Git model for AllocatorMemoBuilder: enough structure to keep
`main` always-demoable and give a clean history to walk during review, without
the ceremony a large team needs. It runs entirely locally — no CI gate, no
deploy hooks — so the rules are the discipline, and `./amb` encodes them.

## The branches

| Branch         | Role                                                        | Moves when                          |
|----------------|-------------------------------------------------------------|-------------------------------------|
| **`main`**     | Always green, always demoable. The commit you'd show Equi.  | a release or a hotfix merges in     |
| **`develop`**  | Integration line. Where features come together.             | a feature merges in                 |
| **`feature/*`**| One change in progress. Short-lived.                        | you're building something           |
| **`release/vX.Y`** | Freeze a cut of `develop`, stabilize, then promote.     | you're cutting a version            |
| **`hotfix/*`** | Urgent fix branched from `main`, merged back to both.       | `main` is broken and can't wait     |

```
feature/*  ─┐
feature/*  ─┼─▶  develop  ─▶  release/vX.Y  ─▶  main   (tag vX.Y)
feature/*  ─┘                                    ▲
                              hotfix/*  ──────────┘  (then back-merge to develop)
```

Nothing lands on `main` except a **release merge** or a **hotfix**. Day-to-day
work never commits to `main` directly.

## Why this shape

- **`main` stays clean** so there is always one commit that builds and demos —
  the single most valuable thing to have during a review.
- **`develop` absorbs churn.** Rapid iteration integrates here; if it briefly
  breaks, the demo line is untouched.
- **Releases are deliberate.** Cutting `release/vX.Y` is the moment you stop
  adding and start hardening — version bump, changelog, final test pass.
- **Rollback is a tag away.** Every release is tagged `vX.Y`; recovering a
  known-good state is `git checkout vX.Y`, and auditing a regression is
  `git diff vX.Y..HEAD`.

## Naming

- `feature/<slug>` — e.g. `feature/metrics-engine`, `feature/audit-trail`
- `release/vX.Y`   — e.g. `release/v0.1`
- `hotfix/<slug>`  — e.g. `hotfix/sharpe-annualization`

Slugs are lowercase, hyphenated, and describe the change, not the file.

## Commit messages — Conventional Commits

```
<type>(<scope>): <subject>

feat(metrics):   add Sortino with configurable MAR
fix(ingest):     handle European decimal commas in returns
docs(adr):       record deterministic-retrieval decision
test(metrics):   golden values for Sharpe/Calmar
chore(cli):      add ./amb lint target
refactor(memo):  split claim assembly from rendering
```

Types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `perf`, `build`.
This keeps history greppable and makes a changelog derivable at release time.

## Merge policy

- **`feature/*` → `develop`:** squash-merge. One feature becomes one tidy commit
  on the integration line. Delete the branch after.
- **`release/*` → `main`:** merge commit (no squash) so the release is a visible
  join, then tag it. Back-merge `main` → `develop` so tags/hotfixes propagate.
- **`hotfix/*`:** merge to `main` (tag a patch), then merge to `develop`.

Solo take-home reality: PRs are optional and self-reviewed, but keep the *branch
discipline* — it's what produces a history worth reading. Open a PR when you want
GitHub's diff view to review a chunk of work against `develop`.

## Versioning

`vMAJOR.MINOR` while pre-1.0 (`v0.1`, `v0.2`, …). Tag on the release merge to
`main`. Bump MINOR for new capability, MAJOR at the first "this is the product"
cut. Patch tags (`v0.1.1`) come from hotfixes.

## Working the flow (plain git)

```
git checkout develop && git pull
git checkout -b feature/audit-trail          # start a feature
# …commit… then squash back:
git checkout develop && git merge --squash feature/audit-trail

git checkout -b release/v0.3 develop         # cut a release
git checkout main && git merge release/v0.3 && git tag v0.3
```

`./amb` stays focused on building the memo; branching is plain git.

## Authorship

Commits are authored as `Avinash Peddi <avinashpeddi7@gmail.com>` (already set
locally: `git config user.email`). This matches existing history and the
`aPeddi` GitHub account. Everything is local — there is no deploy-time email
authorization to worry about — so this is purely about a consistent, honest
contribution graph.

## Housekeeping

- Delete `feature/*` once merged. Keep only what's in flight.
- No `backup/*` walls of branches — the rollback guarantee lives in **tags**,
  not in stale branches.
- `Inspo.md` is the private brainstorm and is git-ignored; the tracked spec is
  `docs/SPEC.md`, and the reasoning behind big calls is in `docs/decisions/`.
