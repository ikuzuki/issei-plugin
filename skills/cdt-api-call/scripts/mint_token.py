"""DEV-ONLY minting of a short-lived platform JWT for control-plane API calls.

The control-plane API authenticates a caller with an RS256 platform JWT
(``Authorization: Bearer <token>``). Its only issuing route exchanges a Microsoft
Entra ``id_token``, so there is no machine-to-machine path: a script either borrows
a browser session or signs its own token with the live signing key. This signs its
own, the same way the control-plane smoke fixtures do - four SSM reads under
``/cdt/cdt-control-plane`` and a short-lived RS256 JWT whose issuer, audience and
``token_use`` match what the deployed service validates against.

The caller identity is synthetic. Token validation does no database lookup, so
``sub`` and ``tenant_id`` need not correspond to real records; ``role`` is what the
role guard gates on, and the metric write routes want ``internal_admin`` or
``internal_analyst``.

DEV ONLY, and it reads a private signing key from SSM: point it at a dev profile,
keep the TTL short, and never log or persist the returned value.

Requires ``python-jose`` and ``boto3`` - run it with a repo venv rather than a bare
interpreter (the sibling scripts are stdlib-only; this one cannot be, since stdlib
has no RS256 signer).

Use from a script
-----------------
    from mint_token import mint_token
    token = mint_token(role="internal_admin")

Use from a shell
----------------
    aws sso login --profile cdt-dev
    export AWS_PROFILE=cdt-dev
    export CONTROL_PLANE_TOKEN=$(python mint_token.py)
    python mint_token.py --claims          # print the claims, not the token

Env:
  AWS_PROFILE   (optional)   passed through to boto3; SSO to cdt-dev first
  AWS_REGION    (optional)   defaults to eu-west-2
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from datetime import UTC, datetime, timedelta

SSM_PREFIX = "/cdt/cdt-control-plane"
PRIVATE_KEY_PARAM = f"{SSM_PREFIX}/jwt-private-key"
KEY_ID_PARAM = f"{SSM_PREFIX}/jwt-key-id"
ISSUER_PARAM = f"{SSM_PREFIX}/jwt-issuer"
AUDIENCE_PARAM = f"{SSM_PREFIX}/jwt-audience"

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-2")

# Synthetic caller identity. Validation does no lookup, so these need not exist.
DEFAULT_USER_ID = "local-tooling"
DEFAULT_TENANT_ID = "local"
DEFAULT_ROLE = "internal_admin"
DEFAULT_TTL_MINUTES = 15


def _ssm_values(region: str) -> tuple[str, str, str, str]:
    """Read the four signing parameters, decrypting the private key.

    Returns
    -------
    tuple[str, str, str, str]
        ``(private_key, key_id, issuer, audience)``.

    Raises
    ------
    SystemExit
        If boto3 is absent, or any parameter cannot be read - expired SSO being the
        usual cause.
    """
    try:
        import boto3
    except ImportError:
        raise SystemExit("boto3 not installed; run this with a repo venv.") from None

    ssm = boto3.client("ssm", region_name=region)
    try:
        key = ssm.get_parameter(Name=PRIVATE_KEY_PARAM, WithDecryption=True)
        rest = ssm.get_parameters(
            Names=[KEY_ID_PARAM, ISSUER_PARAM, AUDIENCE_PARAM], WithDecryption=True
        )
    except Exception as exc:
        raise SystemExit(
            f"could not read signing parameters under {SSM_PREFIX}; "
            f"SSO to the target profile first. Cause: {exc}"
        ) from None

    by_name = {p["Name"]: p["Value"] for p in rest["Parameters"]}
    missing = [n for n in (KEY_ID_PARAM, ISSUER_PARAM, AUDIENCE_PARAM) if n not in by_name]
    if missing:
        raise SystemExit(f"missing SSM parameters: {missing}")
    return (
        key["Parameter"]["Value"],
        by_name[KEY_ID_PARAM],
        by_name[ISSUER_PARAM],
        by_name[AUDIENCE_PARAM],
    )


def mint_token(
    role: str = DEFAULT_ROLE,
    tenant_id: str = DEFAULT_TENANT_ID,
    ttl_minutes: int = DEFAULT_TTL_MINUTES,
    region: str = AWS_REGION,
    user_id: str = DEFAULT_USER_ID,
) -> str:
    """Sign and return a platform JWT.

    Parameters
    ----------
    role : str
        Role claim the role guard gates on, e.g. ``internal_admin``.
    tenant_id : str
        Tenant claim. Synthetic unless a route enforces tenant ownership.
    ttl_minutes : int
        Lifetime. Keep it just long enough for the run.
    region : str
        AWS region for the SSM reads.
    user_id : str
        ``sub`` claim.

    Returns
    -------
    str
        A signed RS256 JWT for an Authorization Bearer header.
    """
    try:
        from jose import jwt
    except ImportError:
        raise SystemExit("python-jose not installed; run this with a repo venv.") from None

    private_key, key_id, issuer, audience = _ssm_values(region)
    now = datetime.now(tz=UTC)
    iat = int(now.timestamp())
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "token_use": "access",
        "name": "Local Tooling",
        "email": "local-tooling@curveanalytics.co.uk",
        "iat": iat,
        "nbf": iat,
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": key_id})


def _claims(token: str) -> dict:
    """Decode the payload segment without verifying, for the ``--claims`` summary."""
    body = token.split(".")[1]
    body += "=" * (-len(body) % 4)
    return json.loads(base64.urlsafe_b64decode(body))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Mint a dev platform JWT.")
    parser.add_argument("--role", default=DEFAULT_ROLE)
    parser.add_argument("--tenant", default=DEFAULT_TENANT_ID)
    parser.add_argument("--ttl", type=int, default=DEFAULT_TTL_MINUTES, help="minutes")
    parser.add_argument(
        "--claims",
        action="store_true",
        help="print the claims instead of the token, so nothing secret reaches the terminal",
    )
    args = parser.parse_args(argv)

    token = mint_token(role=args.role, tenant_id=args.tenant, ttl_minutes=args.ttl)
    if args.claims:
        claims = _claims(token)
        print(json.dumps({k: claims[k] for k in sorted(claims)}, indent=2))
        print(f"\nsigned, {len(token)} chars, expires in {args.ttl}m")
        return
    print(token)


if __name__ == "__main__":
    main()
