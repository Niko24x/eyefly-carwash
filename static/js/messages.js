(function () {
    const AUTO_DISMISS_MS = 5000;
    const toasts = document.querySelectorAll('.message-toast');

    function dismissToast(toast) {
        if (toast.classList.contains('is-dismissed')) {
            return;
        }

        toast.classList.add('is-dismissed');

        window.setTimeout(() => {
            toast.remove();
            const container = document.getElementById('message-toasts');
            if (container && !container.querySelector('.message-toast')) {
                container.remove();
            }
        }, 250);
    }

    toasts.forEach((toast) => {
        toast.style.setProperty('--toast-duration', `${AUTO_DISMISS_MS}ms`);

        const closeButton = toast.querySelector('.message-toast-close');
        const timerId = window.setTimeout(() => dismissToast(toast), AUTO_DISMISS_MS);

        if (closeButton) {
            closeButton.addEventListener('click', () => {
                window.clearTimeout(timerId);
                dismissToast(toast);
            });
        }
    });
})();
