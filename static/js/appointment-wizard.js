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
    let vehicles = [];
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
    try {
        vehicles = JSON.parse(document.getElementById('wizard-vehicles-data').textContent);
    } catch (error) {
        console.error('No se pudo leer la configuración de vehículos.', error);
    }

    const buildingInput = form.querySelector('[name="building"]');
    const serviceInput = form.querySelector('[name="service"]');
    const vehicleInput = form.querySelector('[name="vehicle"]');
    const vehicleAssignmentsInput = form.querySelector('[name="vehicle_assignments"]');
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
    const vehicleTableBody = document.getElementById('wizard-vehicle-table-body');

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
    let vehicleAssignments = {};

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
                const changed = String(selectedService) !== String(service.id);
                selectedService = service.id;
                serviceInput.value = service.id;
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
                service: selectedService,
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
                service: selectedService,
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
        renderVehicleRows(seriesDates, service);
    }

    function syncVehicleInputs() {
        if (vehicleAssignmentsInput) {
            vehicleAssignmentsInput.value = JSON.stringify(vehicleAssignments);
        }
        const firstAssigned = Object.values(vehicleAssignments).find((value) => value);
        if (vehicleInput) {
            vehicleInput.value = firstAssigned || '';
        }
    }

    function findVehicleById(vehicleId) {
        if (!vehicleId) {
            return null;
        }
        return vehicles.find((vehicle) => String(vehicle.id) === String(vehicleId)) || null;
    }

    function selectedSeriesDates() {
        const cadence = recurrenceInput ? (recurrenceInput.value || 'unica') : 'unica';
        const endIso = endDateInput ? endDateInput.value : '';
        return previewRecurrenceDates(selectedDate, endIso, cadence);
    }

    function allSeriesDatesHaveVehicles() {
        const dates = selectedSeriesDates();
        return Boolean(dates.length) && dates.every((dateIso) => vehicleAssignments[dateIso]);
    }

    function setFieldValue(name, value) {
        const field = form.querySelector(`[name="${name}"]`);
        if (field) {
            field.value = value || '';
        }
    }

    function applyVehicleToFields(vehicleId) {
        const vehicle = findVehicleById(vehicleId);
        if (!vehicle) {
            updateNav();
            return;
        }
        setFieldValue('car_brand', vehicle.brand);
        setFieldValue('car_model', vehicle.model);
        setFieldValue('car_color', vehicle.color);
        setFieldValue('car_plate', vehicle.plate);
        setFieldValue('parking_level', vehicle.parking_level);
        setFieldValue('parking_number', vehicle.parking_number);
        updateNav();
    }

    function renderVehicleRows(seriesDates, service) {
        if (!vehicleTableBody) {
            return;
        }
        vehicleTableBody.innerHTML = '';
        if (!seriesDates.length) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="2">Selecciona fecha y servicio para asignar vehículo.</td>';
            vehicleTableBody.appendChild(row);
            return;
        }

        const validDateSet = new Set(seriesDates);
        Object.keys(vehicleAssignments).forEach((dateIso) => {
            if (!validDateSet.has(dateIso)) {
                delete vehicleAssignments[dateIso];
            }
        });

        seriesDates.forEach((dateIso, index) => {
            const row = document.createElement('tr');
            if (index === 0) {
                row.classList.add('wizard-vehicle-row--primary');
            }
            const serviceCell = document.createElement('td');
            serviceCell.innerHTML = `
                <div class="wizard-vehicle-service">
                    <strong>${service ? service.name : 'Servicio seleccionado'}</strong>
                    <span class="wizard-field-hint">${formatDisplayDate(dateIso)}</span>
                </div>`;

            const vehicleCell = document.createElement('td');
            const select = document.createElement('select');
            select.dataset.vehicleDate = dateIso;
            const emptyLabel = vehicles.length
                ? 'Selecciona un vehículo'
                : 'No hay vehículos en tu cuenta';
            select.innerHTML = [
                `<option value="">${emptyLabel}</option>`,
                ...vehicles.map((vehicle) => (
                    `<option value="${vehicle.id}">${vehicle.label}</option>`
                )),
            ].join('');
            select.value = vehicleAssignments[dateIso] || (index === 0 && vehicleInput ? vehicleInput.value : '');
            if (select.value) {
                vehicleAssignments[dateIso] = select.value;
            }
            if (!vehicles.length) {
                select.disabled = true;
            }
            select.addEventListener('change', () => {
                if (select.value) {
                    vehicleAssignments[dateIso] = select.value;
                    applyVehicleToFields(select.value);
                } else {
                    delete vehicleAssignments[dateIso];
                }
                const applyButton = row.querySelector('.wizard-apply-vehicle');
                if (applyButton) {
                    applyButton.disabled = !select.value;
                }
                syncVehicleInputs();
                updateNav();
            });
            vehicleCell.appendChild(select);

            if (index === 0 && seriesDates.length > 1) {
                const applyButton = document.createElement('button');
                applyButton.type = 'button';
                applyButton.className = 'wizard-apply-vehicle';
                applyButton.textContent = 'Este carro para todas las citas';
                applyButton.disabled = !select.value;
                applyButton.addEventListener('click', () => {
                    applyVehicleToAllDates(select.value);
                });
                vehicleCell.appendChild(applyButton);
            }

            row.appendChild(serviceCell);
            row.appendChild(vehicleCell);
            vehicleTableBody.appendChild(row);
        });
        syncVehicleInputs();
    }

    // ----- Validation per step -----
    function customerFieldsFilled() {
        return allSeriesDatesHaveVehicles();
    }

    function applyVehicleToAllDates(vehicleId) {
        if (!vehicleId) {
            return;
        }
        vehicleTableBody.querySelectorAll('select[data-vehicle-date]').forEach((select) => {
            select.value = vehicleId;
            vehicleAssignments[select.dataset.vehicleDate] = vehicleId;
        });
        applyVehicleToFields(vehicleId);
        syncVehicleInputs();
        updateNav();
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
    let isSubmitting = false;

    form.addEventListener('submit', (event) => {
        if (!isStepValid(TOTAL_STEPS) || !recurrenceFieldsValid() || !selectedBuilding
            || !selectedService || !selectedDate || !selectedTime) {
            event.preventDefault();
            return;
        }
        if (isSubmitting) {
            event.preventDefault();
            return;
        }
        isSubmitting = true;
        submitButton.disabled = true;
        submitButton.textContent = 'Confirmando...';
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
        if (vehicleAssignmentsInput && vehicleAssignmentsInput.value) {
            try {
                vehicleAssignments = JSON.parse(vehicleAssignmentsInput.value) || {};
            } catch (error) {
                vehicleAssignments = {};
            }
        }
    }

    restoreFromForm();
    renderBuildings();
    renderServices();
    syncVehicleInputs();

    const startStep = Number(form.dataset.startStep || 1);
    showStep(
        Number.isFinite(startStep) && startStep >= 1 && startStep <= TOTAL_STEPS ? startStep : 1,
        { animate: false },
    );
})();
