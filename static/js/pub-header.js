(function () {
    const header = document.querySelector('.pub-header');
    if (!header) {
        return;
    }

    const SCROLL_THRESHOLD = 12;

    function updateHeader() {
        header.classList.toggle('is-scrolled', window.scrollY > SCROLL_THRESHOLD);
    }

    updateHeader();
    window.addEventListener('scroll', updateHeader, { passive: true });
})();
