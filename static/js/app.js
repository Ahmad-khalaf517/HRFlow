/* Small progressive enhancements for Django's server-rendered forms and navigation. */
(() => {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const openButton = document.getElementById('sidebar-open');
    const closeButton = document.getElementById('sidebar-close');
    const collapseButton = document.getElementById('sidebar-collapse');
    const shell = document.getElementById('app-shell');
    const desktop = window.matchMedia('(min-width: 768px)');
    let mobileOpen = false;

    function setMobileOpen(open, restoreFocus = false) {
        if (!sidebar) return;
        mobileOpen = open && !desktop.matches;
        sidebar.classList.toggle('-translate-x-full', !mobileOpen);
        sidebar.classList.toggle('translate-x-0', mobileOpen);
        sidebar.inert = !desktop.matches && !mobileOpen;
        overlay?.classList.toggle('hidden', !mobileOpen);
        openButton?.setAttribute('aria-expanded', String(mobileOpen));
        shell.inert = mobileOpen;
        document.body.classList.toggle('menu-open', mobileOpen);
        if (mobileOpen) closeButton?.focus();
        else if (restoreFocus) openButton?.focus();
    }
    openButton?.addEventListener('click', () => setMobileOpen(true));
    closeButton?.addEventListener('click', () => setMobileOpen(false, true));
    overlay?.addEventListener('click', () => setMobileOpen(false, true));
    collapseButton?.addEventListener('click', () => {
        const collapsed = document.body.classList.toggle('sidebar-collapsed');
        collapseButton.setAttribute('aria-expanded', String(!collapsed));
        collapseButton.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
    });
    document.querySelectorAll('.sidebar-link').forEach(link => {
        const label = link.textContent.trim();
        link.setAttribute('aria-label', label);
        link.setAttribute('title', label);
        if (link.classList.contains('font-semibold')) link.setAttribute('aria-current', 'page');
    });
    document.addEventListener('keydown', event => {
        if (!mobileOpen) return;
        if (event.key === 'Escape') setMobileOpen(false, true);
        if (event.key !== 'Tab') return;
        const focusable = [...sidebar.querySelectorAll('a[href], button:not([disabled])')]
            .filter(element => element.getClientRects().length);
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault(); last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault(); first?.focus();
        }
    });
    desktop.addEventListener('change', () => setMobileOpen(false));
    setMobileOpen(false);

    // Feedback persists until dismissed, including errors and slow-to-read messages.
    document.querySelectorAll('.toast-close').forEach(button => {
        button.addEventListener('click', () => button.closest('[data-message]').remove());
    });
    document.querySelector('.form-error-summary')?.focus();

    // Keep the page intact while navigating, so Back restores usable content.
    const submitted = new Map();
    document.addEventListener('submit', event => {
        const form = event.target;
        if (event.defaultPrevented || form.method === 'dialog') return;
        if (submitted.has(form)) { event.preventDefault(); return; }
        const button = event.submitter;
        if (!button) return;
        const original = {button, text: button.textContent, disabled: button.disabled, hidden: null};
        // Disabled submitters are omitted by browsers; preserve their action value.
        if (button.name) {
            original.hidden = document.createElement('input');
            original.hidden.type = 'hidden';
            original.hidden.name = button.name;
            original.hidden.value = button.value;
            form.append(original.hidden);
        }
        submitted.set(form, original);
        form.setAttribute('aria-busy', 'true');
        button.disabled = true;
        button.textContent = 'Processing…';
    });
    window.addEventListener('pageshow', () => {
        submitted.forEach(({button, text, disabled, hidden}, form) => {
            button.disabled = disabled;
            button.textContent = text;
            hidden?.remove();
            form.removeAttribute('aria-busy');
        });
        submitted.clear();
        setMobileOpen(false);
    });
})();
