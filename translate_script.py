#!/usr/bin/env python3
"""
Translation workflow helper for Jambo.

Run this every time you add or change a translatable string ( _('...') in
Python, {{ _('...') }} in templates ) anywhere in the app.

Usage:
    python translate.py

What it does, in order:
    1. Extract every translatable string in the app into messages.pot
    2. Merge new/changed strings into app/translations/<lang>/LC_MESSAGES/messages.po
       (existing translations are preserved -- this never overwrites them)
    3. Pause and tell you exactly how many entries still need a human
       translation, so you know what to open and fill in
    4. Wait for you to confirm you're done editing the .po file
    5. Compile to the .mo file Flask-Babel actually reads at runtime
    6. Remind you to restart the Flask app

Run this from the project root (same folder as babel.cfg).
"""

import subprocess
import sys
import re
from pathlib import Path

# Add another language code here later if the app ever supports more
# than English/French (e.g. "pt" for Portuguese-speaking markets).
LANGUAGES = ["fr"]

PROJECT_ROOT = Path(__file__).resolve().parent
BABEL_CFG = PROJECT_ROOT / "babel.cfg"
POT_FILE = PROJECT_ROOT / "messages.pot"
TRANSLATIONS_DIR = PROJECT_ROOT / "app" / "translations"


def run(cmd, description):
    print(f"\n---- {description} ----")
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        print("Fix the error above before continuing.")
        sys.exit(1)


def count_untranslated(po_path):
    """Counts empty msgstr "" entries and #, fuzzy entries in a .po file,
    so the user knows exactly how much manual work is left before
    compiling. Doesn't need a real .po parser for this -- both patterns
    are simple enough to catch with a couple of regexes."""
    if not po_path.exists():
        return None, None

    content = po_path.read_text(encoding="utf-8")
    empty = len(re.findall(r'msgstr ""\s*\n(?!\S)', content))
    fuzzy = len(re.findall(r'#, fuzzy', content))
    return empty, fuzzy


def main():
    if not BABEL_CFG.exists():
        print(f"❌ Could not find babel.cfg at {BABEL_CFG}")
        print("Run this script from your project root.")
        sys.exit(1)

    # Step 1: extract
    run(
        ["pybabel", "extract", "-F", str(BABEL_CFG), "-o", str(POT_FILE), "."],
        "Extracting translatable strings"
    )

    # Step 2: update each language's .po file
    for lang in LANGUAGES:
        run(
            ["pybabel", "update", "-i", str(POT_FILE), "-d", str(TRANSLATIONS_DIR), "-l", lang],
            f"Merging into {lang} translation file"
        )

    # Step 3: report what needs manual attention
    print("\n" + "=" * 60)
    for lang in LANGUAGES:
        po_path = TRANSLATIONS_DIR / lang / "LC_MESSAGES" / "messages.po"
        empty, fuzzy = count_untranslated(po_path)
        if empty is None:
            print(f"⚠️  Couldn't find {po_path}")
            continue
        print(f"[{lang}] {empty} untranslated, {fuzzy} marked 'fuzzy' (needs review)")
        print(f"     -> {po_path}")
    print("=" * 60)

    if all(count_untranslated(TRANSLATIONS_DIR / l / "LC_MESSAGES" / "messages.po")[0] == 0
           and count_untranslated(TRANSLATIONS_DIR / l / "LC_MESSAGES" / "messages.po")[1] == 0
           for l in LANGUAGES):
        print("\n✅ Nothing new to translate -- skipping straight to compile.")
    else:
        print("\nOpen the .po file(s) above, fill in the empty msgstr \"\" entries,")
        print("and review/fix anything marked '#, fuzzy' (then delete that line).")
        input("\nPress Enter once you've saved your changes, to compile...")

    # Step 4: compile
    run(
        ["pybabel", "compile", "-d", str(TRANSLATIONS_DIR)],
        "Compiling to .mo"
    )

    print("\n✅ Done. Restart your Flask app to pick up the changes.")


if __name__ == "__main__":
    main()