#!/usr/bin/env python3
"""httpkom-cli: CLI for LysKOM using httpkom's endpoints via Quart test client.

Usage:
    python -m httpkom.cli <endpoint> [key=value ...] [--data-file FILE] [options]
    python -m httpkom.cli --list

Examples:
    python -m httpkom.cli person-create --data-file person.json
    python -m httpkom.cli conference-create --data-file conf.json --pers-name "Test" --passwd test123
    python -m httpkom.cli membership-add pers_no=6 conf_no=7 --pers-name "Test" --passwd test123
    python -m httpkom.cli text-get text_no=1
"""

import argparse
import asyncio
import json
import sys

from quart import url_for

from httpkom import app, init_app, HTTPKOM_CONNECTION_HEADER


# CLI name -> (http_method, quart_endpoint_name)
ENDPOINTS = {
    # Persons
    "person-create":              ("POST",   "frontend.persons_create"),
    "person-set-passwd":          ("POST",   "frontend.persons_set_passwd"),
    "person-set-presentation":    ("POST",   "frontend.persons_set_presentation"),
    "person-get-user-area-block": ("GET",    "frontend.persons_get_user_area_block"),

    # Conferences
    "conference-create":          ("POST",   "frontend.conferences_create"),
    "conference-lookup":          ("GET",    "frontend.conferences_list"),
    "conference-get":             ("GET",    "frontend.conferences_get"),
    "conference-get-texts":       ("GET",    "frontend.conferences_get_texts"),

    # Texts
    "text-create":                ("POST",   "frontend.texts_create"),
    "text-get":                   ("GET",    "frontend.texts_get"),
    "text-get-body":              ("GET",    "frontend.texts_get_body"),
    "text-mark":                  ("PUT",    "frontend.texts_put_mark"),
    "text-unmark":                ("DELETE", "frontend.texts_delete_mark"),
    "text-get-marks":             ("GET",    "frontend.texts_get_marks"),
    "text-mark-read":             ("PUT",    "frontend.texts_put_read_marking"),
    "text-mark-unread":           ("DELETE", "frontend.texts_delete_read_marking"),

    # Memberships
    "membership-add":             ("PUT",    "frontend.persons_put_membership"),
    "membership-remove":          ("DELETE", "frontend.persons_delete_membership"),
    "membership-get":             ("GET",    "frontend.persons_get_membership"),
    "membership-list":            ("GET",    "frontend.persons_list_memberships"),
    "membership-get-unread":      ("GET",    "frontend.persons_get_membership_unread"),
    "membership-list-unreads":    ("GET",    "frontend.persons_list_membership_unreads"),
    "membership-set-unread":      ("POST",   "frontend.persons_set_unread"),
    "membership-mark-read":       ("PUT",    "frontend.conferences_put_text_read_marking"),

    # Sessions
    "session-who-am-i":           ("GET",    "frontend.sessions_who_am_i"),
    "session-set-conference":     ("POST",   "frontend.sessions_change_working_conference"),

    # Server
    "server-info":                ("GET",    "frontend.server_info"),
}

SERVER_ID = "cli"


def configure_app(host, port):
    init_app(app)
    app.config["HTTPKOM_LYSKOM_SERVERS"] = [
        (SERVER_ID, "CLI", host, port),
    ]


def parse_key_value_args(args):
    """Parse key=value pairs, coercing numeric values to int."""
    result = {}
    for arg in args:
        if "=" not in arg:
            print(f"Invalid argument (expected key=value): {arg}", file=sys.stderr)
            sys.exit(1)
        key, value = arg.split("=", 1)
        try:
            value = int(value)
        except ValueError:
            pass
        result[key] = value
    return result


def get_path_params(endpoint_name, kv_args):
    """Separate key=value args into path params and remaining body/query params."""
    rule = None
    for r in app.url_map.iter_rules():
        if r.endpoint == endpoint_name:
            rule = r
            break
    if rule is None:
        return {}, kv_args

    path_param_names = set(rule.arguments) - {"server_id"}
    path_params = {}
    remaining = {}
    for key, value in kv_args.items():
        if key in path_param_names:
            path_params[key] = value
        else:
            remaining[key] = value
    return path_params, remaining


def print_endpoints():
    print("Available endpoints:\n")
    for name, (method, endpoint_name) in sorted(ENDPOINTS.items()):
        for rule in app.url_map.iter_rules():
            if rule.endpoint == endpoint_name:
                params = sorted(rule.arguments - {"server_id"})
                param_str = " ".join(f"{p}=..." for p in params) if params else ""
                print(f"  {name:30s} {param_str}")
                break
    print()


async def run(args):
    method, endpoint_name = ENDPOINTS[args.endpoint]

    kv_args = parse_key_value_args(args.params)
    path_params, extra_params = get_path_params(endpoint_name, kv_args)

    # Load body data from file, stdin, or extra key=value params
    data = None
    if args.data_file:
        if args.data_file == "-":
            data = json.load(sys.stdin)
        else:
            with open(args.data_file) as f:
                data = json.load(f)
    if extra_params:
        if data is None:
            data = extra_params
        else:
            data.update(extra_params)

    async with app.test_request_context("/"):
        url = url_for(endpoint_name, server_id=SERVER_ID, **path_params)

    async with app.test_client() as client:
        # Create session
        resp = await client.post(
            f"/{SERVER_ID}/sessions/",
            json={"client": {"name": "httpkom-cli", "version": "0.1"}},
        )
        resp_json = await resp.get_json()
        conn_id = resp_json["connection_id"]
        headers = {HTTPKOM_CONNECTION_HEADER: conn_id}

        # Login if credentials provided
        if args.pers_name and args.passwd:
            resp = await client.post(
                f"/{SERVER_ID}/sessions/current/login",
                json={"pers_name": args.pers_name, "passwd": args.passwd},
                headers=headers,
            )
            if resp.status_code != 201:
                resp_json = await resp.get_json()
                print(json.dumps(resp_json or {"error": "Login failed"}), file=sys.stderr)
                sys.exit(1)

        # Make the actual request
        client_method = getattr(client, method.lower())
        if method in ("GET", "DELETE"):
            resp = await client_method(url, query_string=data, headers=headers)
        else:
            resp = await client_method(url, json=data or {}, headers=headers)

        resp_json = await resp.get_json()
        if resp.status_code >= 400:
            print(json.dumps(resp_json or {"error": resp.status}), file=sys.stderr)
            sys.exit(1)

        if resp_json is not None:
            print(json.dumps(resp_json))


def main():
    parser = argparse.ArgumentParser(
        description="httpkom CLI - command line interface for LysKOM via httpkom",
    )
    parser.add_argument(
        "endpoint", nargs="?",
        help="Endpoint name (use --list to see available endpoints)",
    )
    parser.add_argument(
        "params", nargs="*",
        help="Path/body parameters as key=value pairs",
    )
    parser.add_argument("--data-file", "-f", help="JSON data file (use - for stdin)")
    parser.add_argument("--host", default="localhost", help="LysKOM server host")
    parser.add_argument("--port", type=int, default=4894, help="LysKOM server port")
    parser.add_argument("--pers-name", help="Person name for login")
    parser.add_argument("--passwd", help="Password for login")
    parser.add_argument("--list", action="store_true", help="List available endpoints")

    args = parser.parse_args()

    configure_app(args.host, args.port)

    if args.list:
        print_endpoints()
        return

    if not args.endpoint:
        parser.print_help()
        sys.exit(1)

    if args.endpoint not in ENDPOINTS:
        print(f"Unknown endpoint: {args.endpoint}", file=sys.stderr)
        print("Use --list to see available endpoints.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
