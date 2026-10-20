(() => {
  const doc = document.documentElement;
  doc.classList.add('js');

  // Header: solid background after scrolling
  const header = document.querySelector('[data-header]');
  const onScroll = () => header && header.classList.toggle('is-solid', window.scrollY > 40);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Mobile menu
  const menuBtn = document.querySelector('[data-menu]');
  if (menuBtn) {
    menuBtn.addEventListener('click', () => {
      const open = document.body.classList.toggle('menu-open');
      menuBtn.setAttribute('aria-expanded', open);
      menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
  }
  document.querySelectorAll('.sub-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const li = btn.closest('.has-sub');
      const open = li.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', open);
    });
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && document.body.classList.contains('menu-open')) menuBtn.click();
  });

  // Scroll reveal
  const items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(el => io.observe(el));
  } else {
    items.forEach(el => el.classList.add('is-in'));
  }

  // Gentle parallax on hero backgrounds
  const layers = document.querySelectorAll('.hero__bg, .page-hero__bg, .book-hero__bg');
  if (layers.length && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    let ticking = false;
    const update = () => {
      const y = window.scrollY;
      layers.forEach(l => { if (y < 1200) l.style.setProperty('--parallax', (y * 0.22).toFixed(1) + 'px'); });
      ticking = false;
    };
    window.addEventListener('scroll', () => { if (!ticking) { requestAnimationFrame(update); ticking = true; } }, { passive: true });
  }

  // Lightbox for award certificates and the gala gallery
  const lb = document.querySelector('[data-lightbox]');
  const zoomables = [...document.querySelectorAll('[data-zoom]')];
  if (lb && zoomables.length) {
    const lbImg = lb.querySelector('img');
    const lbCap = lb.querySelector('figcaption');
    let idx = 0, lastFocus = null;
    const show = i => {
      idx = (i + zoomables.length) % zoomables.length;
      const el = zoomables[idx];
      lbImg.src = el.dataset.zoom;
      const alt = el.dataset.caption || (el.querySelector('img') || {}).alt || '';
      lbImg.alt = alt;
      lbCap.textContent = alt;
    };
    const open = i => { lastFocus = document.activeElement; show(i); lb.hidden = false; document.body.style.overflow = 'hidden'; lb.querySelector('.lightbox__close').focus(); };
    const close = () => { lb.hidden = true; document.body.style.overflow = ''; if (lastFocus) lastFocus.focus(); };
    zoomables.forEach((el, i) => el.addEventListener('click', () => open(i)));
    lb.querySelector('.lightbox__close').addEventListener('click', close);
    lb.querySelector('.lightbox__prev').addEventListener('click', () => show(idx - 1));
    lb.querySelector('.lightbox__next').addEventListener('click', () => show(idx + 1));
    lb.addEventListener('click', e => { if (e.target === lb) close(); });
    document.addEventListener('keydown', e => {
      if (lb.hidden) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'ArrowRight') show(idx + 1);
    });
  }

  // Forms (FormSubmit AJAX)
  document.querySelectorAll('form[data-form]').forEach(form => {
    const note = form.querySelector('.form-note');
    const btn = form.querySelector('button[type=submit]');
    const defaultNote = note ? note.textContent : '';
    form.addEventListener('submit', async e => {
      e.preventDefault();
      let valid = true;
      form.querySelectorAll('[required]').forEach(f => {
        const bad = !f.value.trim() || (f.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.value));
        f.classList.toggle('is-invalid', bad);
        if (bad) valid = false;
      });
      if (!valid) {
        note.className = 'form-note err';
        note.textContent = 'Please fill in the required fields with a valid email address.';
        return;
      }
      btn.disabled = true;
      note.className = 'form-note';
      note.textContent = 'Sending…';
      try {
        const res = await fetch(form.action, { method: 'POST', headers: { Accept: 'application/json' }, body: new FormData(form) });
        if (!res.ok) throw new Error(res.status);
        form.reset();
        note.className = 'form-note ok';
        note.textContent = form.dataset.form === 'newsletter' ? 'Thank you! You’re on the list.' : 'Thank you! Your message has been sent.';
      } catch (err) {
        note.className = 'form-note err';
        note.textContent = 'Something went wrong. Please email breetwilson25@gmail.com instead.';
      } finally {
        btn.disabled = false;
        setTimeout(() => { if (note.classList.contains('ok')) { note.className = 'form-note'; note.textContent = defaultNote; } }, 8000);
      }
    });
  });
})();
