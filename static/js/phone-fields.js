(function () {
    function placeholderForMax(maxLength) {
        var placeholders = {
            7: '622-1234',
            8: '5555-1234',
            9: '555-123-456',
            10: '555-123-4567',
            11: '11-98765-4321',
        };

        return placeholders[maxLength] || '5555-1234';
    }

    function formatLocalPhone(digits, maxLength) {
        var length = digits.length;

        if (length === 0) {
            return '';
        }

        if (maxLength <= 8) {
            if (length <= 4) {
                return digits;
            }
            return digits.slice(0, 4) + '-' + digits.slice(4, maxLength);
        }

        if (maxLength === 9) {
            if (length <= 3) {
                return digits;
            }
            if (length <= 6) {
                return digits.slice(0, 3) + '-' + digits.slice(3);
            }
            return digits.slice(0, 3) + '-' + digits.slice(3, 6) + '-' + digits.slice(6, maxLength);
        }

        if (maxLength === 10) {
            if (length <= 3) {
                return digits;
            }
            if (length <= 6) {
                return digits.slice(0, 3) + '-' + digits.slice(3);
            }
            return digits.slice(0, 3) + '-' + digits.slice(3, 6) + '-' + digits.slice(6, maxLength);
        }

        if (length <= 2) {
            return digits;
        }
        if (length <= 7) {
            return digits.slice(0, 2) + '-' + digits.slice(2);
        }
        return digits.slice(0, 2) + '-' + digits.slice(2, 7) + '-' + digits.slice(7, maxLength);
    }

    function getMaxDigits(select) {
        var option = select.options[select.selectedIndex];
        return parseInt(option && option.dataset.maxDigits ? option.dataset.maxDigits : '10', 10);
    }

    function initPhoneCountryCodeSelect(select, onChange) {
        var options = Array.prototype.slice.call(select.options);

        options.forEach(function (option) {
            if (!option.dataset.fullLabel) {
                option.dataset.fullLabel = option.text;
                option.dataset.shortLabel = option.value;
            }
        });

        function collapse() {
            var selected = select.options[select.selectedIndex];
            if (!selected) {
                return;
            }

            options.forEach(function (option) {
                option.text = option === selected
                    ? option.dataset.shortLabel
                    : option.dataset.fullLabel;
            });
        }

        function expand() {
            options.forEach(function (option) {
                option.text = option.dataset.fullLabel;
            });
        }

        select.addEventListener('mousedown', expand);
        select.addEventListener('focus', expand);
        select.addEventListener('change', function () {
            collapse();
            select.blur();
            if (typeof onChange === 'function') {
                onChange();
            }
        });
        select.addEventListener('blur', collapse);

        collapse();
    }

    function initPhoneLocalNumberInput(input, getMaxLength) {
        function applyFormat() {
            var maxLength = getMaxLength();
            var selectionStart = input.selectionStart;
            var digitsBeforeCursor = input.value.slice(0, selectionStart).replace(/\D/g, '').length;
            var digits = input.value.replace(/\D/g, '').slice(0, maxLength);
            var formatted = formatLocalPhone(digits, maxLength);
            input.value = formatted;

            var newPos = formatted.length;
            if (digitsBeforeCursor === 0) {
                newPos = 0;
            } else {
                var seen = 0;
                for (var index = 0; index < formatted.length; index += 1) {
                    if (/\d/.test(formatted[index])) {
                        seen += 1;
                        if (seen >= digitsBeforeCursor) {
                            newPos = index + 1;
                            break;
                        }
                    }
                }
            }

            input.setSelectionRange(newPos, newPos);
        }

        function syncPlaceholder() {
            input.placeholder = placeholderForMax(getMaxLength());
        }

        input.addEventListener('input', applyFormat);

        if (input.value) {
            var maxLength = getMaxLength();
            input.value = formatLocalPhone(
                input.value.replace(/\D/g, '').slice(0, maxLength),
                maxLength
            );
        }

        syncPlaceholder();

        return function refreshForCountryChange() {
            var maxLength = getMaxLength();
            input.value = formatLocalPhone(input.value.replace(/\D/g, '').slice(0, maxLength), maxLength);
            syncPlaceholder();
        };
    }

    function initPhoneFieldGroup(composite) {
        var select = composite.querySelector('.phone-country-code-select');
        var input = composite.querySelector('.phone-local-number-input');

        if (!select || !input) {
            return;
        }

        var refreshForCountryChange = initPhoneLocalNumberInput(input, function () {
            return getMaxDigits(select);
        });

        initPhoneCountryCodeSelect(select, refreshForCountryChange);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.phone-input-group--composite').forEach(initPhoneFieldGroup);
    });
})();
