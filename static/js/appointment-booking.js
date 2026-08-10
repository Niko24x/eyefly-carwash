(function () {
    const form = document.getElementById('booking-form');
    if (!form) {
        return;
    }

    const mode = form.dataset.mode;
    const apiUrl = form.dataset.apiUrl;
    const configElement = document.getElementById('booking-services-data');
    const buildingsElement = document.getElementById('booking-buildings-data');
    let services = [];
    let buildings = [];
    if (configElement) {
        try {
            services = JSON.parse(configElement.textContent);
        } catch (error) {
            console.error('No se pudo leer la configuración de servicios.', error);
        }
    }
    if (buildingsElement) {
        try {
            buildings = JSON.parse(buildingsElement.textContent);
        } catch (error) {
            console.error('No se pudo leer la configuración de edificios.', error);
        }
    }
    const fixedBuildingId = form.dataset.fixedBuilding || null;
    const excludeId = form.dataset.excludeId || null;

    const buildingSelect = form.querySelector('[name="building"]');
    const serviceSelect = form.querySelector('[name="service"]');
    const dateInput = form.querySelector('[name="date"]');
    const timeInput = form.querySelector('[name="time"]');
    const submitButton = document.getElementById('booking-submit');

    const monthLabel = document.getElementById('calendar-month-label');
    const calendarGrid = document.getElementById('booking-calendar-grid');
    const calendarHelper = document.getElementById('calendar-helper');
    const slotsList = document.getElementById('booking-slots-list');
    const slotsHelper = document.getElementById('slots-helper');
    const slotsDayLabel = document.getElementById('slots-day-label');
    const selectionSummary = document.getElementById('booking-selection-summary');
    const selectedDatetimeLabel = document.getElementById('selected-datetime-label');

    const serviceEyebrow = document.getElementById('service-eyebrow');
    const serviceTitle = document.getElementById('service-title');
    const serviceDescription = document.getElementById('service-description');

    const monthNames = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
    ];
    const weekdayNames = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

    function normalizeTime(timeValue) {
        if (!timeValue) {
            return '';
        }
        const parts = timeValue.trim().split(':');
        if (parts.length < 2) {
            return '';
        }
        return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}`;
    }

    function parseIsoDate(dateValue) {
        const [year, month, day] = dateValue.split('-').map(Number);
        return new Date(year, month - 1, day);
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let initialDate = form.dataset.initialDate || '';
    let initialTime = normalizeTime(form.dataset.initialTime || '');

    if (initialDate) {
        const initialDateObj = parseIsoDate(initialDate);
        if (Number.isNaN(initialDateObj.getTime()) || initialDateObj < today) {
            initialDate = '';
            initialTime = '';
        }
    }

    let currentMonth = initialDate
        ? parseIsoDate(initialDate)
        : new Date(today.getFullYear(), today.getMonth(), 1);
    currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);

    let availableDates = new Set();
    let selectedDate = initialDate || null;
    let selectedTime = initialTime || null;

    function getBuildingId() {
        if (fixedBuildingId) {
            return fixedBuildingId;
        }
        return buildingSelect ? buildingSelect.value : null;
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

    async function fetchAvailableDates() {
        const buildingId = getBuildingId();
        if (!buildingId) {
            availableDates = new Set();
            renderCalendar();
            return;
        }

        calendarHelper.textContent = 'Cargando fechas disponibles...';
        try {
            const response = await fetch(
                buildApiUrl({
                    building: buildingId,
                    year: currentMonth.getFullYear(),
                    month: currentMonth.getMonth() + 1,
                    exclude: excludeId,
                }),
            );
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            availableDates = new Set(data.dates || []);
            if (mode === 'reschedule' && selectedDate) {
                availableDates.add(selectedDate);
            }
            calendarHelper.textContent = availableDates.size
                ? 'Selecciona una fecha disponible.'
                : 'No hay fechas disponibles este mes.';
            renderCalendar();
        } catch (error) {
            calendarHelper.textContent = 'No se pudieron cargar las fechas disponibles.';
            console.error(error);
        }
    }

    async function fetchAvailableSlots(dateValue) {
        const buildingId = getBuildingId();
        if (!buildingId || !dateValue) {
            slotsList.innerHTML = '';
            slotsHelper.hidden = false;
            return;
        }

        slotsHelper.hidden = true;
        slotsList.innerHTML = '<p class="booking-helper">Cargando horarios...</p>';
        try {
            const response = await fetch(
                buildApiUrl({
                    building: buildingId,
                    date: dateValue,
                    exclude: excludeId,
                }),
            );
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            let slots = data.slots || [];
            if (
                mode === 'reschedule'
                && selectedDate === dateValue
                && selectedTime
                && !slots.includes(selectedTime)
            ) {
                slots = [...slots, selectedTime].sort();
            }
            renderSlots(dateValue, slots);
        } catch (error) {
            slotsList.innerHTML = '';
            slotsHelper.hidden = false;
            slotsHelper.textContent = 'No se pudieron cargar los horarios.';
            console.error(error);
        }
    }

    function renderCalendar() {
        const year = currentMonth.getFullYear();
        const month = currentMonth.getMonth();
        monthLabel.textContent = `${monthNames[month]} ${year}`;

        calendarGrid.innerHTML = '';
        weekdayNames.forEach((weekday) => {
            const weekdayCell = document.createElement('div');
            weekdayCell.className = 'booking-calendar-weekday';
            weekdayCell.textContent = weekday;
            calendarGrid.appendChild(weekdayCell);
        });

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startOffset = (firstDay.getDay() + 6) % 7;

        for (let i = 0; i < startOffset; i += 1) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'booking-calendar-day is-empty';
            calendarGrid.appendChild(emptyCell);
        }

        for (let day = 1; day <= lastDay.getDate(); day += 1) {
            const cellDate = new Date(year, month, day);
            const isoDate = [
                year,
                String(month + 1).padStart(2, '0'),
                String(day).padStart(2, '0'),
            ].join('-');
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'booking-calendar-day';
            button.textContent = String(day);
            button.dataset.date = isoDate;

            if (cellDate < today) {
                button.disabled = true;
                button.classList.add('is-muted');
            } else if (!availableDates.has(isoDate)) {
                button.disabled = true;
                button.classList.add('is-unavailable');
            }

            if (selectedDate === isoDate) {
                button.classList.add('is-selected');
                if (availableDates.has(isoDate)) {
                    button.disabled = false;
                    button.classList.remove('is-unavailable');
                }
            }

            button.addEventListener('click', () => {
                selectedDate = isoDate;
                selectedTime = null;
                if (dateInput) {
                    dateInput.value = isoDate;
                }
                if (timeInput) {
                    timeInput.value = '';
                }
                renderCalendar();
                updateSelectionSummary();
                fetchAvailableSlots(isoDate);
                updateSubmitState();
            });

            calendarGrid.appendChild(button);
        }
    }

    function formatDisplayDate(dateValue) {
        const dateObj = parseIsoDate(dateValue);
        return dateObj.toLocaleDateString('es-GT', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric',
        });
    }

    function formatDisplayTime(timeValue) {
        const normalized = normalizeTime(timeValue);
        const [hours, minutes] = normalized.split(':').map(Number);
        const dateObj = new Date();
        dateObj.setHours(hours, minutes, 0, 0);
        return dateObj.toLocaleTimeString('es-GT', {
            hour: 'numeric',
            minute: '2-digit',
        });
    }

    function renderSlots(dateValue, slots) {
        slotsDayLabel.textContent = formatDisplayDate(dateValue);
        slotsList.innerHTML = '';

        if (!slots.length) {
            slotsHelper.hidden = false;
            slotsHelper.textContent = 'No hay horarios disponibles para esta fecha.';
            return;
        }

        slotsHelper.hidden = true;
        const normalizedSelectedTime = normalizeTime(selectedTime);
        slots.forEach((slot) => {
            const normalizedSlot = normalizeTime(slot);
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'booking-slot';
            button.textContent = formatDisplayTime(normalizedSlot);
            button.dataset.time = normalizedSlot;

            if (normalizedSelectedTime === normalizedSlot) {
                button.classList.add('is-selected');
            }

            button.addEventListener('click', () => {
                selectedTime = normalizedSlot;
                if (timeInput) {
                    timeInput.value = normalizedSlot;
                }
                renderSlots(dateValue, slots);
                updateSelectionSummary();
                updateSubmitState();
            });

            slotsList.appendChild(button);
        });
    }

    function updateSelectionSummary() {
        if (!selectedDate || !selectedTime) {
            selectionSummary.hidden = true;
            return;
        }

        selectionSummary.hidden = false;
        selectedDatetimeLabel.textContent = `${formatDisplayDate(selectedDate)} · ${formatDisplayTime(selectedTime)}`;
    }

    function updateSubmitState() {
        const hasSchedule = Boolean(selectedDate && selectedTime);
        if (mode === 'reschedule') {
            submitButton.disabled = !hasSchedule;
            return;
        }

        submitButton.disabled = !hasSchedule;
    }

    function updateServiceDetails() {
        if (!serviceSelect || !serviceTitle) {
            return;
        }

        const service = services.find(
            (item) => String(item.id) === String(serviceSelect.value),
        );
        if (!service) {
            serviceEyebrow.textContent = 'Servicio';
            serviceTitle.textContent = mode === 'edit' ? 'Editar cita' : 'Agendar cita';
            serviceDescription.textContent =
                'Selecciona el edificio, servicio, fecha y hora para agendar tu cita de lavado.';
            return;
        }

        serviceEyebrow.textContent = buildings.find(
            (item) => buildingSelect && String(item.id) === String(buildingSelect.value),
        )?.name || 'Servicio';
        serviceTitle.textContent = service.name;
        serviceDescription.textContent =
            service.description || 'Servicio de lavado de autos a domicilio en tu edificio.';
    }

    document.getElementById('calendar-prev').addEventListener('click', () => {
        currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
        fetchAvailableDates();
    });

    document.getElementById('calendar-next').addEventListener('click', () => {
        currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
        fetchAvailableDates();
    });

    if (buildingSelect) {
        buildingSelect.addEventListener('change', () => {
            selectedDate = null;
            selectedTime = null;
            if (dateInput) {
                dateInput.value = '';
            }
            if (timeInput) {
                timeInput.value = '';
            }
            slotsList.innerHTML = '';
            slotsHelper.hidden = false;
            slotsHelper.textContent = 'Elige una fecha para ver horarios disponibles.';
            updateServiceDetails();
            fetchAvailableDates();
            updateSelectionSummary();
            updateSubmitState();
        });
    }

    if (serviceSelect) {
        serviceSelect.addEventListener('change', updateServiceDetails);
    }

    form.addEventListener('submit', (event) => {
        if (!selectedDate || !selectedTime) {
            event.preventDefault();
            calendarHelper.textContent = 'Selecciona una fecha y hora antes de continuar.';
        }
    });

    updateServiceDetails();
    fetchAvailableDates().then(() => {
        if (selectedDate) {
            if (dateInput) {
                dateInput.value = selectedDate;
            }
            return fetchAvailableSlots(selectedDate);
        }
        return null;
    }).then(() => {
        if (selectedTime && timeInput) {
            timeInput.value = normalizeTime(selectedTime);
        }
        updateSelectionSummary();
        updateSubmitState();
    });
})();
