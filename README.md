# AWS Security Launch Tracker 2026

Static site with every AWS security, identity, governance and compliance launch of 2026, week by week, in EN, PT and ES.

## Layout

| Path | Contents |
|---|---|
| `data/launches.json` | All launches (source of truth) |
| `data/weeks/wNN.json` | One file per week, merged into `launches.json` |
| `data/cfps.json` | Call for papers tab: security and cloud CFPs (Brazil, LATAM, global), refreshed by the CFP scan |
| `src/` | Page template (head, top, W40 deep dive, script, Call for papers tab) |
| `i18n/` | Page strings in EN, PT, ES (`cfp.json` for the Call for papers tab) |
| `scripts/add_week.py` | Validates and merges a week file |
| `scripts/build.py` | Builds `dist/index.html` (full page) and `dist/artifact.html` |
| `scripts/deploy.sh` | Merge + build + deploy (GitHub, Amplify or S3) |
| `.github/workflows/pages.yml` | Builds and publishes to GitHub Pages on push |

## GitHub Pages (current hosting)

One-time setup:

1. Push this folder to a GitHub repository (branch `main`).
2. In the repository: Settings > Pages > Build and deployment > Source: **GitHub Actions**.
3. The workflow `.github/workflows/pages.yml` builds `dist/index.html` and publishes it on every push that changes `data/`, `src/`, `i18n/` or `scripts/`. It can also be run by hand from the Actions tab.

Weekly routine:

```bash
# 1. save the week file as data/weeks/w42.json
# 2. merge, build locally, commit and push
TARGET=github ./scripts/deploy.sh data/weeks/w42.json
```

Or, without a terminal: upload `data/weeks/w42.json` through the GitHub web UI. The workflow merges every file in `data/weeks/` (already-present links are skipped), so the site updates even if `launches.json` was not changed locally.

## Weekly update (other targets)

1. Create `data/weeks/wNN.json` with one object per launch:

```json
{"d": "2026-10-08", "t": "Official title", "u": "https://aws.amazon.com/about-aws/whats-new/...",
 "p": "threat|identity|posture|network|data|ai", "s": "GuardDuty", "x": "One line from the official text."}
```

2. Run one of:

```bash
./scripts/deploy.sh data/weeks/w42.json                         # merge + build, no deploy

TARGET=amplify AMPLIFY_APP_ID=d123abc AMPLIFY_BRANCH=main \
  ./scripts/deploy.sh data/weeks/w42.json                       # Amplify manual deployment

TARGET=s3 S3_BUCKET=my-bucket CF_DISTRIBUTION_ID=E123ABC \
  ./scripts/deploy.sh data/weeks/w42.json                       # S3 + CloudFront
```

The week number, the "Updated" date and the source date range are computed from the data. `add_week.py` skips URLs already present, so a re-run does not duplicate entries.

## Checks done by `add_week.py`

- All six fields present; pillar is one of the six keys.
- URL starts with `https://aws.amazon.com/`.
- No en or em dashes in title or summary.
- Date falls in ISO year 2026; the week is computed from the date.

## Amplify prerequisites (one time)

- An Amplify app with a branch created for manual deployments (no Git connection).
- AWS CLI v2 with credentials allowed to call `amplify:CreateDeployment` and `amplify:StartDeployment` on that app.

The W40 deep dive section stays fixed; new weeks show up in the explorer, chart and summaries.
