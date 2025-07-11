let pageNum = 1;
let pagesCnt = 0;
let itemsCnt = 0;
let total = 0;

// Вывод всплывашки с сообщениями
const onAlert = (text, type='success', time=3000) => {
        myAlert.innerText = text;
        myAlert.classList.add('active', type);
    setTimeout(() => {
        myAlert.innerText = '';
        myAlert.classList.remove('active', type);
    }, time);
};

// Обновление пагинации
const updatePagination = () => {
    const pagination = document.getElementById("pagination");
    const pageField = document.getElementById("page");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    pageField.innerText = `${pageNum} из ${pagesCnt}`;
    prevBtn.classList.remove('disabled');
    nextBtn.classList.remove('disabled');
    if (pageNum === pagesCnt) {
        nextBtn.classList.add('disabled');
    }
    if (pageNum === 1) {
        prevBtn.classList.add('disabled');
    }

    if (total <= 10) {
        pagination.classList.add('hide')
    } else {
        pagination.classList.remove('hide')
    }
};

// Получение списка фоток от сервера
const fetchList = async () => {
    try {
        const res = await fetch(`/get-images?page=${pageNum}`);

        if (res.ok) {
            const resJson = await res.json();
            const list = resJson.list;
            total = resJson.total;
            pagesCnt = !total || total < 10 ? 1 : total % 10 ? ~~(total / 10) + 1 : ~~(total / 10);
            itemsCnt = list.length;
            updatePagination();

            return list;
        } else {
            const resJson = await res.json();
            onAlert(resJson.error || "Ошибка загрузки", "error");
        }
    } catch (err) {
        onAlert("Ошибка сервера", "error");
    }
};

// Генерация списка фотографий
const renderList = (list) => {
    const tbody = document.getElementById("tbody");

    list.forEach((i => {
        const tr = document.createElement("tr");
        tbody.appendChild(tr);
        // td Ссылка
        const link = document.createElement("a");
        link.href = `http://localhost/images/${i.filename}.${i.file_type}`;
        link.target = '_blank';
        link.classList.add('link');
        link.textContent = `${i.filename}.${i.file_type}`;
        const tdLink = document.createElement("td");
        tdLink.classList.add('td', 'url');
        tdLink.appendChild(link);
        tr.appendChild(tdLink);
        // td Имя
        const img = document.createElement("img");
        img.src = 'img/img.svg';
        img.alt = 'img';
        const tdName = document.createElement("td");
        tdName.classList.add('td', 'name');
        tdName.append(img, i.original_name.substring(0, i.original_name.lastIndexOf('.')));
        tr.appendChild(tdName);
        // td Размер
        const tdSize = document.createElement("td");
        tdSize.classList.add('td', 'size');
        const size = i.size > 1000000 ? `${(i.size / 1024 / 1024).toFixed(2)}Мб` : `${(i.size / 1024).toFixed(2)}Кб`
        tdSize.append(size);
        tr.appendChild(tdSize);
        // td Дата
        const tdDate = document.createElement("td");
        tdDate.classList.add('td', 'date');
        tdDate.append(i.upload_time);
        tr.appendChild(tdDate);
        // td Тип
        const tdType = document.createElement("td");
        tdType.classList.add('td', 'type');
        tdType.append(i.file_type);
        tr.appendChild(tdType);
        // td Удаление
        const icon = document.createElement("img");
        icon.src = 'img/delete.svg';
        icon.alt = 'delete';
        const button = document.createElement("button");
        button.classList.add('deleteBtn');
        button.addEventListener("click", () => onDelete(i.id));
        button.appendChild(icon);
        const tdDelete = document.createElement("td");
        tdDelete.classList.add('td', 'delete');
        tdDelete.appendChild(button);
        tr.appendChild(tdDelete);
    }));
};

// Обновление списка фотографий
const onListUpdate = async () => {
    const table = document.getElementById("table");
    const tbody = document.getElementById("tbody");
    const empty = document.getElementById("empty");
    const list = await fetchList();
    tbody.innerText = '';
    if (list.length) {
        renderList(list);
        empty.classList.add('hide');
        table.classList.remove('hide');
    } else {
        empty.classList.remove('hide');
        table.classList.add('hide');
    }
};

// Листалка назад по постраничной навигации
const onPrev = async () => {
    if (pageNum === 1) return;
    pageNum--;
    await onListUpdate();
}

// Листалка вперед по постраничной навигации
const onNext = async() => {
    if (pageNum === pagesCnt) return;
    pageNum++;
    await onListUpdate();
}

// Удаление элемента из списка
const onDelete = async (id) => {
    try {
        const res = await fetch('/images', { method: 'DELETE', body: id });

        if (res.ok) {
            if (itemsCnt === 1) {
                pageNum--;
            }
            await onListUpdate();
            onAlert("Файл успешно удален", "success");
        } else {
            onAlert("Ошибка удаления файла", "error");
        }
    } catch (err) {
        onAlert("Ошибка сервера", "error");
    }
};

window.onload = async function() {
    await onListUpdate();
};