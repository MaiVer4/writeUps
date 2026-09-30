import os
import re
import yaml
import shutil
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "dist"
CONFIG_FILE = BASE_DIR / "config.yaml"

def load_config():
    default_config = {
        "title": "Portafolio de Writeups",
        "author": "snicker",
        "handle": "snicker",
        "bio": "Pentesting, resolución de máquinas CTF y notas de seguridad ofensiva.",
        "github": "",
        "linkedin": "",
        "footer_note": "Ciberseguridad · CTF · DockerLabs · HackTheBox"
    }
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)
            if user_config:
                default_config.update(user_config)
    return default_config

def parse_frontmatter(content):
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return meta, body
    return {}, content

def highlight_terminal_line(line):
    # Detect arrow or comment first (before entity escaping)
    comment_part = ""
    # Matches "  <- comment" or "  # comment" at the end of line
    cm_match = re.search(r"(\s+(?:&lt;-|<-|←)\s+.*)$", line)
    if cm_match:
        comment_part = f'<span class="cm">{cm_match.group(1).replace("<-", "←")}</span>'
        line = line[:cm_match.start()]
    
    # Escape HTML
    line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Check for prompts:
    # 1. Standard $ or # prompt: "$ cmd" or "# cmd"
    # 2. Host prompt: "user@host:~$ cmd" or "root@host:~# cmd"
    prompt_match = re.match(r"^(\s*)([a-zA-Z0-9_.\-]+@[a-zA-Z0-9_.\-]+:[^\$#\n]*[\$#]|\$|#)\s+(.*)$", line)
    if prompt_match:
        indent = prompt_match.group(1)
        prompt_symbol = prompt_match.group(2)
        cmd = prompt_match.group(3)
        return f'{indent}<span class="p">{prompt_symbol}</span> <span class="c">{cmd}</span>{comment_part}'
    
    # Highlights: ==highlight==
    line = re.sub(r"(?<![=&])==(?![=&])(.+?)(?<![=&])==(?![=&])", r'<span class="hl">\1</span>', line)
    
    return line + comment_part

def process_terminal_blocks(text):
    # Matches ```bash [label] ... ``` or ```terminal [label] ... ```
    pattern = re.compile(r"```(?:bash|terminal|sh|zsh)?(?:\s*\[(.*?)\])?\n(.*?)```", re.DOTALL)
    
    def repl(m):
        label = m.group(1) or "terminal"
        raw_code = m.group(2)
        lines = raw_code.rstrip().split("\n")
        highlighted_lines = [highlight_terminal_line(l) for l in lines]
        code_html = "\n".join(highlighted_lines)
        
        return f'''<div class="term">
  <div class="term-bar">
    <span class="term-dot"></span>
    <span class="term-dot"></span>
    <span class="term-dot"></span>
    <span class="term-label">{label}</span>
  </div>
  <div class="term-body"><pre>{code_html}</pre></div>
</div>'''

    return pattern.sub(repl, text)

def process_callouts(text):
    # Matches :::callout [label] (cool|warn)? ... :::
    def block_callout(m):
        ctype = m.group(1) or "cool"
        label = m.group(2) or "Nota"
        content = m.group(3).strip()
        paragraphs = "\n".join(f"<p>{p.strip()}</p>" for p in content.split("\n\n") if p.strip())
        return f'''<div class="callout {ctype}">
  <span class="callout-label">{label}</span>
  {paragraphs}
</div>'''

    text = re.compile(r":::callout(?:-(cool|warn))?(?:\s+\[(.*?)\])?\s*\n(.*?)\n:::", re.DOTALL).sub(block_callout, text)
    
    # Also support GitHub style blockquotes:
    # > [!NOTE] Title
    # > Body
    lines = text.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](?:\s+(.*))?$", line, re.IGNORECASE)
        if match:
            kind = match.group(1).upper()
            title = match.group(2) or ("Nota" if kind == "NOTE" else "Aviso")
            ctype = "warn" if kind in ("WARNING", "CAUTION") else "cool"
            callout_lines = []
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                callout_lines.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            body = "\n".join(callout_lines).strip()
            # replace backticks inside callouts
            body = re.sub(r"`([^`]+)`", r"<code>\1</code>", body)
            paras = "\n".join(f"<p>{p.strip()}</p>" for p in body.split("\n\n") if p.strip())
            new_lines.append(f'''<div class="callout {ctype}">
  <span class="callout-label">{title}</span>
  {paras}
</div>''')
        else:
            new_lines.append(line)
            i += 1
    return "\n".join(new_lines)

def process_flags(text):
    # Matches :::flag ... :::
    def flag_repl(m):
        content = m.group(1).strip()
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        msg = lines[0] if lines else "¡Máquina completada!"
        path = lines[1] if len(lines) > 1 else "uid=0(root)"
        return f'''<div class="flag-block">
  <div class="flag-icon">🗝️</div>
  <p class="flag-msg">{msg}</p>
  <div class="flag-path">{path}</div>
</div>'''

    return re.compile(r":::flag\s*\n(.*?)\n:::", re.DOTALL).sub(flag_repl, text)

def process_phases(body):
    sections = re.split(r"\n##\s+", "\n" + body)
    phases_html = []
    
    phase_counter = 1
    
    for idx, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue
        
        # Text before first header
        if idx == 0 and not body.strip().startswith("##"):
            continue
        
        lines = sec.split("\n")
        header_line = lines[0].strip()
        rest_lines = lines[1:]
        
        # Check for {root} modifier in header
        is_root = "{root}" in header_line
        header_line = header_line.replace("{root}", "").strip()
        
        # Header formatting
        phase_num_match = re.match(r"^(Fase\s+\d+.*?):\s*(.*)$", header_line, re.IGNORECASE)
        if phase_num_match:
            phase_num_str = phase_num_match.group(1)
            phase_title = phase_num_match.group(2)
        else:
            phase_num_str = f"Fase {phase_counter} · Final" if is_root else f"Fase {phase_counter}"
            phase_title = header_line
            phase_counter += 1
        
        # Extract subtitle if first non-empty line has '·' or starts with 'sub:'
        phase_sub = ""
        actual_content_lines = []
        found_sub = False
        for l in rest_lines:
            if not found_sub and l.strip():
                stripped = l.strip()
                # Check if line looks like a subtitle: has symbol (· or →) or is a short tagline without a trailing dot
                is_sub = ("·" in stripped or "→" in stripped or "->" in stripped or 
                          stripped.startswith("sub:") or 
                          (len(stripped) < 65 and not stripped.endswith(".") and not stripped.startswith(("$", "#", ">", "`", ":::"))))
                if is_sub:
                    phase_sub = stripped.replace("sub:", "").replace("->", "→").strip()
                    found_sub = True
                    continue
                else:
                    found_sub = True
            actual_content_lines.append(l)
            
        rest = "\n".join(actual_content_lines).strip()
        
        # Process inline markdown elements
        rest = process_callouts(rest)
        rest = process_flags(rest)
        rest = process_terminal_blocks(rest)
        
        # Wrap standalone paragraphs in <p>
        paragraphs = []
        for block in re.split(r"\n\s*\n", rest):
            block = block.strip()
            if not block:
                continue
            if block.startswith("<div") or block.startswith("<table"):
                paragraphs.append(block)
            else:
                block = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", block)
                block = re.sub(r"`([^`]+)`", r"<code>\1</code>", block)
                block = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', block)
                paragraphs.append(f"<p>{block}</p>")
        
        phase_content = "\n".join(paragraphs)
        root_class = " root-phase" if is_root else ""
        sub_html = f'<p class="phase-sub">{phase_sub}</p>' if phase_sub else ''
        
        phase_block = f'''<section class="phase{root_class}">
  <div class="phase-node"><span></span></div>
  <div class="phase-body">
    <div class="phase-num">{phase_num_str}</div>
    <h2 class="phase-title">{phase_title}</h2>
    {sub_html}
    {phase_content}
  </div>
</section>'''
        phases_html.append(phase_block)
        
    return "\n".join(phases_html)

def build_tree_toc(machines, current_slug=None):
    tree_data = {}
    for m in machines:
        plat = m.get("platform", "Otras")
        dif = m.get("difficulty", "Media")
        tree_data.setdefault(plat, {}).setdefault(dif, []).append(m)
        
    html = ['<div class="toc-win"><div class="toc-bar"><span class="term-dot"></span><span class="term-dot"></span><span class="term-dot"></span><span class="toc-title">máquinas</span></div><div class="toc-tree"><a class="toc-home" href="index.html"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10.5 12 3l9 7.5M5 9.5V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.5"/><path d="M9.5 21v-6h5v6"/></svg><span>Portfolio</span></a><ul class="tree">']
    
    dif_classes = {
        "Muy fácil": "dif-muy-facil",
        "Facil": "dif-facil",
        "Fácil": "dif-facil",
        "Medio": "dif-medio",
        "Media": "dif-media",
        "Dificil": "dif-dificil",
        "Difícil": "dif-dificil",
        "Insane": "dif-insane"
    }

    for plat, difs in tree_data.items():
        total_plat_count = sum(len(items) for items in difs.values())
        html.append(f'<li class="tnode tiene-hijos abierto"><button type="button" class="trow trow-plat"><span class="tchev"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></span><span class="tlabel">{plat}</span><span class="tcount">{total_plat_count}</span></button><ul class="tsub">')
        
        for dif, items in difs.items():
            dif_cls = dif_classes.get(dif, "dif-facil")
            html.append(f'<li class="tnode tiene-hijos abierto"><button type="button" class="trow trow-dif"><span class="tchev"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></span><span class="tdot {dif_cls}"></span><span class="tlabel">{dif}</span><span class="tcount">{len(items)}</span></button><ul class="tsub">')
            
            for item in items:
                active_cls = ' activo' if item["slug"] == current_slug else ''
                html.append(f'<li><a class="tleaf{active_cls}" href="{item["slug"]}.html">{item["title"]}</a></li>')
            html.append('</ul></li>')
            
        html.append('</ul></li>')
        
    html.append('</ul></div></div>')
    return "\n".join(html)

def build_writeup_page(meta, body, all_machines, config):
    slug = meta["slug"]
    title = meta.get("title", slug)
    platform = meta.get("platform", "DockerLabs")
    os_name = meta.get("os", "Linux")
    eyebrow = f"{platform} · Máquina {os_name}"
    description = meta.get("description", "")
    ip = meta.get("ip", "")
    services = meta.get("services", "")
    difficulty = meta.get("difficulty", "Media")
    hops = meta.get("hops", "1")
    
    tree_toc = build_tree_toc(all_machines, current_slug=slug)
    phases_html = process_phases(body)
    
    meta_spans = []
    if ip:
        meta_spans.append(f"<span><b>Objetivo</b> {ip}</span>")
    if services:
        meta_spans.append(f"<span><b>Servicios</b> {services}</span>")
    if difficulty:
        meta_spans.append(f"<span><b>Dificultad</b> {difficulty}</span>")
    if hops:
        meta_spans.append(f"<span><b>Saltos de usuario</b> {hops}</span>")
    meta_row_html = "".join(meta_spans)
    
    return f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · {platform}</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <meta name="theme-color" content="#0b0d10">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="stylesheet" href="estilos.css">
</head>
<body>
  <button type="button" class="toc-toggle" aria-label="Abrir índice de máquinas">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
  </button>
  <div class="toc-backdrop"></div>
  <nav class="toc toc-nav" aria-label="Máquinas">
    {tree_toc}
  </nav>

  <div class="wrap">
    <a class="volver" href="index.html">← Portfolio</a>
    <header class="masthead">
      <div class="eyebrow">{eyebrow}</div>
      <h1 class="title">{title}</h1>
      <p class="dek">{description}</p>
      <div class="meta-row">
        {meta_row_html}
      </div>
    </header>

    <div class="report">
      <div class="rail-line"></div>
      {phases_html}
    </div>

    <footer class="site-footer">
      <div class="foot-top">
        <span>{platform} · {title}</span>
        <span class="foot-right">{ip} → uid=0</span>
      </div>
      <div class="foot-bottom">
        <span>© {config['author']}. Todos los derechos reservados.</span>
        <span class="foot-note"><a href="index.html">← Volver al portfolio</a></span>
      </div>
    </footer>
  </div>

  <script src="filtros.js"></script>
</body>
</html>'''

def build_index_page(all_machines, config):
    platforms = sorted(list(set(m.get("platform", "Otras") for m in all_machines)))
    difficulties = sorted(list(set(m.get("difficulty", "Media") for m in all_machines)))
    
    chips = ['<button class="chip activo" data-grupo="todo" data-valor="">Todas</button>']
    for p in platforms:
        chips.append(f'<button class="chip" data-grupo="plataforma" data-valor="{p}">{p}</button>')
    for d in difficulties:
        chips.append(f'<button class="chip" data-grupo="dificultad" data-valor="{d}">{d}</button>')
    chips_html = "".join(chips)
    
    dif_classes = {
        "Muy fácil": "dif-muy-facil",
        "Facil": "dif-facil",
        "Fácil": "dif-facil",
        "Medio": "dif-medio",
        "Media": "dif-media",
        "Dificil": "dif-dificil",
        "Difícil": "dif-dificil",
        "Insane": "dif-insane"
    }

    cards_html = []
    for m in all_machines:
        plat = m.get("platform", "DockerLabs")
        dif = m.get("difficulty", "Media")
        dif_cls = dif_classes.get(dif, "dif-facil")
        slug = m["slug"]
        title = m.get("title", slug)
        desc = m.get("description", "")
        ip = m.get("ip", "")
        tags = m.get("tags", [])
        
        tags_spans = "".join(f'<span class="tag">{t}</span>' for t in tags)
        
        card = f'''<a class="card" href="{slug}.html" data-plataforma="{plat}" data-dificultad="{dif}">
  <div class="card-top">
    <span class="badge badge-plat">{plat}</span>
    <span class="badge dif {dif_cls}">{dif}</span>
  </div>
  <h3 class="card-title">{title}</h3>
  <p class="card-dek">{desc}</p>
  <div class="tags">{tags_spans}</div>
  <div class="card-foot">
    <span>{ip}</span>
    <span class="card-go">leer →</span>
  </div>
</a>'''
        cards_html.append(card)
        
    cards_grid = "\n".join(cards_html)
    
    github_link = f'<a href="{config["github"]}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 19c-4 1.5-4-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 00-1.3-3.2 4.2 4.2 0 00-.1-3.2s-1.1-.3-3.5 1.3a12 12 0 00-6.4 0C6.3 2.8 5.2 3.1 5.2 3.1a4.2 4.2 0 00-.1 3.2A4.6 4.6 0 003.8 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/></svg><span>GitHub</span></a>' if config.get("github") else ""
    
    linkedin_link = f'<a href="{config["linkedin"]}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h4v11H4zM6 4a2 2 0 110 4 2 2 0 010-4zM10 9h4v1.5c.6-1 1.8-1.8 3.5-1.8C20 8.7 22 10.5 22 14v6h-4v-5.5c0-1.5-.5-2.5-2-2.5s-2.3 1-2.3 2.6V20H10z"/></svg><span>LinkedIn</span></a>' if config.get("linkedin") else ""
    
    return f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{config['title']} · {config['handle']}</title>
  <meta name="description" content="{config['bio']}">
  <meta name="theme-color" content="#0b0d10">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="stylesheet" href="estilos.css">
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <div class="eyebrow">PORTAFOLIO DE WRITEUPS · CTF</div>
      <h1 class="title">{config['author']} <span class="handle">@{config['handle']}</span></h1>
      <p class="dek">{config['bio']}</p>
      <div class="links">
        {github_link}
        {linkedin_link}
      </div>
      <div class="stats">
        <span><b>{len(all_machines)}</b> máquinas resueltas</span>
        <span><b>{len(platforms)}</b> plataformas</span>
      </div>
    </header>

    <section class="cv-section" id="writeups">
      <h2 class="sec-title">Writeups</h2>
      <div class="filtros">
        {chips_html}
      </div>
      <div class="grid">
        {cards_grid}
      </div>
    </section>

    <footer class="site-footer">
      <div class="foot-top">
        <div class="foot-brand">
          <span class="foot-name">{config['author']}</span>
          <span class="foot-handle">@{config['handle']}</span>
          <span class="foot-tag">{config['bio']}</span>
        </div>
        <div class="foot-links">
          {github_link}
          {linkedin_link}
        </div>
      </div>
      <div class="foot-bottom">
        <span>© {config['author']}. Todos los derechos reservados.</span>
        <span class="foot-note">{config['footer_note']}</span>
      </div>
    </footer>
  </div>

  <script src="filtros.js"></script>
</body>
</html>'''

def main():
    config = load_config()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    
    # 1. Copy static files to dist
    for item in STATIC_DIR.glob("*"):
        if item.is_file():
            shutil.copy(item, OUTPUT_DIR / item.name)
            
    # 2. Parse all markdown files
    all_machines = []
    parsed_files = []
    
    for md_file in sorted(CONTENT_DIR.glob("*.md")):
        if md_file.name.startswith("_") or md_file.name.startswith("."):
            continue
        with open(md_file, "r", encoding="utf-8") as f:
            raw = f.read()
        meta, body = parse_frontmatter(raw)
        slug = md_file.stem
        meta["slug"] = slug
        if "title" not in meta:
            meta["title"] = slug.replace("-", " ").title()
        all_machines.append(meta)
        parsed_files.append((meta, body))
        
    print(f"[*] Encontradas {len(all_machines)} máquinas en {CONTENT_DIR}")
    
    # 3. Generate writeup HTML for each machine
    for meta, body in parsed_files:
        html = build_writeup_page(meta, body, all_machines, config)
        out_file = OUTPUT_DIR / f"{meta['slug']}.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [+] Generado writeup: {out_file.name}")
        
    # 4. Generate index.html
    index_html = build_index_page(all_machines, config)
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  [+] Generado index: index.html")
    print(f"[✓] Construcción completada en {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
