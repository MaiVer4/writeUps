// Filtros del índice — vanilla JS, progresivo (sin JS se ven todas las tarjetas).
(function () {
  const chips = Array.from(document.querySelectorAll('.chip'));
  const cards = Array.from(document.querySelectorAll('.card'));
  if (!chips.length) return;

  let filtro = { grupo: 'todo', valor: '' };

  function aplicar() {
    cards.forEach((c) => {
      let visible = true;
      if (filtro.grupo === 'plataforma') visible = c.dataset.plataforma === filtro.valor;
      else if (filtro.grupo === 'dificultad') visible = c.dataset.dificultad === filtro.valor;
      c.classList.toggle('oculta', !visible);
    });
  }

  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      chips.forEach((c) => c.classList.remove('activo'));
      chip.classList.add('activo');
      filtro = { grupo: chip.dataset.grupo, valor: chip.dataset.valor };
      aplicar();
    });
  });
})();

// --- Panel del índice: abrir/cerrar + desplegables (portada y writeups) ---
(function () {
  const toc = document.querySelector('.toc');
  if (!toc) return;
  const toggle = document.querySelector('.toc-toggle');
  const backdrop = document.querySelector('.toc-backdrop');
  const cerrar = () => { toc.classList.remove('abierta'); if (backdrop) backdrop.classList.remove('visible'); };
  const abrir = () => { toc.classList.add('abierta'); if (backdrop) backdrop.classList.add('visible'); };
  if (toggle) toggle.addEventListener('click', () => (toc.classList.contains('abierta') ? cerrar() : abrir()));
  if (backdrop) backdrop.addEventListener('click', cerrar);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') cerrar(); });

  // Desplegables del índice de secciones (chevron, portada)
  document.querySelectorAll('.toc-chevron').forEach((ch) => {
    ch.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const it = ch.closest('.toc-item');
      if (it) it.classList.toggle('abierto');
    });
  });

  // Desplegables del árbol de máquinas (writeups)
  document.querySelectorAll('.trow').forEach((r) => {
    if (r.classList.contains('disabled')) return;
    r.addEventListener('click', () => {
      const n = r.closest('.tnode');
      if (n) n.classList.toggle('abierto');
    });
  });

  // En modo panel, cerrar al elegir un destino
  toc.querySelectorAll('a[href]').forEach((a) =>
    a.addEventListener('click', () => { if (window.innerWidth < 1240) cerrar(); }));
})();

// --- Scroll-spy + progreso (solo en la portada, con secciones) ---
(function () {
  const items = Array.from(document.querySelectorAll('.toc-item'));
  if (!items.length) return;
  const secciones = items.map((it) => document.getElementById(it.dataset.sec)).filter(Boolean);
  if (!secciones.length) return;

  function activar(id) {
    items.forEach((it) => {
      const on = it.dataset.sec === id;
      it.classList.toggle('activo', on);
      if (it.classList.contains('tiene-hijos')) it.classList.toggle('abierto', on);
    });
  }
  function actualizarActiva() {
    const linea = window.scrollY + Math.min(170, window.innerHeight * 0.28);
    let actual = secciones[0].id;
    secciones.forEach((s) => {
      const top = s.getBoundingClientRect().top + window.scrollY;
      if (top <= linea) actual = s.id;
    });
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) {
      actual = secciones[secciones.length - 1].id;
    }
    activar(actual);
  }
  const fill = document.querySelector('.toc-progress-fill');
  function progreso() {
    const h = document.documentElement.scrollHeight - window.innerHeight;
    const p = h > 0 ? (window.scrollY / h) * 100 : 0;
    if (fill) fill.style.width = Math.max(0, Math.min(100, p)) + '%';
  }
  window.addEventListener('scroll', () => { actualizarActiva(); progreso(); }, { passive: true });
  window.addEventListener('resize', () => { actualizarActiva(); progreso(); });
  actualizarActiva();
  progreso();
})();

// --- Popup de herramientas (mini-terminal) ---
(function () {
  const tools = Array.from(document.querySelectorAll('.tool-btn'));
  if (!tools.length) return;

  const escHTML = (s) =>
    String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  const backdrop = document.createElement('div');
  backdrop.className = 'tool-pop-backdrop';

  const pop = document.createElement('div');
  pop.className = 'tool-pop';
  pop.setAttribute('role', 'dialog');
  pop.innerHTML =
    '<div class="term-bar">' +
    '<span class="term-dot"></span><span class="term-dot"></span><span class="term-dot"></span>' +
    '<span class="term-label" id="tp-name"></span>' +
    '<button type="button" class="tp-close" aria-label="Cerrar">&times;</button>' +
    '</div>' +
    '<div class="term-body"><pre><span class="p">$</span> <span class="c">whatis <span id="tp-cmd"></span></span>\n' +
    '<span id="tp-desc"></span></pre></div>';

  document.body.appendChild(backdrop);
  document.body.appendChild(pop);

  const elName = pop.querySelector('#tp-name');
  const elCmd = pop.querySelector('#tp-cmd');
  const elDesc = pop.querySelector('#tp-desc');
  let abierto = null;

  function cerrar() {
    pop.classList.remove('visible');
    backdrop.classList.remove('visible');
    abierto = null;
  }

  function abrir(btn) {
    const nombre = btn.dataset.nombre || '';
    elName.textContent = nombre;
    elCmd.textContent = nombre;
    elDesc.innerHTML = escHTML(btn.dataset.desc || '');

    // Mostrar primero (para medir), luego posicionar
    pop.classList.add('visible');
    backdrop.classList.add('visible');

    const r = btn.getBoundingClientRect();
    const pr = pop.getBoundingClientRect();
    const margen = 10;
    let left = r.left;
    let top = r.bottom + 8;
    // Clamp horizontal dentro del viewport
    if (left + pr.width > window.innerWidth - margen) {
      left = Math.max(margen, window.innerWidth - pr.width - margen);
    }
    left = Math.max(margen, left);
    // Si no cabe debajo, colócalo encima
    if (top + pr.height > window.innerHeight - margen) {
      top = Math.max(margen, r.top - pr.height - 8);
    }
    pop.style.left = left + 'px';
    pop.style.top = top + 'px';
    abierto = btn;
  }

  tools.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (abierto === btn) cerrar();
      else abrir(btn);
    });
  });

  backdrop.addEventListener('click', cerrar);
  pop.querySelector('.tp-close').addEventListener('click', cerrar);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') cerrar(); });
  window.addEventListener('resize', cerrar);
  window.addEventListener('scroll', cerrar, true);
})();
