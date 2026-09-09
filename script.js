// ---------- Глобальные переменные ----------
let supplements = [];
let chartInstance = null;

// ---------- Загрузка данных ----------
fetch('data.json')
    .then(res => {
        if (!res.ok) throw new Error('Не удалось загрузить data.json');
        return res.json();
    })
    .then(data => {
        supplements = data;
        initApp();
    })
    .catch(err => {
        console.error('Ошибка:', err);
        document.body.innerHTML = '<p style="color:red;">❌ Не удалось загрузить данные. Проверьте, что файл data.json лежит рядом с index.html.</p>';
    });

// ---------- Инициализация ----------
function initApp() {
    populateSymptomFilter();
    renderCards(supplements);
    renderBubbleChart(supplements);
    populateCompareSelects();
    setupThemeToggle();
    setupSymptomFilter();
    setupCompareButton();
}

// ---------- Фильтр по симптомам (эффектам) ----------
function populateSymptomFilter() {
    const effectsSet = new Set();
    supplements.forEach(s => {
        if (Array.isArray(s.effects)) {
            s.effects.forEach(e => effectsSet.add(e));
        }
    });
    const select = document.getElementById('symptomSelect');
    effectsSet.forEach(e => {
        const opt = document.createElement('option');
        opt.value = e;
        opt.textContent = e;
        select.appendChild(opt);
    });
}

function setupSymptomFilter() {
    document.getElementById('symptomSelect').addEventListener('change', function() {
        const selected = this.value;
        if (selected === 'all') {
            renderCards(supplements);
            renderBubbleChart(supplements);
        } else {
            const filtered = supplements.filter(s => s.effects && s.effects.includes(selected));
            renderCards(filtered);
            renderBubbleChart(filtered);
        }
    });
}

// ---------- Отрисовка карточек ----------
function renderCards(data) {
    const grid = document.getElementById('cardsGrid');
    if (!data || data.length === 0) {
        grid.innerHTML = '<p style="opacity:0.6;">Нет добавок для отображения</p>';
        return;
    }
    grid.innerHTML = data.map(s => `
        <div class="card">
            <h3>${s.name || 'Без названия'}</h3>
            <div class="verdict" style="background:${getVerdictColor(s.verdict)}; color:#fff;">${s.verdict || 'Неизвестно'}</div>
            <div class="price">${s.price ? s.price + ' ₽/мес' : 'Цена не указана'}</div>
            <div class="effects">
                ${Array.isArray(s.effects) ? s.effects.map(e => `<span>${e}</span>`).join('') : ''}
            </div>
        </div>
    `).join('');
}

// ---------- Пузырьковая диаграмма (Chart.js) ----------
function renderBubbleChart(data) {
    const ctx = document.getElementById('bubbleChart').getContext('2d');
    if (chartInstance) {
        chartInstance.destroy();
    }
    if (!data || data.length === 0) {
        // Показываем пустой график
        chartInstance = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: [] },
            options: { plugins: { legend: { display: false } } }
        });
        return;
    }

    // Собираем точки
    const datasets = data.map(item => ({
        label: item.name || 'Без названия',
        data: [{
            x: item.price || 0,
            y: item.scienceIndex || 0
        }],
        backgroundColor: getVerdictColor(item.verdict),
        pointRadius: Math.sqrt(item.metaCount || 1) * 2.5,
        pointHoverRadius: Math.sqrt(item.metaCount || 1) * 4,
    }));

    chartInstance = new Chart(ctx, {
        type: 'scatter',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    title: { display: true, text: 'Цена за месяц (₽)', color: getComputedStyle(document.body).getPropertyValue('--text') },
                    grid: { color: 'rgba(128,128,128,0.15)' }
                },
                y: {
                    title: { display: true, text: 'Индекс науки', color: getComputedStyle(document.body).getPropertyValue('--text') },
                    grid: { color: 'rgba(128,128,128,0.15)' }
                }
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    enabled: false // отключаем стандартный, будем использовать свой
                }
            },
            onHover: function(event, chartElements) {
                if (chartElements && chartElements.length) {
                    const index = chartElements[0].datasetIndex;
                    const item = data[index];
                    if (item) showTooltip(event, item);
                } else {
                    hideTooltip();
                }
            }
        }
    });
}

// ---------- Тултип (кастомный) ----------
function showTooltip(event, item) {
    const tooltip = document.getElementById('tooltip');
    tooltip.style.display = 'block';
    tooltip.innerHTML = `
        <strong>${item.name}</strong>
        <div class="detail">${item.description || 'Нет описания'}</div>
        <div class="detail">💊 Дозировка: ${item.dosage || 'не указана'}</div>
        <div class="detail">⏳ Курс: ${item.course || 'не указан'}</div>
        <div class="detail">⚠️ ${item.contraindications || 'Нет противопоказаний'}</div>
    `;
    // Позиционируем рядом с курсором
    tooltip.style.left = (event.clientX + 15) + 'px';
    tooltip.style.top = (event.clientY - 10) + 'px';
}

function hideTooltip() {
    document.getElementById('tooltip').style.display = 'none';
}

// ---------- Цвет вердикта ----------
function getVerdictColor(verdict) {
    if (!verdict) return '#6c757d';
    const lower = verdict.toLowerCase();
    if (lower.includes('доказано') && lower.includes('сильно')) return '#2d8a4e';
    if (lower.includes('доказано') && lower.includes('умеренно')) return '#5b8c5a';
    if (lower.includes('слабые данные')) return '#d4a017';
    if (lower.includes('дефицит')) return '#d4a017';
    if (lower.includes('только у пациентов')) return '#c07a2c';
    if (lower.includes('пробирки') || lower.includes('животные')) return '#b5651d';
    if (lower.includes('маркетинг')) return '#a94442';
    return '#6c757d';
}

// ---------- Сравнение двух добавок ----------
function populateCompareSelects() {
    const s1 = document.getElementById('compareSelect1');
    const s2 = document.getElementById('compareSelect2');
    supplements.forEach(s => {
        const opt1 = document.createElement('option');
        opt1.value = s.id || s.name;
        opt1.textContent = s.name;
        s1.appendChild(opt1);
        const opt2 = document.createElement('option');
        opt2.value = s.id || s.name;
        opt2.textContent = s.name;
        s2.appendChild(opt2);
    });
    // По умолчанию выбираем первые две
    if (supplements.length >= 2) {
        s1.value = supplements[0].id || supplements[0].name;
        s2.value = supplements[1].id || supplements[1].name;
    }
}

function setupCompareButton() {
    document.getElementById('compareBtn').addEventListener('click', function() {
        const id1 = document.getElementById('compareSelect1').value;
        const id2 = document.getElementById('compareSelect2').value;
        const sup1 = supplements.find(s => (s.id || s.name) === id1);
        const sup2 = supplements.find(s => (s.id || s.name) === id2);
        if (!sup1 || !sup2) {
            document.getElementById('compareResult').innerHTML = '<p style="color:red;">Не удалось найти добавки</p>';
            return;
        }
        // Строим таблицу
        const fields = [
            { label: 'Название', key: 'name' },
            { label: 'Цена (₽/мес)', key: 'price' },
            { label: 'Индекс науки', key: 'scienceIndex' },
            { label: 'Число мета-анализов', key: 'metaCount' },
            { label: 'Вердикт', key: 'verdict' },
            { label: 'Эффекты', key: 'effects', format: arr => Array.isArray(arr) ? arr.join(', ') : '' },
            { label: 'Противопоказания', key: 'contraindications' },
            { label: 'Курс', key: 'course' },
            { label: 'Время до эффекта', key: 'timeToResponse' },
        ];
        let html = `<table>
            <tr><th>Параметр</th><th>${sup1.name}</th><th>${sup2.name}</th></tr>`;
        fields.forEach(f => {
            const val1 = f.format ? f.format(sup1[f.key]) : (sup1[f.key] ?? '—');
            const val2 = f.format ? f.format(sup2[f.key]) : (sup2[f.key] ?? '—');
            html += `<tr><td>${f.label}</td><td>${val1}</td><td>${val2}</td></tr>`;
        });
        html += '</table>';
        document.getElementById('compareResult').innerHTML = html;
    });
    // Запускаем сравнение сразу при загрузке
    document.getElementById('compareBtn').click();
}

// ---------- Тёмная тема ----------
function setupThemeToggle() {
    const btn = document.getElementById('themeToggle');
    btn.addEventListener('click', function() {
        document.body.classList.toggle('dark');
        this.textContent = document.body.classList.contains('dark') ? '☀️ Светлая тема' : '🌙 Тёмная тема';
        // Перерисовываем диаграмму, чтобы подхватились новые цвета осей (опционально)
        renderBubbleChart(supplements);
    });
}