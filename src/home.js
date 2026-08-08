/**
 * ShemaProject — Home page interactions
 * Navbar, scroll reveal, solutions accordion, demo
 */

(function () {
    "use strict";

    /* ── Navbar scroll shadow ── */
    var navbar = document.getElementById('navbar');
    window.addEventListener('scroll', function () {
        if (window.scrollY > 10) navbar.classList.add('scrolled');
        else navbar.classList.remove('scrolled');
    });

    /* ── Mobile burger ── */
    var burger = document.getElementById('burgerBtn');
    var nav = document.getElementById('navbarNav');
    if (burger) burger.addEventListener('click', function () { nav.classList.toggle('open'); });

    /* ── Footer year ── */
    var yearEl = document.getElementById('footerYear');
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    /* ── Solutions accordion (like SO) ── */
    var solutions = document.querySelectorAll('.solution');
    solutions.forEach(function (sol) {
        var header = sol.querySelector('.solution__header');
        if (!header) return;
        header.addEventListener('click', function () {
            // Deactivate all
            solutions.forEach(function (s) {
                s.classList.remove('solution--active');
                var sub = s.querySelector('.solution__subhead');
                var stat = s.querySelector('.solution__stat');
                var chev = s.querySelector('.solution__chevron');
                if (sub) sub.classList.add('solution__subhead--hidden');
                if (stat) stat.classList.add('solution__stat--hidden');
                if (chev) chev.style.transform = 'rotate(0deg)';
            });
            // Activate clicked
            sol.classList.add('solution--active');
            var sub = sol.querySelector('.solution__subhead');
            var stat = sol.querySelector('.solution__stat');
            var chev = sol.querySelector('.solution__chevron');
            if (sub) sub.classList.remove('solution__subhead--hidden');
            if (stat) stat.classList.remove('solution__stat--hidden');
            if (chev) chev.style.transform = 'rotate(-180deg)';
        });
    });

    /* ── Scroll reveal ── */
    var revealEls = document.querySelectorAll(
        '.hero__inner, .stat, .products__headline, .product-card, .subfeature, ' +
        '.other-ways__card, .mission__headline, .solution, .article-card, .demo__inner'
    );
    revealEls.forEach(function (el) { el.classList.add('reveal'); });

    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
        revealEls.forEach(function (el) { io.observe(el); });
    } else {
        revealEls.forEach(function (el) { el.classList.add('visible'); });
    }

    /* ── Demo chips ── */
    var chips = document.querySelectorAll('.demo__chip');
    var refInput = document.getElementById('reference');
    var fetchBtn = document.getElementById('fetchBtn');
    chips.forEach(function (chip) {
        chip.addEventListener('click', function () {
            if (refInput) {
                refInput.value = chip.getAttribute('data-ref');
                if (fetchBtn) fetchBtn.click();
            }
        });
    });

    /* ── Demo fetch ── */
    var resultEl = document.getElementById('result');
    var statusEl = document.getElementById('resultStatus');
    if (fetchBtn && resultEl) {
        fetchBtn.addEventListener('click', async function () {
            var ref = refInput ? refInput.value.trim() : '';
            if (!ref) {
                if (statusEl) { statusEl.textContent = '⚠ vide'; statusEl.className = 'demo__result-status err'; }
                return;
            }
            resultEl.textContent = '⏳ Chargement…';
            if (statusEl) { statusEl.textContent = ''; statusEl.className = 'demo__result-status'; }
            try {
                var parsedRef = (typeof parseReference === 'function') ? parseReference(ref) : ref;
                var urlPath = parsedRef.split('/').map(encodeURIComponent).join('/');
                var response = await fetch('/bym/' + urlPath);
                if (!response.ok) throw new Error('HTTP ' + response.status);
                var data = await response.json();
                resultEl.textContent = JSON.stringify(data, null, 2);
                if (statusEl) { statusEl.textContent = '✓ ' + response.status; statusEl.className = 'demo__result-status ok'; }
            } catch (e) {
                resultEl.textContent = 'Erreur : impossible de récupérer le verset.\n' + e.message;
                if (statusEl) { statusEl.textContent = '✗ erreur'; statusEl.className = 'demo__result-status err'; }
            }
        });
    }

    /* ── Enter key ── */
    if (refInput && fetchBtn) {
        refInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') fetchBtn.click();
        });
    }
})();