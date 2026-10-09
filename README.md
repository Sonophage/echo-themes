# ECHO themes

The themes in ECHO's online theme store. ECHO reads `index.json` from this repo's GitHub Pages site and
downloads a theme as a zip of its folder.

## Add a theme

1. Put the theme's folder in `themes/`. It is the same folder ECHO writes to `ECHO/Themes/`: `theme.json`,
   and any of `Icons/`, `Wallpaper/`, `Fonts/`, `Sounds/`, `Boot/`, `GameStart/`, `README.md` and `Preview/`.
   ECHO's `Themes/Template` names every file a theme can hold.
2. Give it a `README.md` with its details between two `---` lines (author, version, description, tags) and
   a `Preview/hero.jpg`. The store shows both.
3. Open a pull request. The check runs on it; a theme with a file ECHO would not keep fails it.

Check a theme yourself with a checkout of [echo-launcher](https://github.com/Sonophage/echo-launcher):

```sh
python3 tools/check_theme.py ../echo-launcher themes/<Name>
```

Build the site locally:

```sh
python3 tools/build_catalog.py themes dist
```

## The first-party themes

ECHO, PSP, Ryoku and Wild are drawn by `tools/art/build_themes.py` (icons, wallpaper and `theme.json`;
ECHO's sounds too). It needs Pillow, the Noto Serif CJK fonts and an echo-launcher checkout beside this
repo for ECHO's own font:

```sh
python3 tools/art/build_themes.py themes ECHO PSP Ryoku Wild
```

All of their art is original. PSP and Wild are drawn in the spirit of those menus; no Sony or Nintendo
artwork or logos are included.
