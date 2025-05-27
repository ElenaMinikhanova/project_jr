const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const uploadIcon = document.getElementById('uploadIcon');
const nameDiv = document.querySelector('.generation .name');

let pendingFile = null; // Для хранения выбранного файла до загрузки

// Обработка выбора файла через диалог
fileInput.addEventListener('change', () => {
  if (fileInput.files && fileInput.files[0]) {
    handleFileSelection(fileInput.files[0]);
  }
});

// Обработка перетаскивания
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    handleFileSelection(e.dataTransfer.files[0]);
  }
});

// Обработка клика по области для выбора файла
dropZone.addEventListener('click', () => {
  fileInput.click();
});

// Функция для временного хранения выбранного файла
function handleFileSelection(file) {
  const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
  const maxSize = 5 * 1024 * 1024;
  if (!validTypes.includes(file.type)) {
    alert('Unsupported file type. Please upload JPG, PNG, or GIF.');
    return;
  }

  if (file.size > maxSize) {
    alert('File size exceeds 5MB.');
    return;
  }

  pendingFile = file; // сохраняем для дальнейшей загрузки

  // Визуальное отображение выбранного изображения
  const reader = new FileReader();
  reader.onload = function(e) {
    uploadIcon.style.display = 'none';

    // Удаляем предыдущий превью, если есть
    let existingImg = document.getElementById('imgPreview');
    if (existingImg) {
      existingImg.remove();
    }
    const imgPreview = document.createElement('img');
    imgPreview.id = 'imgPreview';
    imgPreview.src = e.target.result;
    imgPreview.style.maxWidth = '100%';
    imgPreview.style.maxHeight = '100%';

    dropZone.innerHTML = '';
    dropZone.appendChild(imgPreview);
  };
  reader.readAsDataURL(file);
}

// Обработка нажатия на кнопку "BROWSE YOUR FILE"
document.getElementById('browseBtn').addEventListener('click', () => {
  if (!pendingFile) {
    alert('Please select a file first.');
    return;
  }
  uploadSelectedFile();
});

// Функция загрузки файла по кнопке
async function uploadSelectedFile() {
  if (!pendingFile) {
    alert('No file selected.');
    return;
  }

  const data = await uploadFile(pendingFile);
  if (data && data.path) {
    const uploadedUrl = window.location.origin + '/' + data.path;
    displayLink(uploadedUrl);
  }
}

// Функция для отправки файла на сервер
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });
    if (!response.ok) {
      throw new Error(`Ошибка сервера: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    alert('Ошибка при загрузке файла: ' + error.message);
    return null;
  }
}

// Обработчик для кнопки "COPY"
document.querySelector('.generation .copy').addEventListener('click', () => {
  const url = document.querySelector('.generation .name').textContent.trim();
  if (url) {
    navigator.clipboard.writeText(url).then(() => {
      alert('Ссылка скопирована!');
    }).catch(err => {
      alert('Не удалось скопировать ссылку');
      console.error('Clipboard error:', err);
    });
  }
});

function displayLink(url) {
  const nameDiv = document.querySelector('.generation .name');
  const copyBtn = document.querySelector('.generation .copy');

  nameDiv.textContent = url;
}