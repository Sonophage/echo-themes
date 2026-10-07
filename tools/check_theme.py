# checks a theme folder against ECHO's own slot lists and media limits; prints problems, exit 1 if any
import json, os, re, subprocess, sys
from PIL import Image
repo, theme = sys.argv[1], sys.argv[2]
kit = f"{repo}/core/theme-kit/src/main/kotlin/com/echo/themekit"
slots = set(re.findall(r'(?:catbar|item|status)\("([a-z0-9_]+)"', open(f"{kit}/IconSlots.kt").read()))
src = open(f"{kit}/CustomizableIcons.kt").read()
consoles = set(re.findall(r'"([a-z0-9_]+)"', src[src.index("SYSICON_PLATFORM_IDS"):src.index(")")]))
media = dict(re.findall(r'"([a-z_]+)" to (SOUNDS|BOOT|GAME_START)', open(f"{kit}/ThemeMedia.kt").read()))
folder_of = {"SOUNDS": "Sounds", "BOOT": "Boot", "GAME_START": "GameStart"}
limits = open(f"{kit}/UiMediaLimits.kt").read()
const = {k: int(v.replace("_", "")) for k, v in re.findall(r'const val (\w+_MS)\s*=\s*([\d_]+)L', limits)}
spec = {k: v for k, v in re.findall(r'val (\w+)\s*= ?Spec\(Kind\.\w+,\s*[\d_]+L,\s*[\d_]+L,\s*(\w+)', limits)}
slot_spec = dict(re.findall(r'\("([a-z_]+)", UiMediaKind\.\w+, "[^"]*", UiMediaLimits\.(\w+)\)', open(f"{repo}/core/core-domain/src/main/kotlin/com/echo/core/domain/model/UiMediaSlot.kt").read()))
problems, kept = [], 0
def bad(m): problems.append(m)
m = json.load(open(f"{theme}/theme.json"))
if m.get("manifest") not in ("echo-theme", "pfptheme"): bad("theme.json: manifest is not echo-theme")
for key, allowed in [("waveDesign", {"PSP", "ECHO_RINGS", "ECHO_ARCS"}), ("gameBootStyle", {"DISC", "LENS"}), ("launchDiscStyle", {"DISC", "LENS"}), ("buttonSet", {"GENERIC", "XBOX", "NINTENDO", "PLAYSTATION"})]:
    if m.get(key) is not None and m[key] not in allowed: bad(f"theme.json: {key}={m[key]} is not one ECHO knows")
for root, _, files in os.walk(theme):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), theme); parts = rel.split(os.sep); stem, ext = os.path.splitext(f); ext = ext[1:].lower()
        if rel in ("theme.json", "README.md"): kept += 1; continue
        if parts[0] == "Icons":
            ok = (len(parts) == 2 and stem in slots) or (len(parts) == 3 and parts[1] == "Consoles" and stem in consoles)
            if not ok or ext not in ("png", "gif"): bad(f"{rel}: not an icon slot ECHO has"); continue
            if os.path.getsize(os.path.join(root, f)) > 8 << 20: bad(f"{rel}: over 8 MB")
        elif parts[0] == "Wallpaper":
            if f not in ("wallpaper.png", "preview.png") and not re.fullmatch(r"motion\.(mp4|webm|gif)", f): bad(f"{rel}: not a wallpaper file ECHO reads"); continue
        elif parts[0] in folder_of.values():
            if media.get(stem) is None or folder_of[media[stem]] != parts[0] or ext not in ("mp3", "wav", "ogg", "m4a", "mp4", "webm"): bad(f"{rel}: not a media slot of {parts[0]}"); continue
            ms = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(root, f)], capture_output=True, text=True).stdout or 0) * 1000
            hard = const[spec[slot_spec[stem]]]
            if ms <= 0: bad(f"{rel}: no duration")
            elif ms > hard: bad(f"{rel}: {ms:.0f} ms, over the {hard} ms limit")
        elif parts[0] == "Preview":
            if not ((len(parts) == 2 and stem == "hero") or (len(parts) == 3 and parts[1] == "Screenshots")) or ext not in ("jpg", "jpeg", "png", "webp"): bad(f"{rel}: not a hero or screenshot"); continue
        else:
            bad(f"{rel}: has no place in a theme"); continue
        if ext in ("png", "jpg", "jpeg", "webp", "gif"):
            try: Image.open(os.path.join(root, f)).verify()
            except Exception as e: bad(f"{rel}: not a readable picture ({e})"); continue
        kept += 1
print(f"{os.path.basename(os.path.normpath(theme))}: {kept} files kept, {len(problems)} problems")
for p in problems: print("  ", p)
sys.exit(1 if problems else 0)
