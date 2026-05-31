#!/usr/bin/env python3
"""Scan GitHub repos, detect tech stack, update README table with icons."""

import os, json, re, base64, urllib.request, urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN", "")
USER = os.environ.get("GITHUB_USER", "nl-t-ln")
ICONS = "./icons"
README = "./README.md"
MANUAL = "./.github/manual-stack.json"
COLS = 7
CDN = "https://cdn.jsdelivr.net/gh/devicons/devicon/icons"

# GitHub API language → (display, icon_file, devicon_name)
LANGS = {
    "C": ("C", "c", "c"),
    "C++": ("C++", "cplusplus", "cplusplus"),
    "C#": ("C#", "csharp", "csharp"),
    "Python": ("Python", "python", "python"),
    "Java": ("Java", "java", "java"),
    "JavaScript": ("JavaScript", "javascript", "javascript"),
    "TypeScript": ("TypeScript", "typescript", "typescript"),
    "HTML": ("HTML5", "html5", "html5"),
    "CSS": ("CSS3", "css3", "css3"),
    "Go": ("Go", "go", "go"),
    "Rust": ("Rust", "rust", "rust"),
    "Ruby": ("Ruby", "ruby", "ruby"),
    "PHP": ("PHP", "php", "php"),
    "Swift": ("Swift", "swift", "swift"),
    "Kotlin": ("Kotlin", "kotlin", "kotlin"),
    "Dart": ("Dart", "dart", "dart"),
    "Shell": ("Bash", "bash", "bash"),
    "Lua": ("Lua", "lua", "lua"),
    "Scala": ("Scala", "scala", "scala"),
    "SCSS": ("Sass", "sass", "sass"),
}

# npm dependency name → (display, icon_file, devicon_name)
NPM = {
    "react": ("React", "react", "react"),
    "next": ("Next.js", "nextjs", "nextjs"),
    "vue": ("Vue.js", "vuejs", "vuejs"),
    "nuxt": ("Nuxt.js", "nuxtjs", "nuxtjs"),
    "@angular/core": ("Angular", "angular", "angularjs"),
    "express": ("Express.js", "express", "express"),
    "tailwindcss": ("Tailwind", "tailwindcss", "tailwindcss"),
    "mongoose": ("MongoDB", "mongodb", "mongodb"),
    "firebase": ("Firebase", "firebase", "firebase"),
    "svelte": ("Svelte", "svelte", "svelte"),
    "electron": ("Electron", "electron", "electron"),
}

# pip package → (display, icon_file, devicon_name)
PIP = {
    "flask": ("Flask", "flask", "flask"),
    "django": ("Django", "django", "django"),
    "fastapi": ("FastAPI", "fastapi", "fastapi"),
    "numpy": ("NumPy", "numpy", "numpy"),
    "pandas": ("Pandas", "pandas", "pandas"),
    "tensorflow": ("TensorFlow", "tensorflow", "tensorflow"),
    "torch": ("PyTorch", "pytorch", "pytorch"),
    "opencv-python": ("OpenCV", "opencv", "opencv"),
}

# filename → (display, icon_file, devicon_name)
FILES = {
    "Dockerfile": ("Docker", "docker", "docker"),
    "docker-compose.yml": ("Docker", "docker", "docker"),
    "docker-compose.yaml": ("Docker", "docker", "docker"),
    "go.mod": ("Go", "go", "go"),
    "Cargo.toml": ("Rust", "rust", "rust"),
    "Gemfile": ("Ruby", "ruby", "ruby"),
    "pubspec.yaml": ("Flutter", "flutter", "flutter"),
}


def api(endpoint):
    req = urllib.request.Request(f"https://api.github.com{endpoint}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  API {e.code}: {endpoint}")
        return None


def get_repos():
    repos, page = [], 1
    while True:
        data = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def get_file(repo, path):
    data = api(f"/repos/{USER}/{repo}/contents/{path}")
    if data and isinstance(data, dict) and "content" in data:
        return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return None


def scan_npm(repo):
    techs = set()
    raw = get_file(repo, "package.json")
    if not raw:
        return techs
    try:
        pkg = json.loads(raw)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        for key, val in NPM.items():
            if key in deps:
                techs.add(val)
    except json.JSONDecodeError:
        pass
    return techs


def scan_pip(repo):
    techs = set()
    raw = get_file(repo, "requirements.txt")
    if not raw:
        return techs
    for line in raw.splitlines():
        pkg = re.split(r"[>=<!\[\];#]", line.strip())[0].strip().lower()
        if pkg in PIP:
            techs.add(PIP[pkg])
    return techs


def scan_files(repo):
    techs = set()
    root = api(f"/repos/{USER}/{repo}/contents/")
    if not root or not isinstance(root, list):
        return techs
    names = {i["name"] for i in root}
    for fname, val in FILES.items():
        if fname in names:
            techs.add(val)
    return techs


def download_icon(icon_file, devicon_name):
    path = os.path.join(ICONS, f"{icon_file}.svg")
    if os.path.exists(path):
        return True
    for variant in ("original", "plain", "original-wordmark", "plain-wordmark"):
        url = f"{CDN}/{devicon_name}/{devicon_name}-{variant}.svg"
        try:
            urllib.request.urlretrieve(url, path)
            print(f"  Downloaded {icon_file}.svg ({variant})")
            return True
        except urllib.error.HTTPError:
            continue
    print(f"  No icon found for {icon_file}")
    return False


def build_table(items):
    """items: list of (display_name, icon_file)"""
    lines = ['<table align="center">']
    for i in range(0, len(items), COLS):
        row = items[i : i + COLS]
        lines.append("    <tr>")
        for name, icon in row:
            lines.append(
                f'        <td align="center" width="90">'
                f'<img height="55" src="./icons/{icon}.svg" width="55">'
                f"<br>{name}</td>"
            )
        lines.append("    </tr>")
    lines.append("</table>")
    return "\n".join(lines)


def main():
    os.makedirs(ICONS, exist_ok=True)

    print(f"Scanning repos for {USER}...")
    repos = get_repos()
    print(f"Found {len(repos)} repos\n")

    techs = set()  # set of (display, icon_file, devicon_name)

    for repo in repos:
        if repo.get("fork"):
            continue
        name = repo["name"]
        print(f"[{name}]")

        # languages
        langs = api(f"/repos/{USER}/{name}/languages") or {}
        for lang in langs:
            if lang in LANGS:
                techs.add(LANGS[lang])

        # file indicators
        techs.update(scan_files(name))

        # npm frameworks (only if JS/TS present)
        if any(l in langs for l in ("JavaScript", "TypeScript")):
            techs.update(scan_npm(name))

        # pip frameworks (only if Python present)
        if "Python" in langs:
            techs.update(scan_pip(name))

    # always include Git + GitHub
    techs.add(("Git", "git", "git"))
    techs.add(("GitHub", "github", "github"))

    # load manual entries
    if os.path.exists(MANUAL):
        with open(MANUAL) as f:
            for entry in json.load(f):
                # manual items use local icons only, no devicon download
                techs.add((entry["name"], entry["icon"], entry.get("devicon", "")))

    # dedupe, sort, download missing icons
    valid = []
    for display, icon_file, devicon in sorted(techs, key=lambda t: t[0].lower()):
        if os.path.exists(os.path.join(ICONS, f"{icon_file}.svg")):
            valid.append((display, icon_file))
            print(f"  ✓ {display}")
        elif devicon and download_icon(icon_file, devicon):
            valid.append((display, icon_file))
            print(f"  ✓ {display} (new)")
        else:
            print(f"  ✗ {display} (skipped, no icon)")

    # build table and update README
    table = build_table(valid)
    start, end = "<!-- STACK:AUTO:START -->", "<!-- STACK:AUTO:END -->"

    with open(README) as f:
        content = f.read()

    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{table}\n{end}"

    if pat.search(content):
        content = pat.sub(replacement, content)
    else:
        print("ERROR: markers not found in README.md")
        return

    with open(README, "w") as f:
        f.write(content)

    print(f"\n✓ README updated with {len(valid)} technologies")


if __name__ == "__main__":
    main()
