// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Состояние приложения
let state = {
    category: null,
    productName: null,
    specifications: {},
    photos: [],
    avitoLink: null
};

// Элементы DOM
const steps = {
    category: document.getElementById('step-category'),
    name: document.getElementById('step-name'),
    specs: document.getElementById('step-specs'),
    photos: document.getElementById('step-photos'),
    link: document.getElementById('step-link'),
    preview: document.getElementById('step-preview'),
    success: document.getElementById('step-success')
};

// Маппинг шагов для индикатора
const stepOrder = ['category', 'name', 'specs', 'photos', 'link', 'preview'];

// Переход к шагу
function showStep(stepName) {
    Object.values(steps).forEach(step => step.classList.remove('active'));
    if (steps[stepName]) {
        steps[stepName].classList.add('active');
    }
    updateStepIndicator(stepName);
}

// Обновление индикатора прогресса
function updateStepIndicator(currentStep) {
    const dots = document.querySelectorAll('.step-dot');
    const currentIndex = stepOrder.indexOf(currentStep);
    
    dots.forEach((dot, index) => {
        dot.classList.remove('active', 'completed');
        if (index < currentIndex) {
            dot.classList.add('completed');
        } else if (index === currentIndex) {
            dot.classList.add('active');
        }
    });
}

// Шаг 1: Выбор категории
document.querySelectorAll('.category-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        state.category = btn.dataset.category;
        showStep('name');
    });
});

// Шаг 2: Название товара
document.getElementById('search-specs-btn').addEventListener('click', async () => {
    const productName = document.getElementById('product-name').value.trim();
    if (!productName) {
        tg.showAlert('Введите название товара');
        return;
    }
    
    state.productName = productName;
    document.getElementById('loading').classList.remove('hidden');
    
    try {
        // Запрос к бэкенду для поиска характеристик
        const response = await fetch('/api/search-specs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_name: productName,
                category: state.category,
                init_data: tg.initData
            })
        });
        
        const data = await response.json();
        if (data.success) {
            state.specifications = data.specifications;
            renderSpecs();
            showStep('specs');
        } else {
            tg.showAlert(data.error || 'Ошибка при поиске характеристик');
        }
    } catch (error) {
        tg.showAlert('Ошибка соединения с сервером');
        console.error(error);
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
});

// Рендеринг характеристик
function renderSpecs() {
    const container = document.getElementById('specs-container');
    container.innerHTML = '';
    
    for (const [key, value] of Object.entries(state.specifications)) {
        const div = document.createElement('div');
        div.className = 'spec-item';
        div.innerHTML = `
            <label>${key}</label>
            <input type="text" data-spec="${key}" value="${value}" />
        `;
        container.appendChild(div);
    }
}

// Обновление характеристик при редактировании
document.getElementById('specs-container').addEventListener('input', (e) => {
    if (e.target.dataset.spec) {
        state.specifications[e.target.dataset.spec] = e.target.value;
    }
});

// Подтверждение характеристик
document.getElementById('confirm-specs-btn').addEventListener('click', () => {
    showStep('photos');
});

// Редактирование характеристик
document.getElementById('edit-specs-btn').addEventListener('click', () => {
    renderSpecs();
});

// Шаг 4: Фотографии
document.getElementById('add-photo-btn').addEventListener('click', () => {
    document.getElementById('photo-input').click();
});

document.getElementById('photo-input').addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (state.photos.length + files.length > 12) {
        tg.showAlert('Максимум 12 фотографий');
        return;
    }
    
    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (event) => {
            state.photos.push(event.target.result);
            renderPhotos();
        };
        reader.readAsDataURL(file);
    });
});

function renderPhotos() {
    const container = document.getElementById('photos-preview');
    container.innerHTML = '';
    
    state.photos.forEach((photo, index) => {
        const div = document.createElement('div');
        div.className = 'photo-item';
        div.innerHTML = `
            <img src="${photo}" alt="Фото ${index + 1}">
            <button class="remove-btn" data-index="${index}">×</button>
        `;
        container.appendChild(div);
    });
    
    // Удаление фото
    container.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const index = parseInt(btn.dataset.index);
            state.photos.splice(index, 1);
            renderPhotos();
        });
    });
}

document.getElementById('photos-done-btn').addEventListener('click', () => {
    if (state.photos.length === 0) {
        tg.showAlert('Добавьте хотя бы одну фотографию');
        return;
    }
    showStep('link');
});

// Шаг 5: Ссылка на Авито - Предпросмотр
document.getElementById('preview-btn').addEventListener('click', async () => {
    const avitoLink = document.getElementById('avito-link').value.trim();
    if (!avitoLink || !avitoLink.startsWith('http')) {
        tg.showAlert('Введите корректную ссылку на Авито');
        return;
    }
    
    state.avitoLink = avitoLink;
    
    // Получаем предпросмотр поста
    try {
        const response = await fetch('/api/preview-post', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...state,
                init_data: tg.initData
            })
        });
        
        const data = await response.json();
        if (data.success) {
            renderPreview(data.preview);
            showStep('preview');
        } else {
            tg.showAlert(data.error || 'Ошибка при создании предпросмотра');
        }
    } catch (error) {
        tg.showAlert('Ошибка соединения с сервером');
        console.error(error);
    }
});

// Рендеринг предпросмотра
function renderPreview(previewText) {
    const container = document.getElementById('preview-content');
    
    // Парсим HTML из текста поста (если есть HTML теги)
    const lines = previewText.split('\n');
    let html = '';
    
    lines.forEach(line => {
        if (line.trim()) {
            // Обработка заголовков
            if (line.includes('<b>') && line.includes('</b>')) {
                html += `<div style="font-size: 18px; font-weight: 700; margin: 12px 0; color: var(--tg-theme-text-color);">${line}</div>`;
            }
            // Обработка характеристик
            else if (line.startsWith('•')) {
                html += `<div class="preview-spec-item"><span class="preview-spec-name">${line.replace('•', '').split(':')[0]}:</span><span class="preview-spec-value">${line.split(':').slice(1).join(':').trim()}</span></div>`;
            }
            // Обработка ссылок
            else if (line.startsWith('http')) {
                html += `<a href="${line}" target="_blank" class="preview-link">🛒 Купить на Авито</a>`;
            }
            // Обычный текст
            else {
                html += `<div style="margin: 8px 0; color: var(--tg-theme-text-color);">${line}</div>`;
            }
        } else {
            html += '<div style="height: 8px;"></div>';
        }
    });
    
    container.innerHTML = html;
}

// Редактирование из предпросмотра
document.getElementById('edit-preview-btn').addEventListener('click', () => {
    showStep('link');
});

// Шаг 6: Отправка поста
document.getElementById('submit-btn').addEventListener('click', async () => {
    tg.showPopup({
        title: 'Отправка поста',
        message: 'Отправляем пост на модерацию...',
        buttons: [{ type: 'ok' }]
    });
    
    try {
        const response = await fetch('/api/create-post', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...state,
                init_data: tg.initData
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showStep('success');
            tg.MainButton.setText('Закрыть');
            tg.MainButton.show();
            tg.MainButton.onClick(() => {
                tg.close();
            });
        } else {
            tg.showAlert(data.error || 'Ошибка при создании поста');
        }
    } catch (error) {
        tg.showAlert('Ошибка соединения с сервером');
        console.error(error);
    }
});

