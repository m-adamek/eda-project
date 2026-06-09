import scrapy
import pathlib
import re

scrapy_dir = pathlib.Path(scrapy.__file__).parent
print("Scrapy dir:", scrapy_dir)

matches = []
for p in scrapy_dir.rglob("*.py"):
    try:
        content = p.read_text(encoding="utf-8")
        if "start_requests" in content:
            matches.append(p)
    except Exception:
        pass

print(f"Found {len(matches)} files referencing 'start_requests':")
for m in matches[:10]:
    print(" -", m.relative_to(scrapy_dir.parent))
