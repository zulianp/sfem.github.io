#!/usr/bin/env python3

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def render_inline(text: str) -> str:
    placeholders = []

    def stash(pattern, value):
        token = f"@@PLACEHOLDER_{len(placeholders)}@@"
        placeholders.append(value)
        return token

    text = re.sub(r"`([^`]+)`", lambda m: stash(m.group(0), f"<code>{html.escape(m.group(1))}</code>"), text)
    text = html.escape(text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" />', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    for i, value in enumerate(placeholders):
        text = text.replace(html.escape(f"@@PLACEHOLDER_{i}@@"), value)
    return text


def render_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    blocks = []
    paragraph = []
    in_list = False
    in_code = False
    code_lang = ""
    code_lines = []
    in_math = False
    math_lines = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            blocks.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list():
        nonlocal in_list
        if in_list:
            blocks.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()

        if in_code:
            if line.startswith("```"):
                if code_lang == "mermaid":
                    blocks.append('<div class="mermaid">\n' + "\n".join(code_lines) + "\n</div>")
                else:
                    blocks.append(
                        f'<pre><code class="language-{html.escape(code_lang)}">'
                        + html.escape("\n".join(code_lines))
                        + "</code></pre>"
                    )
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                code_lines.append(raw)
            continue

        if in_math:
            math_lines.append(raw)
            if line == "$$":
                blocks.append('<div class="math-block">' + "\n".join(math_lines) + "</div>")
                in_math = False
                math_lines = []
            continue

        if line.startswith("```"):
            flush_paragraph()
            close_list()
            in_code = True
            code_lang = line[3:].strip()
            code_lines = []
            continue

        if line == "$$":
            flush_paragraph()
            close_list()
            in_math = True
            math_lines = [raw]
            continue

        if not line:
            flush_paragraph()
            close_list()
            continue

        if line.startswith("<") and line.endswith(">"):
            flush_paragraph()
            close_list()
            blocks.append(line)
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            text = render_inline(heading.group(2))
            slug = re.sub(r"[^a-z0-9]+", "-", heading.group(2).lower()).strip("-")
            blocks.append(f'<h{level} id="{slug}">{text}</h{level}>')
            continue

        if line.startswith("- "):
            flush_paragraph()
            if not in_list:
                blocks.append("<ul>")
                in_list = True
            blocks.append(f"<li>{render_inline(line[2:])}</li>")
            continue

        paragraph.append(line)

    flush_paragraph()
    close_list()
    return "\n".join(blocks)


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <script>
      window.MathJax = {{
        tex: {{ inlineMath: [["\\\\(", "\\\\)"]], displayMath: [["$$", "$$"]] }},
        svg: {{ fontCache: "global" }}
      }};
    </script>
    <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
      mermaid.initialize({{ startOnLoad: true, theme: "neutral" }});
    </script>
    <style>
      :root {{
        color-scheme: light;
        --ink: #18212f;
        --muted: #596679;
        --line: #d7dee8;
        --accent: #0b6bcb;
        --accent-soft: #e8f2ff;
        --surface: #f7f9fc;
        --white: #ffffff;
      }}

      * {{ box-sizing: border-box; }}

      body {{
        margin: 0;
        min-height: 100vh;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ink);
        background: var(--surface);
      }}

      main {{
        width: min(1040px, calc(100% - 40px));
        margin: 0 auto;
        padding: 56px 0 64px;
      }}

      .eyebrow {{
        color: var(--accent);
        font-size: 13px;
        font-weight: 760;
        letter-spacing: .03em;
        text-transform: uppercase;
      }}

      h1 {{
        max-width: 900px;
        margin: 10px 0 16px;
        font-size: clamp(36px, 6vw, 64px);
        line-height: 1.02;
        letter-spacing: 0;
      }}

      h2 {{
        margin: 48px 0 14px;
        padding-top: 18px;
        border-top: 1px solid var(--line);
        font-size: 25px;
        letter-spacing: 0;
      }}

      h3 {{
        margin: 30px 0 10px;
        font-size: 18px;
        letter-spacing: 0;
      }}

      p, li {{
        color: var(--muted);
        font-size: 16px;
        line-height: 1.68;
      }}

      p {{
        max-width: 860px;
        margin: 0 0 14px;
      }}

      ul {{
        margin: 8px 0 18px;
        padding-left: 22px;
      }}

      strong {{ color: var(--ink); }}

      a {{
        color: var(--accent);
        text-decoration-thickness: 1px;
        text-underline-offset: 3px;
      }}

      code {{
        padding: 0.12rem 0.28rem;
        border: 1px solid var(--line);
        border-radius: 5px;
        color: var(--ink);
        background: var(--white);
        font-size: 0.92em;
      }}

      pre {{
        overflow: auto;
        padding: 16px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--white);
      }}

      pre code {{
        padding: 0;
        border: 0;
        background: transparent;
      }}

      img {{
        display: block;
        width: min(100%, 820px);
        height: auto;
        margin: 16px 0 22px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--white);
      }}

      .math-block {{
        overflow-x: auto;
        margin: 14px 0 18px;
        padding: 12px 16px;
        border-left: 4px solid var(--accent);
        background: var(--accent-soft);
      }}

      .mermaid {{
        width: min(100%, 820px);
        margin: 18px 0 22px;
        padding: 14px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--white);
      }}

      @media (max-width: 760px) {{
        main {{
          width: min(100% - 28px, 1040px);
          padding-top: 36px;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      {body}
    </main>
  </body>
</html>
"""


def main():
    source = ROOT / "index.md"
    text = source.read_text()
    title = "Mooney-Rivlin Kelvin-Voigt Newmark Validation"
    body = render_markdown(text)
    (ROOT / "index.html").write_text(page(title, body))


if __name__ == "__main__":
    main()
