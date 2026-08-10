(function () {
    const form = document.getElementById('wizard-form');
    if (!form) {
        return;
    }

    const apiUrl = form.dataset.apiUrl;
    const initialService = form.dataset.initialService || '';

    const STEP_NAMES = ['Edificio', 'Servicio', 'Fecha y hora', 'Vehículo'];
    const TOTAL_STEPS = STEP_NAMES.length;

    let services = [];
    let buildings = [];
    try {
        services = JSON.parse(document.getElementById('wizard-services-data').textContent);
    } catch (error) {
        console.error('No se pudo leer la configuración de servicios.', error);
    }
    try {
        buildings = JSON.parse(document.getElementById('wizard-buildings-data').textContent);
    } catch (error) {
        console.error('No se pudo leer la configuración de edificios.', error);
    }

    const buildingInput = form.querySelector('[name="building"]');
    const serviceInput = form.querySelector('[name="service"]');
    const dateInput = form.querySelector('[name="date"]');
    const timeInput = form.querySelector('[name="time"]');

    const buildingsContainer = document.getElementById('wizard-buildings');
    const servicesContainer = document.getElementById('wizard-services');

    const calGrid = document.getElementById('wiz-cal-grid');
    const calMonth = document.getElementById('wiz-cal-month');
    const calHelper = document.getElementById('wiz-cal-helper');
    const slotsSection = document.getElementById('wizard-schedule-slots');
    const slotsTitle = document.getElementById('wiz-slots-title');
    const slotsContainer = document.getElementById('wiz-slots');
    const slotsHelper = document.getElementById('wiz-slots-helper');
    const summary = document.getElementById('wiz-summary');

    const stepNum = document.getElementById('wizard-step-num');
    const stepName = document.getElementById('wizard-step-name');
    const backButton = document.getElementById('wizard-back');
    const nextButton = document.getElementById('wizard-next');
    const submitButton = document.getElementById('wizard-submit');

    const monthNames = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
    ];
    const weekdayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let currentStep = 1;
    let selectedBuilding = null;
    let selectedService = null;
    let selectedDate = null;
    let selectedTime = null;
    let currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    let availableDates = new Set();

    function formatPrice(value) {
        const number = Number(value);
        if (Number.isNaN(number)) {
            return value;
        }
        return `Q${number % 1 === 0 ? number.toFixed(0) : number.toFixed(2)}`;
    }

    function parseIsoDate(value) {
        const [year, month, day] = value.split('-').map(Number);
        return new Date(year, month - 1, day);
    }

    function isoDate(year, month, day) {
        return [
            year,
            String(month + 1).padStart(2, '0'),
            String(day).padStart(2, '0'),
        ].join('-');
    }

    function formatDisplayDate(value) {
        return parseIsoDate(value).toLocaleDateString('es-GT', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric',
        });
    }

    function formatDisplayTime(value) {
        const [hours, minutes] = value.split(':').map(Number);
        const dateObj = new Date();
        dateObj.setHours(hours, minutes, 0, 0);
        return dateObj.toLocaleTimeString('es-GT', { hour: 'numeric', minute: '2-digit' });
    }

    function buildApiUrl(params) {
        const url = new URL(apiUrl, window.location.origin);
        Object.entries(params).forEach(([key, value]) => {
            if (value) {
                url.searchParams.set(key, value);
            }
        });
        return url.toString();
    }

    // ----- Step 1: buildings -----
    function renderBuildings() {
        buildingsContainer.innerHTML = '';
        if (!buildings.length) {
            buildingsContainer.innerHTML = '<p class="wizard-helper">No hay edificios disponibles por ahora.</p>';
            return;
        }
        buildings.forEach((building) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'wizard-option';
            if (String(selectedBuilding) === String(building.id)) {
                button.classList.add('is-selected');
            }
            button.innerHTML = `
                <span class="wizard-option-icon" aria-hidden="true">
                    <i class="fa-solid fa-building"></i>
                </span>
                <span class="wizard-option-main">
                    <span class="wizard-option-title">${building.name}</span>
                    <span class="wizard-option-desc">${building.address || ''}</span>
                </span>`;
            button.addEventListener('click', () => {
                const changed = String(selectedBuilding) !== String(building.id);
                selectedBuilding = building.id;
                buildingInput.value = building.id;
                if (changed) {
                    selectedDate = null;
                    selectedTime = null;
                    dateInput.value = '';
                    timeInput.value = '';
                    availableDates = new Set();
                    updateSlotsSection();
                    updateFrequencySection();
                    slotsContainer.innerHTML = '';
                }
                renderBuildings();
                updateNav();
            });
            buildingsContainer.appendChild(button);
        });
    }

    // ----- Step 2: services -----
    function renderServices() {
        servicesContainer.innerHTML = '';
        if (!services.length) {
            servicesContainer.innerHTML = '<p class="wizard-helper">No hay servicios disponibles por ahora.</p>';
            return;
        }
        services.forEach((service) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'wizard-option';
            if (String(selectedService) === String(service.id)) {
                button.classList.add('is-selected');
            }
            const duration = service.duration_minutes
                ? `<span class="wizard-option-meta"><i class="fa-solid fa-clock" aria-hidden="true"></i> ${service.duration_minutes} minutos</span>`
                : '';
            const priceLabel = service.covered_by_membership
                ? '<span class="wizard-option-price wizard-option-price--membership">Incluido en membresía</span>'
                : `<span class="wizard-option-price">${formatPrice(service.price)}</span>`;
            button.innerHTML = `
                <span class="wizard-option-main">
                    <span class="wizard-option-title">${service.name}</span>
                    <span class="wizard-option-desc">${service.description || ''}</span>
                    ${duration}
                </span>
                ${priceLabel}`;
            button.addEventListener('click', () => {
                selectedService = service.id;
                serviceInput.value = service.id;
                renderServices();
                updateNav();
            });
            servicesContainer.appendChild(button);
        });
    }

    function updateSlotsSection() {
        if (!slotsSection) {
            return;
        }
        if (!selectedDate) {
            slotsSection.hidden = true;
            return;
        }
        slotsSection.hidden = false;
        if (slotsTitle) {
            slotsTitle.textContent = `Horarios — ${formatDisplayDate(selectedDate)}`;
        }
    }

    function updateFrequencySection() {
        if (!frequencySection) {
            return;
        }
        const wasHidden = frequencySection.hidden;
        frequencySection.hidden = !selectedTime;
        if (selectedTime) {
            updateRecurrenceUI();
            if (wasHidden) {
                frequencySection.classList.remove('is-revealed');
                // Force reflow so the reveal animation can replay.
                void frequencySection.offsetWidth;
                frequencySection.classList.add('is-revealed');
            }
        } else {
            frequencySection.classList.remove('is-revealed');
        }
    }

    // ----- Step 3: calendar + slots -----
    async function fetchAvailableDates() {
        if (!selectedBuilding) {
            return;
        }
        calHelper.textContent = 'Cargando fechas disponibles...';
        try {
            const response = await fetch(buildApiUrl({
                building: selectedBuilding,
                year: currentMonth.getFullYear(),
                month: currentMonth.getMonth() + 1,
            }));
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            availableDates = new Set(data.dates || []);
            calHelper.textContent = availableDates.size
                ? 'Selecciona una fecha disponible.'
                : 'No hay fechas disponibles este mes.';
            renderCalendar();
        } catch (error) {
            calHelper.textContent = 'No se pudieron cargar las fechas disponibles.';
            console.error(error);
        }
    }

    function renderCalendar() {
        const year = currentMonth.getFullYear();
        const month = currentMonth.getMonth();
        calMonth.textContent = `${monthNames[month]} ${year}`;
        calGrid.innerHTML = '';

        weekdayNames.forEach((weekday) => {
            const cell = document.createElement('div');
            cell.className = 'wizard-cal-weekday';
            cell.textContent = weekday;
            calGrid.appendChild(cell);
        });

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startOffset = firstDay.getDay();

        for (let i = 0; i < startOffset; i += 1) {
            const empty = document.createElement('div');
            empty.className = 'wizard-cal-day is-empty';
            calGrid.appendChild(empty);
        }

        for (let day = 1; day <= lastDay.getDate(); day += 1) {
            const cellDate = new Date(year, month, day);
            const value = isoDate(year, month, day);
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'wizard-cal-day';
            button.textContent = String(day);

            if (cellDate < today) {
                button.disabled = true;
                button.classList.add('is-muted');
            } else if (!availableDates.has(value)) {
                button.disabled = true;
                button.classList.add('is-unavailable');
            }
            if (selectedDate === value) {
                button.classList.add('is-selected');
            }

            button.addEventListener('click', () => {
                selectedDate = value;
                selectedTime = null;
                dateInput.value = value;
                timeInput.value = '';
                renderCalendar();
                updateSlotsSection();
                updateFrequencySection();
                fetchAvailableSlots();
                updateNav();
            });
            calGrid.appendChild(button);
        }
    }

    async function fetchAvailableSlots() {
        if (!selectedBuilding || !selectedDate) {
            if (slotsSection) {
                slotsSection.hidden = true;
            }
            return;
        }
        updateSlotsSection();
        slotsHelper.hidden = false;
        slotsHelper.textContent = 'Cargando horarios...';
        slotsContainer.innerHTML = '';
        try {
            const response = await fetch(buildApiUrl({
                building: selectedBuilding,
                date: selectedDate,
            }));
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            renderSlots(data.slots || []);
        } catch (error) {
            slotsHelper.hidden = false;
            slotsHelper.textContent = 'No se pudieron cargar los horarios.';
            console.error(error);
        }
    }

    function renderSlots(slots) {
        slotsContainer.innerHTML = '';
        if (!slots.length) {
            slotsHelper.hidden = false;
            slotsHelper.textContent = 'No hay horarios disponibles para esta fecha.';
            return;
        }
        slotsHelper.hidden = true;
        slots.forEach((slot) => {
            const normalized = slot.slice(0, 5);
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'wizard-slot';
            button.textContent = formatDisplayTime(normalized);
            if (selectedTime === normalized) {
                button.classList.add('is-selected');
            }
            button.addEventListener('click', () => {
                selectedTime = normalized;
                timeInput.value = normalized;
                renderSlots(slots);
                updateFrequencySection();
                updateNav();
            });
            slotsContainer.appendChild(button);
        });
    }

    const recurrenceInput = form.querySelector('[name="recurrence"]');
    const endDateInput = form.querySelector('[name="end_date"]');
    const endDateField = document.getElementById('wizard-end-date-field');
    const endDateHint = document.getElementById('wizard-end-date-hint');
    const frequencySection = document.getElementById('wizard-frequency');
    const recurrenceOptionButtons = Array.from(
        form.querySelectorAll('[data-recurrence-option]')
    );

    const RECURRENCE_LABELS = {
        unica: 'Solo esta vez',
        semanal: 'Cada semana',
        quincenal: 'Cada 15 días',
        mensual: 'Cada mes',
    };

    function addMonths(year, month, day) {
        const lastDay = new Date(year, month + 1, 0).getDate();
        if (day > lastDay) {
            return null;
        }
        return isoDate(year, month, day);
    }

    function previewRecurrenceDates(startIso, endIso, cadence) {
        if (!startIso || cadence === 'unica' || !endIso) {
            return startIso ? [startIso] : [];
        }
        const start = parseIsoDate(startIso);
        const end = parseIsoDate(endIso);
        if (end < start) {
            return [];
        }

        const dates = [];
        if (cadence === 'semanal' || cadence === 'quincenal') {
            const intervalDays = cadence === 'quincenal' ? 14 : 7;
            const current = new Date(start);
            while (current <= end && dates.length < 52) {
                dates.push(isoDate(current.getFullYear(), current.getMonth(), current.getDate()));
                current.setDate(current.getDate() + intervalDays);
            }
            return dates;
        }

        if (cadence === 'mensual') {
            const day = start.getDate();
            let year = start.getFullYear();
            let month = start.getMonth();
            while (dates.length < 52) {
                const candidate = addMonths(year, month, day);
                if (candidate) {
                    const current = parseIsoDate(candidate);
                    if (current > end) {
                        break;
                    }
                    if (current >= start) {
                        dates.push(candidate);
                    }
                }
                month += 1;
                if (month > 11) {
                    month = 0;
                    year += 1;
                }
                if (new Date(year, month, 1) > end) {
                    break;
                }
            }
            return dates;
        }

        return [startIso];
    }

    function updateRecurrenceUI() {
        if (!recurrenceInput || !endDateField) {
            return;
        }
        const cadence = recurrenceInput.value || 'unica';
        const showEnd = cadence !== 'unica';
        recurrenceOptionButtons.forEach((button) => {
            button.classList.toggle('is-selected', button.dataset.recurrenceOption === cadence);
        });
        endDateField.hidden = !showEnd;
        if (endDateInput) {
            endDateInput.required = showEnd;
            if (showEnd && selectedDate && !endDateInput.value) {
                endDateInput.min = selectedDate;
            }
            if (selectedDate) {
                endDateInput.min = selectedDate;
            }
        }

        if (!showEnd || !endDateHint) {
            if (endDateHint) {
                endDateHint.textContent = '';
            }
            return;
        }

        const dates = previewRecurrenceDates(
            selectedDate,
            endDateInput ? endDateInput.value : '',
            cadence,
        );
        if (!endDateInput || !endDateInput.value) {
            if (cadence === 'mensual') {
                endDateHint.textContent = 'Se repetirá el mismo día del mes hasta la fecha fin.';
            } else if (cadence === 'quincenal') {
                endDateHint.textContent = 'Se repetirá cada dos semanas hasta la fecha fin.';
            } else {
                endDateHint.textContent = 'Se repetirá el mismo día de la semana hasta la fecha fin.';
            }
        } else if (dates.length < 2) {
            endDateHint.textContent = 'Ajusta la fecha fin para incluir al menos una repetición.';
        } else {
            endDateHint.textContent = `Se crearán ${dates.length} citas.`;
        }
    }

    // ----- Step 4: summary -----
    function renderSummary() {
        const building = buildings.find((item) => String(item.id) === String(selectedBuilding));
        const service = services.find((item) => String(item.id) === String(selectedService));
        const servicePrice = service
            ? (service.covered_by_membership ? 'Incluido en membresía' : formatPrice(service.price))
            : '—';
        const cadence = recurrenceInput ? (recurrenceInput.value || 'unica') : 'unica';
        const endIso = endDateInput ? endDateInput.value : '';
        const seriesDates = previewRecurrenceDates(selectedDate, endIso, cadence);
        const rows = [
            ['Edificio', building ? building.name : '—'],
            ['Servicio', service ? `${service.name} · ${servicePrice}` : '—'],
            ['Inicio', selectedDate ? formatDisplayDate(selectedDate) : '—'],
            ['Hora', selectedTime ? formatDisplayTime(selectedTime) : '—'],
            ['Cadencia', RECURRENCE_LABELS[cadence] || 'Única'],
        ];
        if (cadence !== 'unica') {
            rows.push(['Fecha fin', endIso ? formatDisplayDate(endIso) : '—']);
            rows.push(['Citas', String(seriesDates.length || 0)]);
        }
        summary.innerHTML = rows.map(([label, value]) => `
            <div class="wizard-summary-row">
                <dt>${label}</dt>
                <dd>${value}</dd>
            </div>`).join('');
    }

    // ----- Validation per step -----
    function customerFieldsFilled() {
        const requiredNames = [
            'full_name',
            'phone_local_number',
            'email',
            'car_brand',
            'car_model',
            'car_color',
            'car_plate',
            'parking_level',
            'parking_number',
        ];
        return requiredNames.every((name) => {
            const field = form.querySelector(`[name="${name}"]`);
            return field && field.value.trim() !== '';
        });
    }

    function recurrenceFieldsValid() {
        if (!recurrenceInput) {
            return true;
        }
        const cadence = recurrenceInput.value || 'unica';
        if (cadence === 'unica') {
            return true;
        }
        if (!endDateInput || !endDateInput.value || !selectedDate) {
            return false;
        }
        return previewRecurrenceDates(selectedDate, endDateInput.value, cadence).length >= 2;
    }

    function isStepValid(step) {
        switch (step) {
            case 1: return Boolean(selectedBuilding);
            case 2: return Boolean(selectedService);
            case 3: return Boolean(selectedDate && selectedTime) && recurrenceFieldsValid();
            case 4: return customerFieldsFilled();
            default: return false;
        }
    }

    // ----- Navigation / rendering -----
    let isAnimatingStep = false;
    const STEP_ANIMATION_MS = 320;
    const prefersReducedMotion = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function clearStepAnimationClasses(section) {
        section.classList.remove(
            'is-animating',
            'is-slide-in-left',
            'is-slide-in-right',
            'is-slide-out-left',
            'is-slide-out-right',
        );
    }

    function updateStepChrome(step) {
        stepNum.textContent = String(step);
        stepName.textContent = STEP_NAMES[step - 1];

        form.querySelectorAll('.wizard-dot').forEach((dot) => {
            const dotStep = Number(dot.dataset.dot);
            dot.classList.toggle('is-active', dotStep === step);
            dot.classList.toggle('is-done', dotStep < step);
            if (dotStep < step) {
                dot.innerHTML = '<i class="fa-solid fa-check" aria-hidden="true"></i>';
            } else {
                dot.textContent = String(dotStep);
            }
        });
        form.querySelectorAll('.wizard-line').forEach((line) => {
            line.classList.toggle('is-done', Number(line.dataset.line) < step);
        });

        backButton.hidden = step === 1;
        const lastStep = step === TOTAL_STEPS;
        nextButton.hidden = lastStep;
        submitButton.hidden = !lastStep;
    }

    function prepareStepContent(step) {
        if (step === 3) {
            fetchAvailableDates();
            if (selectedDate) {
                updateSlotsSection();
                fetchAvailableSlots();
            } else {
                updateSlotsSection();
            }
            updateFrequencySection();
        } else if (step === 4) {
            renderSummary();
        }
    }

    function showStep(step, options = {}) {
        const animate = options.animate !== false && !prefersReducedMotion;
        const previousStep = currentStep;
        const goingForward = step > previousStep;
        const outgoing = form.querySelector(`.wizard-step[data-step="${previousStep}"]`);
        const incoming = form.querySelector(`.wizard-step[data-step="${step}"]`);

        if (!incoming) {
            return;
        }

        if (isAnimatingStep) {
            return;
        }

        currentStep = step;
        updateStepChrome(step);
        prepareStepContent(step);

        const shouldAnimate = animate
            && outgoing
            && outgoing !== incoming
            && !outgoing.hidden
            && previousStep !== step;

        if (!shouldAnimate) {
            form.querySelectorAll('.wizard-step').forEach((section) => {
                clearStepAnimationClasses(section);
                section.hidden = Number(section.dataset.step) !== step;
            });
            updateNav();
            return;
        }

        isAnimatingStep = true;
        nextButton.disabled = true;
        backButton.disabled = true;

        clearStepAnimationClasses(outgoing);
        clearStepAnimationClasses(incoming);

        incoming.hidden = false;
        outgoing.classList.add('is-animating', goingForward ? 'is-slide-out-left' : 'is-slide-out-right');
        incoming.classList.add('is-animating', goingForward ? 'is-slide-in-right' : 'is-slide-in-left');

        window.setTimeout(() => {
            outgoing.hidden = true;
            clearStepAnimationClasses(outgoing);
            clearStepAnimationClasses(incoming);
            form.querySelectorAll('.wizard-step').forEach((section) => {
                if (section !== incoming) {
                    section.hidden = true;
                }
            });
            isAnimatingStep = false;
            backButton.disabled = false;
            updateNav();
        }, STEP_ANIMATION_MS);
    }

    function updateNav() {
        if (isAnimatingStep) {
            nextButton.disabled = true;
            return;
        }
        nextButton.disabled = !isStepValid(currentStep);
        submitButton.disabled = !isStepValid(TOTAL_STEPS);
    }

    nextButton.addEventListener('click', () => {
        if (!isAnimatingStep && isStepValid(currentStep) && currentStep < TOTAL_STEPS) {
            showStep(currentStep + 1, { animate: true });
        }
    });

    backButton.addEventListener('click', () => {
        if (!isAnimatingStep && currentStep > 1) {
            showStep(currentStep - 1, { animate: true });
        }
    });

    document.getElementById('wiz-cal-prev').addEventListener('click', () => {
        currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
        fetchAvailableDates();
    });
    document.getElementById('wiz-cal-next').addEventListener('click', () => {
        currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
        fetchAvailableDates();
    });

    [
        'full_name',
        'phone_local_number',
        'email',
        'car_brand',
        'car_model',
        'car_color',
        'car_plate',
        'parking_level',
        'parking_number',
        'notes',
    ].forEach((name) => {
        const field = form.querySelector(`[name="${name}"]`);
        if (field) {
            field.addEventListener('input', updateNav);
        }
    });

    function onRecurrenceChange() {
        updateRecurrenceUI();
        if (currentStep === 4) {
            renderSummary();
        }
        updateNav();
    }

    if (recurrenceInput) {
        recurrenceInput.addEventListener('change', onRecurrenceChange);
        recurrenceOptionButtons.forEach((button) => {
            button.addEventListener('click', () => {
                recurrenceInput.value = button.dataset.recurrenceOption;
                recurrenceInput.dispatchEvent(new Event('change', { bubbles: true }));
            });
        });
    }
    if (endDateInput) {
        endDateInput.addEventListener('change', onRecurrenceChange);
        endDateInput.addEventListener('input', onRecurrenceChange);
    }

    form.addEventListener('submit', (event) => {
        if (!isStepValid(TOTAL_STEPS) || !recurrenceFieldsValid() || !selectedBuilding
            || !selectedService || !selectedDate || !selectedTime) {
            event.preventDefault();
        }
    });

    // ----- Init -----
    function restoreFromForm() {
        if (buildingInput && buildingInput.value) {
            selectedBuilding = buildingInput.value;
        }
        if (serviceInput && serviceInput.value) {
            selectedService = serviceInput.value;
        } else if (initialService) {
            const match = services.find((item) => String(item.id) === String(initialService));
            if (match) {
                selectedService = match.id;
                serviceInput.value = match.id;
            }
        }
        if (dateInput && dateInput.value) {
            selectedDate = dateInput.value;
            const parsed = parseIsoDate(selectedDate);
            currentMonth = new Date(parsed.getFullYear(), parsed.getMonth(), 1);
        }
        if (timeInput && timeInput.value) {
            selectedTime = timeInput.value.slice(0, 5);
            timeInput.value = selectedTime;
        }
    }

    restoreFromForm();
    renderBuildings();
    renderServices();

    const startStep = Number(form.dataset.startStep || 1);
    showStep(
        Number.isFinite(startStep) && startStep >= 1 && startStep <= TOTAL_STEPS ? startStep : 1,
        { animate: false },
    );
})();
