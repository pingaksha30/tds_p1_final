# generator.py
import os, base64, re
from pathlib import Path

# pattern to decode data URLs like data:image/png;base64,xxxx
DATA_URI_RE = re.compile(r"data:(?P<mime>[\w/-]+);base64,(?P<data>.+)")

def save_attachments(attachments, outdir):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    saved = []
    for att in attachments or []:
        name = att.get("name", "attachment.bin")
        url = att.get("url", "")
        m = DATA_URI_RE.match(url)
        if m:
            data = base64.b64decode(m.group("data"))
            p = Path(outdir) / name
            p.write_bytes(data)
            saved.append(str(p.name))
    return saved

def generate_minimal_app(task, brief, attachments, outdir):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    saved_files = save_attachments(attachments, outdir)

    index_html = f"""<!doctype html>
<html>
  <head><meta charset="utf-8"><title>{task}</title></head>
  <body>
    <h1>{task}</h1>
    <p id="brief">{brief}</p>
    <div id="content">Loading...</div>
    <script>
      const params = new URLSearchParams(location.search);
      const url = params.get("url");
      if (url) {{
        document.getElementById("content").textContent = 'URL: ' + url;
      }} else {{
        document.getElementById("content").textContent = 'No ?url provided — using default attachment.';
      }}
    </script>
  </body>
</html>"""
    (Path(outdir) / "index.html").write_text(index_html, encoding="utf-8")

    (Path(outdir) / "README.md").write_text(f"# {task}\n\n{brief}\n", encoding="utf-8")
    (Path(outdir) / "LICENSE").write_text("MIT License\n\nCopyright (c) YEAR\n", encoding="utf-8")

    return {"files": ["index.html", "README.md", "LICENSE"] + saved_files}
