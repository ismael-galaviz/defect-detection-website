"""Staff command-line tool (specs/001-backend/contracts/cli.md).

Run against production with: railway run python -m app.cli <command>
"""

import argparse
import http.server
import json
import os
import sys
import urllib.parse
import urllib.request

from app.google import SCOPES, TOKEN_URL


def cmd_google_auth(_args) -> int:
    """One-time OAuth consent on the owner's machine; prints the refresh token."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET first.", file=sys.stderr)
        return 2
    received: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            received.update(dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query)))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab.")

        def log_message(self, *_):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent"})
    print(f"Open this URL, signed in as the VeritX Google account:\n\n{url}\n")
    server.handle_request()
    if "code" not in received:
        print(f"No code received: {received.get('error', 'unknown error')}", file=sys.stderr)
        return 1
    body = urllib.parse.urlencode({
        "code": received["code"], "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    with urllib.request.urlopen(TOKEN_URL, data=body, timeout=15) as resp:  # noqa: S310
        token = json.load(resp)
    if "refresh_token" not in token:
        print("Google returned no refresh token; revoke the app's access and retry.",
              file=sys.stderr)
        return 1
    print(f"GOOGLE_REFRESH_TOKEN={token['refresh_token']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("google-auth", help="get GOOGLE_REFRESH_TOKEN").set_defaults(
        func=cmd_google_auth)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
