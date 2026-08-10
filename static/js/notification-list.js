(function () {
    var messageModal = document.querySelector('[data-modal="notification-message"]');
    var messageContent = document.querySelector('[data-notification-message-content]');
    var registeredAt = document.querySelector('[data-notification-registered-at]');

    if (!messageModal || !messageContent || !registeredAt) {
        return;
    }

    function closeModal() {
        messageModal.hidden = true;
        messageContent.textContent = '';
        registeredAt.textContent = '';
    }

    function openMessageModal(templateId, registeredLabel) {
        var template = document.getElementById(templateId);
        if (!template) {
            return;
        }

        registeredAt.textContent = registeredLabel || '—';
        messageContent.textContent = template.content.textContent.trim();
        messageModal.hidden = false;
    }

    document.addEventListener('click', function (event) {
        var closeButton = event.target.closest('[data-close-modal]');
        if (closeButton && messageModal.contains(closeButton)) {
            closeModal();
            return;
        }

        if (event.target === messageModal) {
            closeModal();
            return;
        }

        var messageButton = event.target.closest('[data-notification-message-button]');
        if (messageButton) {
            openMessageModal(
                messageButton.dataset.messageId,
                messageButton.dataset.registeredAt
            );
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !messageModal.hidden) {
            closeModal();
        }
    });
})();
