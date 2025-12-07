# export_script.py
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "project_export.txt")

# Ignore list
IGNORE_DIRS = {
    "venv", ".venv",
    "__pycache__", ".git", ".idea",
    ".mypy_cache", ".pytest_cache",
    "build", "dist"
}

# Add new non-Python extensions here
EXPORT_EXTENSIONS = {".py", ".json"}

VERSION_TAG = "PROJECT_EXPORT_v1.4"

# Optional clipboard support
try:
    import pyperclip  # noqa: F401
    _HAS_PYPERCLIP = True
except Exception:
    _HAS_PYPERCLIP = False


def is_ignored_dir(dirname: str) -> bool:
    return dirname.lower() in IGNORE_DIRS


def collect_files(root: str):
    """Collect python + json files."""
    collected = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not is_ignored_dir(d)]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in EXPORT_EXTENSIONS:
                full = os.path.join(dirpath, filename)
                rel = os.path.relpath(full, root)
                collected.append((rel, full))

    # deterministic ordering
    collected.sort(key=lambda x: (x[0].count(os.sep), x[0]))
    return collected


def compress_blank_lines(text: str) -> str:
    """Remove 2+ consecutive blank lines, reduce to max 1."""
    return re.sub(r"\n{2,}", "\n", text)


def build_table_of_contents(files):
    lines = [
        f"# === PROJECT TABLE OF CONTENTS ({len(files)} files) ===",
        f"# Version: {VERSION_TAG}",
        ""
    ]
    for path, _ in files:
        lines.append(f"#  - {path}")
    lines.append("")
    return "\n".join(lines)


def build_file_section(rel_path: str, full_path: str) -> str:
    """Read a file and wrap it."""
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            code = f.read()
    except UnicodeDecodeError:
        code = "<Error reading file: non-UTF8 encoding>"

    code = compress_blank_lines(code)

    ext = os.path.splitext(rel_path)[1].lower()
    fence = "python" if ext == ".py" else "json" if ext == ".json" else ""

    return (
        f"# === FILE START: {rel_path} ===\n"
        f"```{fence}\n{code}\n```\n"
        f"# === FILE END: {rel_path} ===\n"
    )


def main():
    files = collect_files(PROJECT_ROOT)
    if not files:
        print("No files found.")
        return

    toc = build_table_of_contents(files)
    sections = [toc]

    for rel_path, full_path in files:
        sections.append(build_file_section(rel_path, full_path))

    final_text = "\n\n".join(sections)
    final_text = compress_blank_lines(final_text)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(final_text)

    # Clipboard copy happens *after* final_text exists, and only if available.
    if _HAS_PYPERCLIP:
        try:
            import pyperclip
            pyperclip.copy(final_text)
            print(f"Copied to clipboard ✓ ({VERSION_TAG})")
        except Exception as exc:
            print(f"⚠ Failed to copy to clipboard: {exc}")
    else:
        print("⚠ pyperclip not available; skipped clipboard copy.")

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"Export complete: {len(files)} files, {size_kb:.1f} KB")
    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
