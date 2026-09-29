---
name: cdt-api-call
description: Mint a short-lived CDT platform JWT locally and fire an authenticated request at a CDT plane API (control plane, data plane serving, compute plane). Use whenever a task needs to call a CDT API that returns 401/403 without a bearer token, or when the user says "call the control plane", "hit the metrics endpoint", "mint a token", "get me a dev token", "why is this 401", "update a metric definition", "seed/patch the metric store", or asks to script anything against a CDT API. Also use before reaching for a browser session or DevTools to harvest a cookie — that is the slow path and this replaces it. Dev by default; refuse staging/prod writes without explicit confirmation.
---

# Call a CDT API with a minted token

The CDT planes authenticate with an RS256 **platform JWT** in an
`Authorization: Bearer` header. The control plane's only issuing route,
`POST /auth/exchange`, trades a Microsoft Entra `id_token` for one — so there is
**no machine-to-machine path**. Do not try to drive an Entra login, and do not
scrape the `__Host-session` cookie out of a browser profile: sign a short-lived
token instead, which is what the platform's own smoke fixtures do.

## The one-liner

```bash
aws sso login --profile cdt-dev          # only if the session has expired
export AWS_PROFILE=cdt-dev
CONTROL_PLANE_TOKEN=$(python scripts/mint_token.py) python <your-script>.py
```

## Environments

Each environment is its own AWS account with its own signing key, so a token only
works against the environment whose profile minted it. Base paths are all
`/api/v1`.

| Env | Profile | Control plane | Data plane |
|---|---|---|---|
| dev | `cdt-dev` | `https://33wtdcbo13.execute-api.eu-west-2.amazonaws.com/dev` | `https://data.dev.digitaltrack.app` |
| staging | `cdt-staging` | `https://r2dd96g6e2.execute-api.eu-west-2.amazonaws.com/staging` | `https://data.staging.digitaltrack.app` |
| prod | `cdt-prod` | `https://2kc4ejqgsk.execute-api.eu-west-2.amazonaws.com/prod` | `https://data.digitaltrack.app` |

One `aws sso login --profile cdt-dev` covers all three profiles. If a URL stops
resolving, list the API with
`aws apigateway get-rest-apis --profile <profile> --region eu-west-2` (the name is
`cdt-control-plane-<env>`) and the data-plane host from `data_plane_host` in
`intech-data-plane/infrastructure/tfvars/<env>.tfvars`.

Staging and prod hold no published tenant data yet, so a serving query there 503s
at the version pin before any request validation runs. Discovery routes such as
`GET /serving/metrics` still work.

`scripts/mint_token.py` (beside this skill) reads four SSM parameters under
`/cdt/cdt-control-plane` — `jwt-private-key` (decrypted), `jwt-key-id`,
`jwt-issuer`, `jwt-audience` — and signs a 15-minute token whose issuer, audience
and `token_use` match what the deployed service validates. Needs `python-jose` and
`boto3`, so run it with a repo venv, not a bare interpreter.

Import it instead when scripting: `from mint_token import mint_token`.

## Rules that keep this safe

**Never print the token.** Not to the terminal, not into a file, not into a
transcript. Use `$(...)` substitution or import the function. `--claims` prints the
decoded claims and a length, which is what you want for "did that work".

**Keep the TTL short.** The default 15 minutes covers a handful of writes. Raising
it needs a reason.

**Dev unless told otherwise.** The script signs with whatever profile is active, so
`AWS_PROFILE` is the blast radius. A staging or prod write needs explicit
confirmation in the same turn.

## Choosing the claims

`role` is what the role guard gates on. Metric and tenant write routes want
`internal_admin` or `internal_analyst`; read routes are looser.

`tenant_id` must be a canonical UUID4. The control plane rejects anything else
with a 401 on every route, including the global-scope metric routes, so never mint
with `global` or a readable name. With no `--tenant`, the script mints a fresh
random UUID4, which is right for control-plane admin work: internal roles read and
write the `global` metric scope whatever the token's tenant, and `global` goes in
the `tenant_id` query parameter, not the claim.

Otherwise `tenant_id` matters more than it looks. Tenant-scoped control-plane
routes 404, not 403, when the queried tenant is not the caller's own, so a
`{"code":"NOT_FOUND"}` on an endpoint you know has data usually means the token's
tenant is wrong, not that the resource is missing. Data-plane serving takes the
tenant from the token, so a query needs the real tenant's UUID (dev water tenant:
`76308178-9074-4ca4-afb0-747cd602d10b`).

## Reading before writing

Control-plane `PUT` routes are **full replacement over the fields supplied**: an
omitted mutable field is cleared. So never hand-assemble a write body. `GET` the
live object, mutate the one field, and send it all back — the metric response
carries every mutable field, so the round-trip is lossless.

Every metric-definition write also republishes the metric-defs S3 snapshot, so N
writes advance the published version N times. Two consequences worth stating in any
report: a rebuild publishes *any* drift already sitting in the store, not just your
change; and the data plane re-reads the snapshot pointer every 30 seconds, so a
publish reaches serving within that window without a redeploy.

`intech-data-plane` `_scratch/metric-seed/add_dimension.py` (on the
`temp-water-loaders-cdt274` reference branch) is a worked example of the
read-mutate-write shape, and `seed_metrics.py` beside it is the counter-example:
it rewrites the whole catalogue from a hardcoded copy that has drifted behind the
store, so running it silently reverts anything edited since. Prefer surgical.

## Verifying a change landed

Check the published snapshot, not just the HTTP 200:

```bash
aws s3 cp s3://cdt-control-plane-dev-configs/metric-defs/global/latest.json - \
  --profile cdt-dev --region eu-west-2
```

Then diff the new `v{n}.json` against the previous version and confirm the delta is
only what was intended. Report anything else that moved rather than assuming it was
yours. Then read it back from `GET /serving/metrics` on the data plane. That is the
proof serving picked it up; the S3 object only proves the publish.

## Provenance

The minting pattern is the control plane's own
`tests/smoke/conftest.py::_mint_smoke_token`. If that ever ships as shared team
tooling on `main`, defer to it and reduce this skill to a pointer — the copy here
exists because the equivalent script currently only lives on a do-not-merge branch.
