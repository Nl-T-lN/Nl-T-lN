#!/usr/bin/env python3
"""Scan GitHub repos, detect tech stack, update README table with icons."""

import os, json, re, base64, urllib.request, urllib.error, math

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
    rows = 4
    cols = math.ceil(len(items) / rows)
    
    grid = [[None for _ in range(cols)] for _ in range(rows)]
    
    for i, item in enumerate(items):
        r = i % rows
        c = i // rows
        grid[r][c] = item
        
    for r in range(rows):
        lines.append("    <tr>")
        for c in range(cols):
            item = grid[r][c]
            if item:
                name, icon = item
                lines.append(
                    f'        <td align="center" width="90">'
                    f'<img height="55" src="./icons/{icon}.svg" width="55">'
                    f"<br>{name}</td>"
                )
            else:
                lines.append('        <td align="center" width="90"></td>')
        lines.append("    </tr>")
    lines.append("</table>")
    return "\n".join(lines)


def build_details(tech_repos):
    """Generate a collapsible <details> section mapping tech → repos."""
    lines = []
    lines.append("<details>")
    lines.append("<summary><b>where each stack is used →</b></summary>")
    lines.append("<br>")
    lines.append("")
    for display, repos in sorted(tech_repos.items(), key=lambda t: t[0].lower()):
        if not repos:
            continue
        repo_links = ", ".join(
            f'<a href="https://github.com/{USER}/{r}">{r}</a>' for r in sorted(repos)
        )
        lines.append(f"**{display}** — {repo_links}")
        lines.append("")
    lines.append("</details>")
    return "\n".join(lines)


def parse_existing(content, techs, tech_repos):
    """Parse existing auto-generated block to ensure we never delete anything."""
    start = content.find("<!-- STACK:AUTO:START -->")
    end = content.find("<!-- STACK:AUTO:END -->")
    if start == -1 or end == -1:
        return
    
    block = content[start:end]
    
    # Parse existing table items
    for match in re.finditer(r'<img[^>]+src="\./icons/([^.]+)\.svg"[^>]*><br>([^<]+)</td>', block):
        icon = match.group(1)
        name = match.group(2)
        if name not in techs:
            techs[name] = (icon, "")  # empty devicon since it's already downloaded
        
    # Parse existing repo mappings
    for match in re.finditer(r'\*\*([^*]+)\*\* — (.*)', block):
        name = match.group(1)
        links = match.group(2)
        for r_match in re.finditer(r'>([^<]+)</a>', links):
            repo = r_match.group(1)
            tech_repos.setdefault(name, set()).add(repo)

def main():
    os.makedirs(ICONS, exist_ok=True)

    print(f"Scanning repos for {USER}...")
    repos = get_repos()
    print(f"Found {len(repos)} repos\n")

    techs = {}           # display_name -> (icon_file, devicon_name)
    tech_repos = {}      # display_name -> set of repo names

    def track(tech_tuple, repo_name):
        """Add a tech and record which repo it came from."""
        name, icon, devicon = tech_tuple
        techs[name] = (icon, devicon)
        tech_repos.setdefault(name, set()).add(repo_name)

    for repo in repos:
        if repo.get("fork"):
            continue
        name = repo["name"]
        print(f"[{name}]")

        # languages
        langs = api(f"/repos/{USER}/{name}/languages") or {}
        for lang in langs:
            if lang in LANGS:
                track(LANGS[lang], name)

        # file indicators
        for t in scan_files(name):
            track(t, name)

        # npm frameworks (only if JS/TS present)
        if any(l in langs for l in ("JavaScript", "TypeScript")):
            for t in scan_npm(name):
                track(t, name)

        # pip frameworks (only if Python present)
        if "Python" in langs:
            for t in scan_pip(name):
                track(t, name)

    # always include Git + GitHub (no specific repo)
    techs["Git"] = ("git", "git")
    techs["GitHub"] = ("github", "github")

    # load manual entries (no specific repo)
    if os.path.exists(MANUAL):
        with open(MANUAL) as f:
            for entry in json.load(f):
                techs[entry["name"]] = (entry["icon"], entry.get("devicon", ""))

    with open(README) as f:
        content = f.read()

    # NEVER DELETE: Merge with existing items from README
    parse_existing(content, techs, tech_repos)

    # dedupe, sort, download missing icons
    valid = []
    for display, (icon_file, devicon) in sorted(techs.items(), key=lambda t: t[0].lower()):
        if os.path.exists(os.path.join(ICONS, f"{icon_file}.svg")):
            valid.append((display, icon_file))
            print(f"  ✓ {display}")
        elif devicon and download_icon(icon_file, devicon):
            valid.append((display, icon_file))
            print(f"  ✓ {display} (new)")
        else:
            print(f"  ✗ {display} (skipped, no icon)")

    table = build_table(valid)
    details = build_details(tech_repos)
    start, end = "<!-- STACK:AUTO:START -->", "<!-- STACK:AUTO:END -->"

    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{table}\n\n{details}\n{end}"

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
