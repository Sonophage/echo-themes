# builds the site the ECHO theme store reads: dist/index.json, one zip per theme folder, and each theme's
# README.md, Preview/ and still wallpaper for its store page. ECHO reads the zips through its own theme-folder reader, so this
# script only packs files; it does not interpret the theme format.
import hashlib, json, os, shutil, sys, urllib.parse, zipfile

themes_dir, out = sys.argv[1], sys.argv[2]
shutil.rmtree(out, ignore_errors=True); os.makedirs(f"{out}/themes")
entries = []
for name in sorted(os.listdir(themes_dir)):
    src = os.path.join(themes_dir, name)
    if not os.path.isfile(os.path.join(src, "theme.json")): continue
    archive = f"{out}/themes/{name}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in sorted(os.walk(src)):
            for f in sorted(files):
                path = os.path.join(root, f)
                z.write(path, os.path.join(name, os.path.relpath(path, src)))
    data = open(archive, "rb").read()
    page = f"{out}/themes/{name}"
    os.makedirs(page)
    q = lambda p: urllib.parse.quote(p)
    entry = {"id": name, "name": name, "archive": q(f"themes/{name}.zip"), "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    if os.path.isfile(f"{src}/README.md"):
        shutil.copy(f"{src}/README.md", page); entry["readme"] = q(f"themes/{name}/README.md")
    # the theme's own still wallpaper, shown behind its store page instead of a screenshot (owner, 2026-10-07)
    walls = f"{src}/Wallpaper"
    if os.path.isdir(walls):
        still = next((f for f in sorted(os.listdir(walls)) if f.lower().startswith("wallpaper.") and f.lower().rsplit(".", 1)[-1] in ("png", "jpg", "jpeg", "webp")), None)
        if still:
            os.makedirs(f"{page}/Wallpaper"); shutil.copy(f"{walls}/{still}", f"{page}/Wallpaper/{still}")
            entry["wallpaper"] = q(f"themes/{name}/Wallpaper/{still}")
    preview = f"{src}/Preview"
    if os.path.isdir(preview):
        shutil.copytree(preview, f"{page}/Preview")
        hero = next((f for f in sorted(os.listdir(preview)) if f.lower().startswith("hero.")), None)
        if hero: entry["hero"] = q(f"themes/{name}/Preview/{hero}")
        shots = f"{preview}/Screenshots"
        if os.path.isdir(shots): entry["screenshots"] = [q(f"themes/{name}/Preview/Screenshots/{s}") for s in sorted(os.listdir(shots))][:8]
    entries.append(entry)
json.dump({"format": 1, "themes": entries}, open(f"{out}/index.json", "w"), indent=2)
print(f"{len(entries)} themes -> {out}")
