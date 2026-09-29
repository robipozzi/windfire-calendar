import os
import sys
import argparse
import traceback
import requests # pyright: ignore[reportMissingModuleSource]
from colorama import Fore, Style, init # pyright: ignore[reportMissingModuleSource]
from datetime import date

colorama_init = init(autoreset=True)

# ======================================================================
# ======================== START - CONFIGURATION =======================
# ======================================================================
DEFAULT_CALENDAR_PORT = "8443"
ENVIRONMENT_ALIASES = {"1": "dev", "2": "test", "3": "prod", "dev": "dev", "test": "test", "prod": "prod"}
ENVIRONMENT_NAMES = {"dev": "Development", "test": "Test", "prod": "Production"}

# Windfire Calendar server host per environment (port comes from PORT, default 8443)
CALENDAR_ENVIRONMENTS = {
    "dev": "localhost",
    "test": "localhost",
    "prod": "raspberry02",
}

# Windfire Security server per environment: defaults, overridden by KEYCLOAK_<ENV>_HOST/PORT in app/.env
SECURITY_ENVIRONMENTS = {
    "dev": ("localhost", "8444"),
    "test": ("localhost", "8444"),
    "prod": ("raspberry01", "8444"),
}
DEFAULT_SECURITY_ENVIRONMENT = "prod"
APP_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", ".env")

REQUEST_TIMEOUT = 30
CALENDAR_ENDPOINTS = {
    "/v1/calendar/events/count/year": "post",
    "/v1/calendar/events/count/today": "post",
    "/v1/calendar/events/count/range": "post",
    "/v1/calendar/events/upcoming": "get",
}
ALL_ENDPOINTS = {"/v1/monitor/health": "get", **CALENDAR_ENDPOINTS}

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
service = os.getenv("SERVICE")
verify_ssl = os.getenv("VERIFY_SSL_CERTS", "false").strip().lower() == "true"
ca_bundle_path = os.getenv("ROOT_CA_PATH")
event_title = os.getenv("EVENT_TITLE", "Palestra")

# Resolved at startup by configure()
httpsCalendarServerUrl = None
authClient = None
token = None


def read_env_file(path):
    """Read KEY=value pairs from a .env file (inline comments and quotes are stripped)"""
    values = {}
    try:
        with open(path) as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                value = value.split("#", 1)[0].strip().strip("\"'")
                values[key.strip()] = value
    except OSError:
        pass
    return values


def normalize_environment(value):
    if value is None:
        return None
    return ENVIRONMENT_ALIASES.get(value.strip().lower())


def prompt_environment(title, default=None):
    """Ask for an environment until a valid answer is given; an empty answer selects default (if any)"""
    while True:
        print(Style.BRIGHT + Fore.BLUE + f"Select {title} environment :")
        for number, name in (("1", "dev"), ("2", "test"), ("3", "prod")):
            suffix = " [default]" if name == default else ""
            print(Style.BRIGHT + Fore.BLUE + f"{number}. {ENVIRONMENT_NAMES[name]}{suffix}")
        try:
            answer = input().strip()
        except EOFError:
            answer = ""
            if default is None:
                print(Style.BRIGHT + Fore.LIGHTRED_EX + f"No {title} environment selected")
                sys.exit(2)
        if not answer and default is not None:
            return default
        environment = normalize_environment(answer)
        if environment:
            return environment
        print(Style.BRIGHT + Fore.LIGHTRED_EX + f"No valid option selected: {answer}")


def resolve_environment(cli_value, env_var, title, default=None):
    """Resolution order: CLI argument -> environment variable -> interactive prompt"""
    for source, value in (("argument", cli_value), (env_var, os.getenv(env_var))):
        if value:
            environment = normalize_environment(value)
            if environment is None:
                print(Style.BRIGHT + Fore.LIGHTRED_EX + f"Invalid {title} environment '{value}' from {source}, expected 1|2|3|dev|test|prod")
                sys.exit(2)
            return environment
    return prompt_environment(title, default)


def configure(args):
    """Resolve Calendar and Security servers, then initialize authClient pointing at the chosen Security server"""
    global httpsCalendarServerUrl, authClient

    calendarEnvironment = resolve_environment(args.env, "ENVIRONMENT", "Windfire Calendar")
    securityEnvironment = resolve_environment(args.security_env, "SECURITY_ENVIRONMENT", "Windfire Security",
                                              default=DEFAULT_SECURITY_ENVIRONMENT)

    calendarServerPort = DEFAULT_CALENDAR_PORT
    port_env = os.getenv("PORT")
    if port_env:
        try:
            calendarServerPort = str(int(port_env))
        except ValueError:
            print(Style.BRIGHT + Fore.YELLOW + f"Invalid PORT value '{port_env}', using default port {calendarServerPort}")
    httpsCalendarServerUrl = os.getenv("HTTPS_CALENDAR_SERVER_URL",
                                       f"https://{CALENDAR_ENVIRONMENTS[calendarEnvironment]}:{calendarServerPort}")

    securityHost, securityPort = SECURITY_ENVIRONMENTS[securityEnvironment]
    envFile = read_env_file(APP_ENV_FILE)
    prefix = securityEnvironment.upper()
    securityHost = envFile.get(f"KEYCLOAK_{prefix}_HOST") or securityHost
    securityPort = envFile.get(f"KEYCLOAK_{prefix}_PORT") or securityPort
    # authClient reads these in __init__, so they must be set before importing it
    os.environ["KEYCLOAK_SERVER_HOST"] = securityHost
    os.environ["KEYCLOAK_SERVER_PORT"] = securityPort
    from client.authClient import authClient as client
    authClient = client

    print(Style.BRIGHT + Fore.CYAN + "Configuration:")
    print(Style.BRIGHT + f"  Windfire Calendar environment : {ENVIRONMENT_NAMES[calendarEnvironment]} --> {httpsCalendarServerUrl}")
    print(Style.BRIGHT + f"  Windfire Security environment : {ENVIRONMENT_NAMES[securityEnvironment]} --> {authClient.url_base}")
    if verify_ssl:
        print(Style.BRIGHT + f"  SSL certificates              : verified with {ca_bundle_path}")
    else:
        print(Style.BRIGHT + f"  SSL certificates              : NOT verified")
    print(Style.BRIGHT + f"  Event title                   : {event_title}")
    print("")
# ======================================================================
# ========================= END - CONFIGURATION ========================
# ======================================================================

# ======================================================================
# ========================== START - RUNNER ============================
# ======================================================================
class TestFailure(Exception):
    pass


class TestSkipped(Exception):
    pass


TESTS = []


def test_case(name, group, requires_auth=False):
    """Register a test; it fails through assert/TestFailure and is skipped when it needs a token and there is none"""
    def decorator(func):
        TESTS.append({"name": name, "group": group, "requires_auth": requires_auth, "func": func})
        return func
    return decorator


def call(method, path, json=None, token=None, allow_redirects=True, headers=None):
    """Call the Windfire Calendar server; token=None sends no Authorization header"""
    http_headers = {"Content-Type": "application/json"}
    if token:
        http_headers["Authorization"] = f"Bearer {token}"
    if headers:
        http_headers.update(headers)
    return requests.request(method, httpsCalendarServerUrl + path,
                            json=json,
                            headers=http_headers,
                            verify=ca_bundle_path if verify_ssl else False,
                            allow_redirects=allow_redirects,
                            timeout=REQUEST_TIMEOUT)


def body(response):
    try:
        return response.json()
    except ValueError:
        return response.text


def expect_status(response, *expected):
    if response.status_code not in expected:
        raise TestFailure(f"{response.request.method} {response.url} -> expected {'/'.join(map(str, expected))}, "
                          f"got {response.status_code}: {body(response)}")
    return body(response)


def check_count_schema(result):
    for field in ("event_title", "count", "start_date", "end_date"):
        assert field in result, f"field '{field}' missing in {result}"
    assert isinstance(result["count"], int) and not isinstance(result["count"], bool), f"count is not an int: {result['count']!r}"
    assert result["count"] >= 0, f"count is negative: {result['count']}"
    assert result["event_title"] == event_title, f"event_title {result['event_title']!r} != {event_title!r}"


def run_tests(only=None):
    global token
    selected = [t for t in TESTS if not only or only.lower() in f"{t['group']} {t['name']}".lower()]
    if not selected:
        print(Style.BRIGHT + Fore.LIGHTRED_EX + f"No test matches '{only}'")
        return 1
    # Tests needing a token also need the authentication test, even if --only filtered it out
    authTest = next(t for t in TESTS if t["func"] is test_authenticate)
    if any(t["requires_auth"] for t in selected) and authTest not in selected:
        selected = sorted(selected + [authTest], key=TESTS.index)

    results = []
    currentGroup = None
    for test in selected:
        if test["group"] != currentGroup:
            currentGroup = test["group"]
            print(Style.BRIGHT + Fore.BLUE + f"===> {currentGroup} <===")
        status, reason = "PASS", ""
        try:
            if test["requires_auth"] and not token:
                raise TestSkipped("no authentication token")
            test["func"]()
        except TestSkipped as e:
            status, reason = "SKIP", str(e)
        except (AssertionError, TestFailure) as e:
            status, reason = "FAIL", str(e) or "assertion failed"
        except requests.RequestException as e:
            status, reason = "FAIL", f"request error: {e}"
        except Exception as e:
            status, reason = "FAIL", f"{type(e).__name__}: {e}"
            traceback.print_exc()
        color = {"PASS": Fore.GREEN, "FAIL": Fore.LIGHTRED_EX, "SKIP": Fore.YELLOW}[status]
        print(Style.BRIGHT + color + f"  [{status}] {test['name']}" + (f" - {reason}" if reason else ""))
        results.append((test, status, reason))
    print("")
    return print_summary(results)


def print_summary(results):
    print(Style.BRIGHT + Fore.CYAN + "######################################################")
    print(Style.BRIGHT + Fore.CYAN + "##################### Summary ########################")
    print(Style.BRIGHT + Fore.CYAN + "######################################################")
    width = max(len(f"{t['group']} / {t['name']}") for t, _, _ in results)
    for test, status, reason in results:
        color = {"PASS": Fore.GREEN, "FAIL": Fore.LIGHTRED_EX, "SKIP": Fore.YELLOW}[status]
        label = f"{test['group']} / {test['name']}".ljust(width)
        line = f"{label}  {status}"
        if status != "PASS":
            line += f"  ({reason[:200]})"
        print(Style.BRIGHT + color + line)
    totals = {s: sum(1 for _, status, _ in results if status == s) for s in ("PASS", "FAIL", "SKIP")}
    print("")
    color = Fore.LIGHTRED_EX if totals["FAIL"] else Fore.GREEN
    print(Style.BRIGHT + color + f"Total: {len(results)}  Passed: {totals['PASS']}  Failed: {totals['FAIL']}  Skipped: {totals['SKIP']}")
    return 1 if totals["FAIL"] else 0
# ======================================================================
# =========================== END - RUNNER =============================
# ======================================================================

# ======================================================================
# ======================== START - TEST CASES ==========================
# ======================================================================
@test_case("health", group="Monitor")
def test_health():
    result = expect_status(call("get", "/v1/monitor/health"), 200)
    assert result.get("status") == "healthy", f"status is {result.get('status')!r}"
    assert result.get("service"), "service missing"


@test_case("root redirect", group="Monitor")
def test_root_redirect():
    response = call("get", "/", allow_redirects=False)
    expect_status(response, 307)
    assert response.headers.get("location") == "/docs", f"location is {response.headers.get('location')!r}"


@test_case("OpenAPI contract", group="Monitor")
def test_openapi_contract():
    paths = expect_status(call("get", "/openapi.json"), 200).get("paths", {})
    for path, method in ALL_ENDPOINTS.items():
        assert path in paths, f"{path} missing from OpenAPI"
        assert method in paths[path], f"{method.upper()} {path} missing from OpenAPI (has {list(paths[path])})"


# The suite's token comes from this test; run_tests() always runs it when a selected test needs a token
@test_case("authenticate with valid credentials", group="Security")
def test_authenticate():
    global token
    assert username and password and service, "USERNAME, PASSWORD and SERVICE must be set"
    token = authClient.authenticate(username, password, service)
    assert token, f"no token returned by {authClient.url_base} for user '{username}' and service '{service}'"


@test_case("authenticate with a wrong password", group="Security", requires_auth=True)
def test_authenticate_wrong_password():
    result = authClient.authenticate(username, password + "-wrong", service)
    assert result is None, "a token was returned for a wrong password"


def protected_request(path, method, token_value):
    json = {"event_title": event_title, "year": 2025} if method == "post" else None
    return call(method, path, json=json, token=token_value)


def register_authorization_tests():
    for path, method in CALENDAR_ENDPOINTS.items():
        def no_bearer(path=path, method=method):
            # FastAPI's HTTPBearer answers 403 on older versions and 401 on newer ones
            expect_status(protected_request(path, method, None), 401, 403)

        def fake_token(path=path, method=method):
            result = expect_status(protected_request(path, method, "not-a-valid-token"), 401)
            assert result.get("detail") == "Invalid or expired token", f"detail is {result.get('detail')!r}"

        test_case(f"{method.upper()} {path} with no Bearer header", group="Authorization")(no_bearer)
        test_case(f"{method.upper()} {path} with a fake token", group="Authorization")(fake_token)


register_authorization_tests()


@test_case("security headers on a protected endpoint", group="Security headers")
def test_security_headers():
    response = protected_request("/v1/calendar/events/upcoming", "get", "not-a-valid-token")
    expected = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }
    for header, value in expected.items():
        assert response.headers.get(header) == value, f"{header} is {response.headers.get(header)!r}, expected {value!r}"


YEAR_PATH = "/v1/calendar/events/count/year"
TODAY_PATH = "/v1/calendar/events/count/today"
RANGE_PATH = "/v1/calendar/events/count/range"
UPCOMING_PATH = "/v1/calendar/events/upcoming"


@test_case("past year (2025)", group="count/year", requires_auth=True)
def test_year_past():
    result = expect_status(call("post", YEAR_PATH, {"event_title": event_title, "year": 2025}, token), 200)
    check_count_schema(result)
    assert (result["start_date"], result["end_date"]) == ("2025-01-01", "2025-12-31"), \
        f"date range is {result['start_date']} -> {result['end_date']}"


@test_case("current year", group="count/year", requires_auth=True)
def test_year_current():
    today = date.today()
    result = expect_status(call("post", YEAR_PATH, {"event_title": event_title, "year": today.year}, token), 200)
    check_count_schema(result)
    assert result["start_date"] == f"{today.year}-01-01", f"start_date is {result['start_date']}"
    assert result["end_date"] == today.isoformat(), f"end_date is {result['end_date']}, expected today"


@test_case("missing year", group="count/year", requires_auth=True)
def test_year_missing():
    expect_status(call("post", YEAR_PATH, {"event_title": event_title}, token), 400)


@test_case("missing event_title", group="count/year", requires_auth=True)
def test_year_missing_title():
    expect_status(call("post", YEAR_PATH, {"year": 2025}, token), 422)


@test_case("non-numeric year", group="count/year", requires_auth=True)
def test_year_not_numeric():
    expect_status(call("post", YEAR_PATH, {"event_title": event_title, "year": "abc"}, token), 422)


@test_case("start = 1 June of the current year", group="count/today", requires_auth=True)
def test_today():
    start = date(date.today().year, 6, 1).isoformat()
    result = expect_status(call("post", TODAY_PATH, {"event_title": event_title, "start_date": start}, token), 200)
    check_count_schema(result)
    assert result["start_date"] == start, f"start_date is {result['start_date']}, expected {start}"
    assert result["end_date"] == date.today().isoformat(), f"end_date is {result['end_date']}, expected today"


@test_case("missing start_date", group="count/today", requires_auth=True)
def test_today_missing_start():
    expect_status(call("post", TODAY_PATH, {"event_title": event_title}, token), 400)


@test_case("bad date format", group="count/today", requires_auth=True)
def test_today_bad_date():
    expect_status(call("post", TODAY_PATH, {"event_title": event_title, "start_date": "01/06/2025"}, token), 422)


@test_case("2023-01-01 -> 2023-12-31", group="count/range", requires_auth=True)
def test_range():
    data = {"event_title": event_title, "start_date": "2023-01-01", "end_date": "2023-12-31"}
    result = expect_status(call("post", RANGE_PATH, data, token), 200)
    check_count_schema(result)
    assert (result["start_date"], result["end_date"]) == ("2023-01-01", "2023-12-31"), \
        f"date range is {result['start_date']} -> {result['end_date']}"


@test_case("start == end", group="count/range", requires_auth=True)
def test_range_same_day():
    data = {"event_title": event_title, "start_date": "2023-06-01", "end_date": "2023-06-01"}
    check_count_schema(expect_status(call("post", RANGE_PATH, data, token), 200))


@test_case("start > end", group="count/range", requires_auth=True)
def test_range_inverted():
    data = {"event_title": event_title, "start_date": "2023-12-31", "end_date": "2023-01-01"}
    result = expect_status(call("post", RANGE_PATH, data, token), 400)
    detail = str(result.get("detail", "")).lower()
    assert "before or equal" in detail, f"detail is {result.get('detail')!r}"


@test_case("missing end_date", group="count/range", requires_auth=True)
def test_range_missing_end():
    expect_status(call("post", RANGE_PATH, {"event_title": event_title, "start_date": "2023-01-01"}, token), 400)


@test_case("range(2025) == year(2025)", group="Consistency", requires_auth=True)
def test_range_matches_year():
    byRange = expect_status(call("post", RANGE_PATH, {"event_title": event_title,
                                                      "start_date": "2025-01-01", "end_date": "2025-12-31"}, token), 200)
    byYear = expect_status(call("post", YEAR_PATH, {"event_title": event_title, "year": 2025}, token), 200)
    assert byRange["count"] == byYear["count"], f"range count {byRange['count']} != year count {byYear['count']}"


@test_case("GET upcoming events", group="upcoming", requires_auth=True)
def test_upcoming():
    result = expect_status(call("get", UPCOMING_PATH, token=token), 200)
    events = result.get("events")
    assert isinstance(events, list), f"events is not a list: {events!r}"
    assert result.get("count") == len(events), f"count {result.get('count')} != {len(events)} events"
    assert len(events) <= 10, f"{len(events)} events returned, expected at most 10"
    for event in events:
        for field in ("id", "summary", "start", "end"):
            assert field in event, f"field '{field}' missing in event {event}"
    print(f"     {len(events)} upcoming events")


@test_case("GET on a POST-only endpoint", group="Method")
def test_wrong_method():
    expect_status(call("get", YEAR_PATH), 405)
# ======================================================================
# ========================= END - TEST CASES ===========================
# ======================================================================


def main():
    parser = argparse.ArgumentParser(description="Windfire Calendar API test suite")
    parser.add_argument("--env", help="Windfire Calendar environment: 1|2|3 (dev|test|prod)")
    parser.add_argument("--security-env", help="Windfire Security environment: 1|2|3 (dev|test|prod), default prod")
    parser.add_argument("--only", help="run only the tests whose group or name contains this text")
    args = parser.parse_args()

    print(Style.BRIGHT + Fore.CYAN + "######################################################")
    print(Style.BRIGHT + Fore.CYAN + "##### Testing FastAPI Calendar Service Endpoints #####")
    print(Style.BRIGHT + Fore.CYAN + "######################################################")
    print("")
    configure(args)
    return run_tests(args.only)


if __name__ == "__main__":
    sys.exit(main())
