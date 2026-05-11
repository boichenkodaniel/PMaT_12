# Задание 9. Аналитический SQL-запрос для библиотечной системы

## Постановка задачи

Написать сложный аналитический SQL-запрос для PostgreSQL, который выводит **топ-5 самых популярных авторов за текущий год** на основе количества выдач их книг. При этом учитываются только те читатели, у которых **нет текущих задолженностей**.

Результат должен содержать:
- имя автора;
- общее количество выданных книг;
- средний срок (в днях), на который брали его произведения.

---

## Расширение схемы данных

Для выполнения запроса логически расширяем существующую базу (`authors`, `books`) двумя таблицами:

### Таблица `readers` (читатели)

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | `SERIAL PRIMARY KEY` | Идентификатор читателя |
| `full_name` | `VARCHAR(200) NOT NULL` | ФИО читателя |
| `registered_at` | `TIMESTAMP DEFAULT now()` | Дата регистрации |

### Таблица `loans` (выдачи книг)

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | `SERIAL PRIMARY KEY` | Идентификатор выдачи |
| `book_id` | `INTEGER NOT NULL REFERENCES books(id)` | Ссылка на книгу |
| `reader_id` | `INTEGER NOT NULL REFERENCES readers(id)` | Ссылка на читателя |
| `loaned_at` | `TIMESTAMP NOT NULL` | Дата и время выдачи |
| `due_date` | `DATE NOT NULL` | Плановая дата возврата |
| `returned_at` | `TIMESTAMP` | Фактическая дата возврата (`NULL` — книга ещё не возвращена) |

**Индексы для производительности:**
```sql
CREATE INDEX ix_loans_book_id ON loans(book_id);
CREATE INDEX ix_loans_reader_id ON loans(reader_id);
CREATE INDEX ix_loans_loaned_at ON loans(loaned_at);
CREATE INDEX ix_loans_returned_at ON loans(returned_at) WHERE returned_at IS NULL;
```

---

## SQL-запрос

```sql
-- ============================================================
-- Топ-5 авторов по популярности за текущий год
-- Условие: только читатели без текущих просрочек
-- ============================================================

WITH eligible_readers AS (
    /* Шаг 1. Отбираем читателей без текущих задолженностей.
       Задолженность — это невозвращённая книга (returned_at IS NULL),
       у которой срок возврата уже истёк (due_date < CURRENT_DATE).
       Используем NOT EXISTS вместо NOT IN для корректной работы с NULL
       и лучшей читаемости плана выполнения. */
    SELECT
        r.id AS reader_id
    FROM readers r
    WHERE NOT EXISTS (
        SELECT 1
        FROM loans l_overdue
        WHERE l_overdue.reader_id = r.id
          AND l_overdue.returned_at IS NULL
          AND l_overdue.due_date < CURRENT_DATE
    )
),
year_loans AS (
    /* Шаг 2. Соединяем выдачи текущего года с отфильтрованными
       читателями и книгами, вычисляя срок выдачи в днях.
       Для возвращённых книг берём фактический срок;
       для ещё не возвращённых — плановый (due_date - loaned_at). */
    SELECT
        b.author_id,
        COALESCE(
            (l.returned_at::date - l.loaned_at::date),
            (l.due_date - l.loaned_at::date)
        ) AS loan_period_days
    FROM loans l
    INNER JOIN eligible_readers er
        ON l.reader_id = er.reader_id
    INNER JOIN books b
        ON l.book_id = b.id
    WHERE l.loaned_at >= DATE_TRUNC('year', CURRENT_DATE)
      AND l.loaned_at <  DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year'
)
/* Шаг 3. Агрегируем данные по авторам, считаем количество выдач
   и средний срок, округляем до 2 знаков. */
SELECT
    a.name  AS author_name,
    COUNT(*) AS total_books_loaned,
    ROUND(AVG(yl.loan_period_days), 2) AS avg_loan_period_days
FROM year_loans yl
INNER JOIN authors a
    ON yl.author_id = a.id
GROUP BY
    a.id,
    a.name
ORDER BY
    total_books_loaned DESC
LIMIT 5;
```

---

## Пошаговое объяснение логики

### 1. CTE `eligible_readers` — фильтрация читателей

```sql
SELECT r.id AS reader_id
FROM readers r
WHERE NOT EXISTS (
    SELECT 1
    FROM loans l_overdue
    WHERE l_overdue.reader_id = r.id
      AND l_overdue.returned_at IS NULL
      AND l_overdue.due_date < CURRENT_DATE
)
```

**Что происходит:**
- Для каждой строки из `readers` проверяем, есть ли у этого читателя **хотя бы одна** просроченная и невозвращённая книга.
- Условия просрочки:
  - `returned_at IS NULL` — книга ещё на руках;
  - `due_date < CURRENT_DATE` — плановая дата возврата уже прошла.
- `NOT EXISTS` возвращает `TRUE`, если подзапрос **не нашёл** таких записей. Эти читатели и попадают в итоговый набор.

**Почему `NOT EXISTS`, а не `LEFT JOIN` + `IS NULL`:**
- `NOT EXISTS` семантически точнее выражает намерение («нет таких записей»).
- PostgreSQL часто строит более эффективный план выполнения (Semi Join / Anti Join).
- Не требуется обработка дубликатов, которые могут возникнуть при соединении.

---

### 2. CTE `year_loans` — выдачи текущего года с расчётом срока

```sql
SELECT
    b.author_id,
    COALESCE(
        (l.returned_at::date - l.loaned_at::date),
        (l.due_date - l.loaned_at::date)
    ) AS loan_period_days
FROM loans l
INNER JOIN eligible_readers er ON l.reader_id = er.reader_id
INNER JOIN books b ON l.book_id = b.id
WHERE l.loaned_at >= DATE_TRUNC('year', CURRENT_DATE)
  AND l.loaned_at <  DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year'
```

**Что происходит:**

#### 2.1. Фильтрация по времени
- `DATE_TRUNC('year', CURRENT_DATE)` возвращает **1 января текущего года** (например, `2026-01-01`).
- Верхняя граница — `+ INTERVAL '1 year'`, то есть `2027-01-01`.
- Диапазон `[2026-01-01, 2027-01-01)` захватывает все выдачи текущего года.

#### 2.2. Соединение с `eligible_readers`
- `INNER JOIN` оставляет только выдачи тех читателей, которые прошли фильтр на отсутствие задолженностей.

#### 2.3. Соединение с `books`
- Получаем `author_id` для каждой выдачи, чтобы потом агрегировать по авторам.

#### 2.4. Расчёт `loan_period_days`
```sql
COALESCE(
    (l.returned_at::date - l.loaned_at::date),   -- вариант A: книга уже возвращена
    (l.due_date - l.loaned_at::date)             -- вариант B: книга ещё не возвращена
)
```
- `COALESCE` возвращает первый не-`NULL` аргумент.
- Если книга **возвращена** (`returned_at IS NOT NULL`), считаем фактический срок: дата возврата минус дата выдачи.
- Если книга **ещё не возвращена**, используем плановый срок: `due_date - loaned_at`.
- Операнды приведены к типу `date`, чтобы результат был в **целых днях**.

---

### 3. Основной `SELECT` — агрегация по авторам

```sql
SELECT
    a.name  AS author_name,
    COUNT(*) AS total_books_loaned,
    ROUND(AVG(yl.loan_period_days), 2) AS avg_loan_period_days
FROM year_loans yl
INNER JOIN authors a ON yl.author_id = a.id
GROUP BY a.id, a.name
ORDER BY total_books_loaned DESC
LIMIT 5;
```

**Что происходит:**

#### 3.1. Соединение с `authors`
- По `author_id` из CTE `year_loans` подтягиваем имя автора.
- `INNER JOIN` гарантирует, что в результат попадут только авторы с хотя бы одной выдачей (авторы без выдач автоматически отфильтровываются).

#### 3.2. `GROUP BY a.id, a.name`
- Группировка идёт по уникальному идентификатору автора (`id`) и его имени.
- `a.id` входит в группировку, потому что является первичным ключом и однозначно определяет автора; это также позволяет избежать неопределённости, если бы у двух авторов совпали имена (в нашей схеме `name` имеет `UNIQUE`, но в общем случае `id` надёжнее).

#### 3.3. Агрегатные функции
- **`COUNT(*)`** — считает количество строк в каждой группе, то есть общее число выдач книг данного автора. Используем `COUNT(*)`, а не `COUNT(book_id)`, поскольку на этом этапе каждая строка уже представляет одну выдачу.
- **`AVG(yl.loan_period_days)`** — вычисляет среднее арифметическое срока выдачи (в днях) для всех книг автора.
- **`ROUND(..., 2)`** — округляет среднее значение до двух десятичных знаков для читаемости.

#### 3.4. Сортировка и ограничение
- **`ORDER BY total_books_loaned DESC`** — авторы с наибольшим числом выдач идут первыми.
- **`LIMIT 5`** — оставляем только топ-5 записей.

---

## Пример результата

| author_name | total_books_loaned | avg_loan_period_days |
|-------------|-------------------:|---------------------:|
| Лев Толстой | 847 | 18.45 |
| Фёдор Достоевский | 692 | 21.30 |
| Александр Пушкин | 554 | 14.80 |
| Михаил Булгаков | 498 | 16.20 |
| Антон Чехов | 421 | 12.55 |

---

## Оптимизация и рекомендации

1. **Индексы:**
   - `CREATE INDEX ix_loans_loaned_at ON loans(loaned_at);` — ускоряет фильтрацию `WHERE l.loaned_at >= ...`.
   - `CREATE INDEX ix_loans_overdue ON loans(reader_id) WHERE returned_at IS NULL AND due_date < CURRENT_DATE;` — частичный индекс для быстрой проверки `NOT EXISTS`.
   - `CREATE INDEX ix_books_author_id ON books(author_id);` — уже создан в миграции `002`.

2. **Материализация CTE:**
   - Если таблица `loans` содержит миллионы записей, PostgreSQL автоматически материализует CTE. При необходимости можно добавить `MATERIALIZED` / `NOT MATERIALIZED` для ручного контроля.

3. **Альтернатива `NOT EXISTS`:**
   - В некоторых случаях коррелированный подзапрос можно заменить на `LEFT JOIN` с проверкой `WHERE l_overdue.id IS NULL`, но `NOT EXISTS` чаще всего предпочтительнее в PostgreSQL благодаря оптимизатору.

4. **Обработка часовых поясов:**
   - Если `loaned_at` хранится в `TIMESTAMP WITH TIME ZONE`, сравнение с `DATE_TRUNC('year', CURRENT_DATE)` работает корректно, так как `CURRENT_DATE` возвращает дату в текущей временной зоне сессии.
