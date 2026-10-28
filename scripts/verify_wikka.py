"""Drives a real WikkaWiki in Docker for scripts/verify-docker.sh.
Python 3 standard library only. Usage: python3 scripts/verify_wikka.py <base-url>
"""
import http.cookiejar
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import urllib.error
import uuid

BASE = sys.argv[1].rstrip("/")
WEB = "pa-wikka-web"
ADMIN = "WikiAdmin"
PASSWORD = "Test" + uuid.uuid4().hex[:12]
TAG = '<script defer src="https://privatusstats.com/js/pa.js"'
failures = 0


def check(name, cond, detail=""):
    global failures
    if cond:
        print("ok   " + name)
    else:
        failures += 1
        print("FAIL " + name + ("\n  " + detail[:800] if detail else ""))


def session():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def get(op, path):
    try:
        with op.open(BASE + path, timeout=60) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return "HTTP %d %s" % (e.code, e.read().decode("utf-8", "replace"))


def post(op, path, fields):
    with op.open(urllib.request.Request(BASE + path, data=urllib.parse.urlencode(fields).encode()), timeout=120) as r:
        return r.read().decode("utf-8", "replace")


def head(html):
    m = re.search(r"(?is)<head.*?</head>", html)
    return m.group(0) if m else ""


def sh(cmd):
    subprocess.run(["docker", "exec", WEB, "sh", "-c", cmd], check=True)


def set_config(extra):
    """Rewrites wikka.config.php with extra keys, using PHP inside the container."""
    php = (
        "include '/var/www/html/wikka.config.php';"
        "foreach (json_decode($argv[1], true) as $k => $v) { if ($v === null) unset($wakkaConfig[$k]); else $wakkaConfig[$k] = $v; }"
        "file_put_contents('/var/www/html/wikka.config.php', '<?php' . PHP_EOL . '$wakkaConfig = ' . var_export($wakkaConfig, true) . ';' . PHP_EOL);"
    )
    import json
    subprocess.run(["docker", "exec", WEB, "php", "-r", php, json.dumps(extra)], check=True)


# 1. Run the Wikka installer.
op = session()
get(op, "/wikka.php?installAction=default")
install = post(op, "/wikka.php?installAction=default", [
    ("config[dbms_host]", "pa-wikka-db"), ("config[dbms_database]", "wikka"), ("config[dbms_user]", "wikka"),
    ("config[dbms_password]", "wikkapw"), ("config[table_prefix]", "wikka_"), ("config[wakka_name]", "Example"),
    ("config[root_page]", "HomePage"), ("config[wiki_suffix]", "@wikka"), ("config[meta_keywords]", ""),
    ("config[meta_description]", ""), ("config[admin_users]", ADMIN), ("config[admin_email]", "admin@example.com"),
    ("password", PASSWORD), ("password2", PASSWORD), ("config[enable_version_check]", "0"), ("submit", "Continue"),
])
# The installer redirects to the install step, which urllib follows.
m = re.search(r'name="config" value="([^"]*)"', install)
check("installer reached the write step", m is not None, re.sub(r"<[^>]+>", " ", install)[-600:])
if m:
    import html as htmllib
    post(op, "/wikka.php?installAction=writeconfig", [("config", htmllib.unescape(m.group(1)))])
home = get(session(), "/HomePage")
check("wiki is installed", "<html" in home.lower() and "installAction" not in home, home[:300])

# 2. Add the action line to every theme header, just before </head>.
sh("for f in /var/www/html/templates/*/header.php; do sed -i 's#</head>#<?php echo $this->Action(\"privatusanalytics\"); ?>\\n</head>#' \"$f\"; done")
check("no tag before a site ID is set", "privatusstats.com" not in get(session(), "/HomePage"))

# 3. Site ID in wikka.config.php.
set_config({"privatus_site_id": "pa_Docker123", "privatus_modules": "engage,vitals"})
home = get(session(), "/HomePage")
check("exact tag is in the head", TAG + ' data-site="pa_Docker123" data-modules="engage,vitals"></script>' in head(home), head(home)[-600:])
check("tag is printed once", home.count("privatusstats.com/js/pa.js") == 1)
check("other pages get it too", TAG in head(get(session(), "/RecentChanges")))

# 4. No modules setting means all five.
set_config({"privatus_modules": None})
check("default modules are all five",
      'data-modules="engage,auto,vitals,clicks,ask"' in head(get(session(), "/HomePage")))

# 5. Admins are skipped by default, and counted when the setting is 0.
admin = session()
login = get(admin, "/UserSettings")
fields = [(n, v) for n, v in re.findall(r'<input[^>]*type="hidden"[^>]*name="([^"]*)"[^>]*value="([^"]*)"', login)]
post(admin, "/UserSettings", fields + [("name", ADMIN), ("password", PASSWORD), ("action", "login"), ("submit", "Login")])
settings_page = get(admin, "/UserSettings")
logged_in = "logout" in settings_page.lower()
check("admin logged in", logged_in, re.sub(r"<[^>]+>", " ", settings_page)[-400:])
check("logged-in admin gets no tag", "privatusstats.com" not in get(admin, "/HomePage"))
set_config({"privatus_skip_admins": "0"})
check("admin gets the tag when privatus_skip_admins is 0", TAG in head(get(admin, "/HomePage")))

# 6. A bad site ID prints nothing.
set_config({"privatus_site_id": 'pa_x" onload="alert(1)'})
bad = get(session(), "/HomePage")
check("bad site ID prints no tag", "privatusstats.com" not in bad and "onload" not in bad)

# 7. The action inside a page body, with its own site ID.
set_config({"privatus_site_id": ""})
sh("""php -r '
include "/var/www/html/wikka.config.php";
$c = $wakkaConfig; $db = new mysqli($c["dbms_host"], $c["dbms_user"], $c["dbms_password"], $c["dbms_database"]);
$db->query("UPDATE " . $c["table_prefix"] . "pages SET body = CONCAT(body, \\"\\n{{privatusanalytics site=\\\\\\"pa_InPage1\\\\\\" modules=\\\\\\"ask\\\\\\"}}\\") WHERE tag = \\"SandBox\\" AND latest = \\"Y\\"");
'""")
sandbox = get(session(), "/SandBox")
check("{{privatusanalytics site=...}} in a page prints the tag", TAG + ' data-site="pa_InPage1" data-modules="ask"></script>' in sandbox,
      re.sub(r"\s+", " ", sandbox)[-600:])

print("\nAll checks passed." if failures == 0 else "\n%d failed." % failures)
sys.exit(1 if failures else 0)
