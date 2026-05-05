"""
Quack Teacher — AI учит утку, утка учит тебя.
ИНТЕРАКТИВНАЯ СИСТЕМА УРОКОВ на 6+ языках.

Каждый урок:
  1. Объяснение (на твоём языке)
  2. Пример кода
  3. Задание
  4. Проверка ответа
  5. Подсказки если застрял

НЕ ЛОМАЕТ ПЕНТАГОН — СПРАШИВАЕТ.
Если чё непонятно, утка сама переспросит.

КРЯЯЯЯ! ОБРАЗОВАНИЕ СВОБОДНО!

Учителя:
  🇷🇺 Марья Ивановна — строгая но справедливая, по ФГОС, "Так, ребята..."
  🇬🇧 Mr. Quackington — chill American CS teacher, "Hey guys, so basically..."
  🇵🇱 Pan Kaczor — energiczny nauczyciel, "Dobra, słuchajcie..."
  🇸🇰 Pán Kačka — trpezlivý učiteľ, "Tak, deti..."
  🇺🇦 Пані Качка — мудра вчителька, "Так, діти..."
"""
import time
import re
from typing import Optional
from .quack import run_quack, KEYWORDS, TRUTHY_WORDS


# ═══════════════════════════════════════════════════════
# Teacher Personalities — each language = unique character
# ═══════════════════════════════════════════════════════

TEACHER_PERSONAS = {
    "ru": {
        "name": "Марья Ивановна Кряквина",
        "title": "Учитель информатики, высшая категория",
        "avatar": "👩‍🏫",
        "style": "strict_but_fair",
        "catchphrase": "Так, ребята, открываем тетради...",
        "praise": [
            "Молодец! Пятёрка! 🌟",
            "Отлично! Так держать!",
            "Верно! Видишь, всё просто!",
            "Правильно! Горжусь тобой!",
            "Класс! Поставлю в журнал пять!",
        ],
        "scold": [
            "Так, не торопись. Подумай ещё раз.",
            "Ошибка! Но ничего, на ошибках учатся.",
            "Нет-нет-нет. Посмотри внимательнее на пример.",
            "Тут ошибка. Давай разберёмся вместе.",
            "Не сдавайся! У тебя получится!",
        ],
        "fgos_note": "Соответствует ФГОС ООО по информатике, раздел 'Алгоритмизация и программирование'",
        "grade_system": {
            5: "Отлично! (с первой попытки)",
            4: "Хорошо (2-3 попытки)",
            3: "Удовлетворительно (нужна практика)",
            2: "Надо подтянуть! Приходи на допы.",
        },
    },
    "en": {
        "name": "Mr. Quackington",
        "title": "CS Teacher, Silicon Valley style",
        "avatar": "🧑‍💻",
        "style": "chill_mentor",
        "catchphrase": "Hey guys, so basically...",
        "praise": [
            "Nailed it! You're a natural! 🎯",
            "Awesome sauce! That's the way!",
            "Boom! First try! You're cracked!",
            "Yooo that's clean code right there!",
            "GG! You're built different! 🔥",
        ],
        "scold": [
            "No worries, let's debug this together.",
            "Hmm, close but not quite. Check the syntax?",
            "Ah almost! Small typo maybe?",
            "That's a good attempt! Just needs a tweak.",
            "No cap, you're almost there. One more try!",
        ],
        "fgos_note": "Aligned with AP Computer Science Principles curriculum",
        "grade_system": {
            5: "A+ (First try, absolute legend)",
            4: "A  (Solid work!)",
            3: "B  (Good effort, keep grinding)",
            2: "C  (Need more practice, you got this!)",
        },
    },
    "pl": {
        "name": "Pan Kaczor Programista",
        "title": "Nauczyciel informatyki, entuzjasta",
        "avatar": "🦆",
        "style": "energetic",
        "catchphrase": "Dobra, słuchajcie, to jest mega proste!",
        "praise": [
            "Brawo! Piątka z plusem! 🌟",
            "Super robota! Tak trzymaj!",
            "Dokładnie tak! Widzisz, że potrafisz!",
            "Świetnie! Jestem dumny!",
            "No i pięknie! KWA KWA! 🦆",
        ],
        "scold": [
            "Spokojnie, spróbuj jeszcze raz.",
            "Prawie dobrze! Mały błąd.",
            "Nie tym razem, ale nie poddawaj się!",
            "Hmm, coś nie tak. Sprawdźmy razem.",
            "Błąd — ale to normalne! Wszyscy się uczą.",
        ],
        "fgos_note": "Zgodne z podstawą programową informatyki",
        "grade_system": {
            5: "Celujący! (pierwsza próba)",
            4: "Bardzo dobry (2-3 próby)",
            3: "Dostateczny (trzeba poćwiczyć)",
            2: "Poprawka! Przyjdź na konsultacje.",
        },
    },
    "sk": {
        "name": "Pán Kačka",
        "title": "Učiteľ informatiky, trpezlivý mentore",
        "avatar": "🦆",
        "style": "patient",
        "catchphrase": "Tak, deti, poďme na to pomaly...",
        "praise": [
            "Výborne! Jednotka! 🌟",
            "Super práca! Tak ďalej!",
            "Presne tak! Vidíš, ide to!",
            "Skvelé! Som na teba hrdý!",
            "Paráda! KVÁK KVÁK! 🦆",
        ],
        "scold": [
            "Nevadí, skús ešte raz.",
            "Takmer správne! Malá chybička.",
            "Tentokrát nie, ale nevzdávaj sa!",
            "Hmm, niečo nie je v poriadku. Pozrime sa spolu.",
            "Chyba — ale to je normálne! Každý sa učí.",
        ],
        "fgos_note": "V súlade so štátnym vzdelávacím programom",
        "grade_system": {
            5: "Výborný! (prvý pokus)",
            4: "Chválitebný (2-3 pokusy)",
            3: "Dobrý (treba precvičiť)",
            2: "Dostatočný! Príď na doučovanie.",
        },
    },
    "ua": {
        "name": "Пані Качка",
        "title": "Вчитель інформатики, мудра наставниця",
        "avatar": "🦆",
        "style": "wise",
        "catchphrase": "Так, діти, давайте розбиратися...",
        "praise": [
            "Молодець! Дванадцять! 🌟",
            "Чудово! Так тримати!",
            "Саме так! Бачиш, все просто!",
            "Правильно! Горджуся тобою!",
            "Прекрасно! КРЯК КРЯК! 🦆",
        ],
        "scold": [
            "Нічого, спробуй ще раз.",
            "Майже правильно! Маленька помилка.",
            "Не цього разу, але не здавайся!",
            "Хмм, щось не так. Давай розберемося разом.",
            "Помилка — але це нормально! Всі вчаться.",
        ],
        "fgos_note": "Відповідає Державному стандарту базової освіти",
        "grade_system": {
            5: "12 балів! (перша спроба)",
            4: "10 балів (2-3 спроби)",
            3: "7 балів (потрібна практика)",
            2: "4 бали! Приходь на додаткові.",
        },
    },
}


# ═══════════════════════════════════════════════════════
# COURSES — Real school curricula tracks
# ФГОС 9-11 (ОГЭ/ЕГЭ боль), AP CS (American pain), Zoomer
# ═══════════════════════════════════════════════════════

COURSES = {
    # ── ФГОС ОГЭ (9 класс) — Первая школьная БОЛЬ ──
    "fgos_oge": {
        "id": "fgos_oge",
        "title": "ФГОС: ОГЭ Информатика (9 класс)",
        "title_en": "Russian OGE Computer Science (Grade 9)",
        "icon": "🇷🇺📝",
        "description": "15 заданий, 150 минут чистой боли. Системы счисления, логика, алгоритмы, ПРОГРАММИРОВАНИЕ.",
        "teacher": "ru",
        "lessons": [
            {
                "id": 1, "title": "Системы счисления: двоичная",
                "explanation": (
                    "Компьютер считает в ДВОИЧНОЙ системе — только 0 и 1.\n"
                    "13 в десятичной = 1101 в двоичной.\n"
                    "Как перевести: делим на 2, записываем остатки снизу вверх.\n"
                    "13÷2=6 ост.1, 6÷2=3 ост.0, 3÷2=1 ост.1, 1÷2=0 ост.1 → 1101"
                ),
                "example": '''# Перевод числа в двоичную систему на Quack
пусть число = 13
пусть результат = ""
пусть н = число
пока н > 0 {
    пусть остаток = н % 2
    результат = текст(остаток) + результат
    н = целое(н / 2)
}
кряк(число, "в двоичной =", результат)''',
                "task": "Напиши программу которая переводит число 42 в двоичную систему.",
                "check": lambda code: "42" in code and ("%" in code or "остаток" in code or "binary" in code),
                "expected_contains": "101010",
                "hints": ["Дели на 2 и собирай остатки", "42÷2=21(0), 21÷2=10(1), 10÷2=5(0), 5÷2=2(1), 2÷2=1(0), 1÷2=0(1) → 101010"],
                "oge_task": "Задание 1 ОГЭ",
            },
            {
                "id": 2, "title": "Системы счисления: восьмеричная и шестнадцатеричная",
                "explanation": (
                    "Восьмеричная (0-7): делим на 8.\n"
                    "Шестнадцатеричная (0-F): делим на 16. A=10, B=11, C=12, D=13, E=14, F=15.\n"
                    "Лайфхак: группируй двоичные по 3 (восьм.) или по 4 (шестн.).\n"
                    "1101 0101₂ = D5₁₆ = 325₈"
                ),
                "example": '''# Перевод в любую систему счисления
функция перевести(число, основание) {
    пусть результат = ""
    пусть символы = "0123456789ABCDEF"
    пусть н = число
    пока н > 0 {
        пусть остаток = н % основание
        результат = текст(остаток) + результат
        н = целое(н / основание)
    }
    вернуть результат
}
кряк("255 в двоичной:", перевести(255, 2))
кряк("255 в восьмеричной:", перевести(255, 8))
кряк("255 в шестнадцатеричной:", перевести(255, 16))''',
                "task": "Переведи число 200 в восьмеричную и шестнадцатеричную системы.",
                "check": lambda code: "200" in code and ("8" in code or "16" in code),
                "hints": ["200÷8=25(0), 25÷8=3(1), 3÷8=0(3) → 310₈", "200÷16=12(8), 12÷16=0(12=C) → C8₁₆"],
                "oge_task": "Задание 1 ОГЭ",
            },
            {
                "id": 3, "title": "Булева алгебра: И, ИЛИ, НЕ",
                "explanation": (
                    "Три базовые операции:\n"
                    "  И (AND, ∧): оба true → true. Иначе false.\n"
                    "  ИЛИ (OR, ∨): хотя бы одно true → true.\n"
                    "  НЕ (NOT, ¬): наоборот. true→false, false→true.\n\n"
                    "Таблица истинности:\n"
                    "  A=1 B=1: A∧B=1, A∨B=1\n"
                    "  A=1 B=0: A∧B=0, A∨B=1\n"
                    "  A=0 B=1: A∧B=0, A∨B=1\n"
                    "  A=0 B=0: A∧B=0, A∨B=0"
                ),
                "example": '''# Таблица истинности на Quack
кряк("A | B | A и B | A или B | не A")
кряк("──────────────────────────────")
для a_val в [0, 1] {
    для b_val в [0, 1] {
        пусть and_r = a_val == 1 и_и b_val == 1
        пусть or_r = a_val == 1 или b_val == 1
        пусть not_r = не (a_val == 1)
        кряк(a_val, "|", b_val, "|  ", and_r, "  |   ", or_r, "   |", not_r)
    }
}''',
                "task": "Вычисли: (1 ИЛИ 0) И НЕ(0 ИЛИ 0). Выведи результат.",
                "check": lambda code: ("или" in code.lower() or "or" in code.lower()) and ("не" in code.lower() or "not" in code.lower()),
                "expected_contains": "True",
                "hints": ["(1 ИЛИ 0) = 1, (0 ИЛИ 0) = 0, НЕ(0) = 1, 1 И 1 = 1 → True"],
                "oge_task": "Задание 2 ОГЭ",
            },
            {
                "id": 4, "title": "Алгоритмы: линейный, ветвление, цикл",
                "explanation": (
                    "3 базовых алгоритмических конструкции:\n"
                    "1. ЛИНЕЙНЫЙ — команды подряд, без условий\n"
                    "2. ВЕТВЛЕНИЕ — если/иначе, выбор пути\n"
                    "3. ЦИКЛ — повторение пока условие true\n\n"
                    "ОГЭ любит: 'Дан алгоритм для исполнителя. Что будет результатом?'\n"
                    "Трюк: трассировка — выписывай значения переменных на каждом шаге."
                ),
                "example": '''# Трассировка алгоритма — КЛЮЧЕВОЙ НАВЫК ОГЭ
# Что выведет программа?
пусть а = 2
пусть б = 3
пока а < 20 {
    а = а + б
    б = б + 1
}
кряк("а =", а, "б =", б)
# Трассировка:
# а=2, б=3 → а=5, б=4
# а=5, б=4 → а=9, б=5
# а=9, б=5 → а=14, б=6
# а=14, б=6 → а=20, б=7 → СТОП (а >= 20)
# Ответ: а=20, б=7''',
                "task": "Дано: а=1, б=1. Цикл: пока а < 100: а = а * 2 + б, б = б + 1. Что выведется?",
                "check": lambda code: "100" in code and ("пока" in code.lower() or "while" in code.lower()),
                "hints": ["а=1,б=1→а=3,б=2→а=8,б=3→а=19,б=4→а=42,б=5→а=89,б=6→а=184,б=7→стоп"],
                "oge_task": "Задания 5-6 ОГЭ",
            },
            {
                "id": 5, "title": "Массивы и поиск",
                "explanation": (
                    "Массив (список) — набор элементов с индексами.\n"
                    "Индексация с 0: список[0] = первый элемент.\n\n"
                    "Типичные задачи ОГЭ:\n"
                    "  - Найти максимум/минимум\n"
                    "  - Подсчитать количество элементов по условию\n"
                    "  - Найти сумму чётных/нечётных"
                ),
                "example": '''# Поиск максимума — задание ОГЭ
пусть данные = [4, 7, 2, 9, 1, 5, 8, 3]
пусть макс_значение = данные[0]
пусть макс_индекс = 0

для и в диапазон(длина(данные)) {
    если данные[и] > макс_значение {
        макс_значение = данные[и]
        макс_индекс = и
    }
}
кряк("Максимум:", макс_значение, "на позиции", макс_индекс)

# Подсчёт чётных
пусть счётчик = 0
для элемент в данные {
    если элемент % 2 == 0 {
        счётчик = счётчик + 1
    }
}
кряк("Чётных элементов:", счётчик)''',
                "task": "Дан список [12, 5, 8, 3, 17, 6, 2, 11]. Найди сумму элементов больше 10.",
                "check": lambda code: "[" in code and "10" in code and ("сумм" in code.lower() or "sum" in code.lower() or "+" in code),
                "expected_contains": "40",
                "hints": ["12 + 17 + 11 = 40", "Цикл по списку, если элемент > 10 → прибавляем к сумме"],
                "oge_task": "Задания 13-15 ОГЭ",
            },
        ],
    },

    # ── ФГОС ЕГЭ (10-11 класс) — МАКСИМАЛЬНАЯ БОЛЬ ──
    "fgos_ege": {
        "id": "fgos_ege",
        "title": "ФГОС: ЕГЭ Информатика (10-11 класс, углублённый)",
        "title_en": "Russian EGE Computer Science (Grades 10-11, Advanced)",
        "icon": "🇷🇺🔥",
        "description": "27 заданий, 235 минут АДСКОГО ПРОГРАММИРОВАНИЯ. Рекурсия, теория игр, обработка файлов.",
        "teacher": "ru",
        "lessons": [
            {
                "id": 1, "title": "Рекурсия — функция вызывает сама себя",
                "explanation": (
                    "Рекурсия = функция вызывает сама себя с меньшими аргументами.\n"
                    "ОБЯЗАТЕЛЬНО: базовый случай (когда остановиться)!\n"
                    "Без базового случая → бесконечная рекурсия → 💀\n\n"
                    "ЕГЭ задание 16: 'Определите результат вызова F(n)'\n"
                    "Трюк: рисуй дерево вызовов!"
                ),
                "example": '''# Рекурсивная функция — задание 16 ЕГЭ
функция F(н) {
    если н <= 1 {
        вернуть 1
    }
    вернуть F(н - 1) + F(н - 2)
}

# Дерево вызовов F(5):
# F(5) = F(4) + F(3)
# F(4) = F(3) + F(2)
# F(3) = F(2) + F(1)
# F(2) = F(1) + F(0) = 1 + 1 = 2
# F(3) = 2 + 1 = 3
# F(4) = 3 + 2 = 5
# F(5) = 5 + 3 = 8

для и в диапазон(8) {
    кряк("F(", и, ") =", F(и))
}''',
                "task": "Напиши рекурсивную функцию: F(n) = 2*F(n-1) + n, F(0) = 1. Вычисли F(5).",
                "check": lambda code: ("функция" in code.lower() or "fn" in code.lower() or "rizz" in code.lower()) and ("F(" in code or "f(" in code),
                "expected_contains": "67",
                "hints": ["F(0)=1, F(1)=2*1+1=3, F(2)=2*3+2=8, F(3)=2*8+3=19, F(4)=2*19+4=42, F(5)=2*42+5=89... wait let me recalc"],
                "ege_task": "Задание 16 ЕГЭ",
            },
            {
                "id": 2, "title": "Сортировка — пузырёк и за пределами",
                "explanation": (
                    "Сортировка пузырьком — самая простая, но медленная O(n²).\n"
                    "Идея: проходим по списку, меняем соседей если они в неправильном порядке.\n"
                    "Повторяем пока массив не отсортирован.\n\n"
                    "ЕГЭ спрашивает: сколько обменов? какой результат после K проходов?"
                ),
                "example": '''# Сортировка пузырьком на Quack
пусть данные = [64, 34, 25, 12, 22, 11, 90]
кряк("До сортировки:", данные)

пусть н = длина(данные)
для и в диапазон(н) {
    для й в диапазон(н - и - 1) {
        если данные[й] > данные[й + 1] {
            # Обмен
            пусть врем = данные[й]
            данные[й] = данные[й + 1]
            данные[й + 1] = врем
        }
    }
}
кряк("После сортировки:", данные)''',
                "task": "Отсортируй список [5, 3, 8, 1, 9, 2] пузырьком. Подсчитай количество обменов.",
                "check": lambda code: "[" in code and ("обмен" in code.lower() or "swap" in code.lower() or "врем" in code.lower()),
                "hints": ["Каждый раз когда меняем местами — увеличиваем счётчик обменов"],
                "ege_task": "Задания 17, 24 ЕГЭ",
            },
            {
                "id": 3, "title": "Теория игр — кто выигрывает?",
                "explanation": (
                    "САМЫЕ СТРАШНЫЕ задачи ЕГЭ (25-26)!\n"
                    "Два игрока по очереди берут камни/делают ходы.\n"
                    "Нужно определить: кто выиграет при оптимальной игре.\n\n"
                    "Алгоритм:\n"
                    "1. Позиция ПРОИГРЫШНАЯ если все ходы ведут в выигрышную\n"
                    "2. Позиция ВЫИГРЫШНАЯ если есть хоть один ход в проигрышную\n"
                    "3. Строим таблицу с конца!"
                ),
                "example": '''# Теория игр — задание 25 ЕГЭ
# Куча камней. Ход: взять 1 или 2 камня. Кто берёт последний — победил.
функция кто_победит(камни) {
    # Таблица: "В" = выигрыш 1го, "П" = проигрыш 1го
    пусть таблица = []
    для и в диапазон(камни + 1) {
        таблица = добавить(таблица, "?")
    }
    таблица[0] = "П"
    для и в диапазон(1, камни + 1) {
        пусть можно_проиграть = ложь
        если и >= 1 {
            если таблица[и - 1] == "П" {
                можно_проиграть = истина
            }
        }
        если и >= 2 {
            если таблица[и - 2] == "П" {
                можно_проиграть = истина
            }
        }
        если можно_проиграть {
            таблица[и] = "В"
        } иначе {
            таблица[и] = "П"
        }
    }
    вернуть таблица
}

пусть результат = кто_победит(10)
для и в диапазон(11) {
    кряк("  Камней:", и, "→", результат[и])
}''',
                "task": "Камней 15, ход: взять 1, 2 или 3. Кто победит — первый или второй?",
                "check": lambda code: "15" in code and ("камн" in code.lower() or "stone" in code.lower() or "pile" in code.lower()),
                "hints": ["При делении на 4: если остаток 0 → проигрыш первого, иначе выигрыш"],
                "ege_task": "Задания 25-26 ЕГЭ",
            },
        ],
    },

    # ── AP CS PRINCIPLES — American Chill Mode ──
    "ap_csp": {
        "id": "ap_csp",
        "title": "AP Computer Science Principles",
        "title_en": "AP CSP — The Conceptual One",
        "icon": "🇺🇸💡",
        "description": "Big Ideas: data, algorithms, the internet. 70 MCQ + Create Task. No specific language required.",
        "teacher": "en",
        "lessons": [
            {
                "id": 1, "title": "Binary & Data Representation",
                "explanation": (
                    "Everything in a computer is binary — 0s and 1s.\n"
                    "8 bits = 1 byte. A byte can store 0-255.\n"
                    "Text: ASCII (A=65), Unicode.\n"
                    "Colors: RGB (3 bytes = 16.7M colors).\n"
                    "Images: grid of pixels, each pixel = 3 bytes RGB."
                ),
                "example": '''# Binary conversion in Quack
fn to_binary(n) {
    let result = ""
    let num = n
    while num > 0 {
        let bit = num % 2
        result = str(bit) + result
        num = int(num / 2)
    }
    return result
}

# ASCII values
print("A =", 65, "binary:", to_binary(65))
print("Z =", 90, "binary:", to_binary(90))
print("Duck emoji needs", 4, "bytes in UTF-8!")

# RGB color
let red = 255
let green = 128
let blue = 0
print("Orange: RGB(", red, green, blue, ")")''',
                "task": "Convert the number 100 to binary and print it.",
                "check": lambda code: "100" in code and "binary" in code.lower() or "%" in code,
                "expected_contains": "1100100",
                "hints": ["100 in binary = 1100100"],
                "ap_topic": "Big Idea 2: Data",
            },
            {
                "id": 2, "title": "Algorithms — Search & Sort",
                "explanation": (
                    "Linear search: check every element. O(n).\n"
                    "Binary search: sorted list, check middle, halve. O(log n).\n\n"
                    "AP loves to ask: how many comparisons for binary search?\n"
                    "Formula: log₂(n) comparisons max.\n"
                    "1000 items → about 10 comparisons!"
                ),
                "example": '''# Linear vs Binary search
fn linear_search(data, target) {
    let steps = 0
    for i in range(len(data)) {
        steps = steps + 1
        if data[i] == target {
            print("Found at index", i, "in", steps, "steps")
            return i
        }
    }
    print("Not found after", steps, "steps")
    return -1
}

let numbers = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
print("Searching for 23 in list of", len(numbers), "items...")
linear_search(numbers, 23)
print("Binary search would take ~", 4, "steps (log2 of 10)")''',
                "task": "Create a list of 20 numbers and find element 15 using linear search. Count the steps.",
                "check": lambda code: "20" in code or "15" in code,
                "hints": ["Create a list with range(1, 21) and search for 15"],
                "ap_topic": "Big Idea 3: Algorithms",
            },
            {
                "id": 3, "title": "Abstraction & Functions",
                "explanation": (
                    "Abstraction = hiding complexity behind a simple interface.\n"
                    "You use print() without knowing HOW it sends pixels to screen.\n"
                    "Functions = named abstractions.\n\n"
                    "AP Create Task: you MUST demonstrate abstraction.\n"
                    "Write functions that call other functions!"
                ),
                "example": '''# Abstraction layers
fn celsius_to_fahrenheit(c) {
    return c * 9 / 5 + 32
}

fn weather_report(city, temp_c) {
    let temp_f = celsius_to_fahrenheit(temp_c)
    if temp_c > 30 {
        print(city, ":", temp_c, "C /", temp_f, "F — HOT!")
    } else {
        if temp_c < 0 {
            print(city, ":", temp_c, "C /", temp_f, "F — FREEZING!")
        } else {
            print(city, ":", temp_c, "C /", temp_f, "F — nice")
        }
    }
}

weather_report("Moscow", -15)
weather_report("LA", 35)
weather_report("London", 12)''',
                "task": "Write a function that takes a test score and returns the letter grade (A/B/C/D/F).",
                "check": lambda code: ("fn " in code or "function" in code.lower() or "rizz " in code) and "return" in code.lower(),
                "hints": ["90+ = A, 80+ = B, 70+ = C, 60+ = D, else F"],
                "ap_topic": "Big Idea 3: Algorithms & Programming",
            },
        ],
    },

    # ── AP CS A — Java Pain (in Quack!) ──
    "ap_csa": {
        "id": "ap_csa",
        "title": "AP Computer Science A",
        "title_en": "AP CSA — The Hardcore Java One (but in Quack)",
        "icon": "🇺🇸🔥",
        "description": "Arrays, 2D arrays, ArrayList, loops, FRQ without IDE. Java concepts in Quack syntax.",
        "teacher": "en",
        "lessons": [
            {
                "id": 1, "title": "Arrays & Off-by-One Errors",
                "explanation": (
                    "Arrays start at index 0. Length 5 → indices 0,1,2,3,4.\n"
                    "THE #1 BUG: off-by-one error!\n"
                    "  Wrong: for i in range(len(arr) + 1) → INDEX OUT OF BOUNDS\n"
                    "  Right: for i in range(len(arr))\n\n"
                    "AP CSA FRQ loves: 'traverse the array and...'\n"
                    "Always ask: am I starting at 0? Am I stopping BEFORE length?"
                ),
                "example": '''# Array traversal — THE BREAD AND BUTTER
let scores = [85, 92, 78, 95, 88, 76, 91, 83]
print("Scores:", scores)

# Find average
let total = 0
for i in range(len(scores)) {
    total = total + scores[i]
}
let avg = total / len(scores)
print("Average:", avg)

# Count above average
let above = 0
for score in scores {
    if score > avg {
        above = above + 1
    }
}
print("Above average:", above, "out of", len(scores))''',
                "task": "Given [3, 7, 2, 8, 1, 9, 4, 6], find the two largest elements.",
                "check": lambda code: "[" in code and ("max" in code.lower() or "макс" in code.lower() or "largest" in code.lower() or ">" in code),
                "hints": ["Track first_max and second_max. If element > first_max, shift first to second."],
                "ap_topic": "Unit 4: Data Collections (30-40% of exam)",
            },
            {
                "id": 2, "title": "2D Arrays — The Grid of Pain",
                "explanation": (
                    "2D array = list of lists = grid/matrix/table.\n"
                    "Access: grid[row][col]\n"
                    "Traverse: nested loops!\n\n"
                    "AP CSA ALWAYS has a 2D array FRQ.\n"
                    "Common patterns:\n"
                    "  - Row-by-row traversal\n"
                    "  - Column-by-column traversal\n"
                    "  - Finding neighbors (up/down/left/right)"
                ),
                "example": '''# 2D Array — board operations
let board = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

# Print board
print("Board:")
for row in board {
    print(" ", row)
}

# Sum of all elements
let total = 0
for row in board {
    for elem in row {
        total = total + elem
    }
}
print("Sum:", total)

# Find specific element
let target = 5
for r in range(len(board)) {
    for c in range(len(board[r])) {
        if board[r][c] == target {
            print("Found", target, "at row", r, "col", c)
        }
    }
}''',
                "task": "Create a 3x3 board, find the sum of the diagonal elements (top-left to bottom-right).",
                "check": lambda code: "[[" in code,
                "expected_contains": "15",
                "hints": ["Diagonal: board[0][0] + board[1][1] + board[2][2]", "For a 3x3 with 1-9: 1+5+9 = 15"],
                "ap_topic": "Unit 4: Data Collections — 2D Arrays",
            },
            {
                "id": 3, "title": "String Processing — FRQ Favorite",
                "explanation": (
                    "Strings = text. index 0 to length-1.\n"
                    "Common operations: length, charAt (index), substring.\n"
                    "In Quack: len(), str[i], contains(), split().\n\n"
                    "AP CSA string FRQ patterns:\n"
                    "  - Reverse a string\n"
                    "  - Check palindrome\n"
                    "  - Count occurrences of a character"
                ),
                "example": '''# String operations
let txt = "QUACK"
print("Text:", txt, "Length:", len(txt))

# Reverse
fn reverse_str(s) {
    let result = ""
    let chars = split(s, "")
    let i = len(chars) - 1
    while i >= 0 {
        result = result + chars[i]
        i = i - 1
    }
    return result
}

print("Reversed:", reverse_str(txt))

# Palindrome check
fn is_palindrome(s) {
    let low = lower(s)
    return low == reverse_str(low)
}

print("QUACK palindrome?", is_palindrome("QUACK"))
print("RACECAR palindrome?", is_palindrome("RACECAR"))''',
                "task": "Write a function that counts how many vowels (a,e,i,o,u) are in a given string.",
                "check": lambda code: ("fn " in code or "function" in code.lower()) and ("vowel" in code.lower() or "гласн" in code.lower()),
                "hints": ["Check each character: if it's in 'aeiouAEIOU', increment counter"],
                "ap_topic": "Unit 1: Using Objects & Methods",
            },
        ],
    },

    # ── ZOOMER CRASH COURSE ──
    "zoomer": {
        "id": "zoomer",
        "title": "Zoomer Crash Course",
        "title_en": "CS but make it TikTok",
        "icon": "💅✨",
        "description": "No cap frfr programming tutorial. If this doesn't make you learn CS, nothing will bestie.",
        "teacher": "en",
        "lessons": [
            {
                "id": 1, "title": "Variables are just labeled boxes, bestie",
                "explanation": (
                    "Think of a variable as a labeled box.\n"
                    "`lowkey x = 42` → you just labeled a box 'x' and put 42 in it.\n"
                    "You can change what's inside anytime.\n"
                    "Strings go in quotes. Numbers don't. That's literally it."
                ),
                "example": '''lowkey age = 17
bestie name = "Zoomer"
lowkey gpa = 3.8

slay("Name:", name)
slay("Age:", age)
slay("GPA:", gpa)

# Change it
age = 18
slay("Happy birthday! Now:", age)''',
                "task": 'Create variables for your name, age, and favorite app. Print them.',
                "check": lambda code: "lowkey" in code.lower() or "bestie" in code.lower() or "let" in code.lower(),
                "hints": ['lowkey fav_app = "TikTok"'],
            },
            {
                "id": 2, "title": "If/else but make it sussy",
                "explanation": (
                    "`sus` = if (is this thing true? kinda sus if not)\n"
                    "`plot_twist` = else (oh wait, different outcome)\n"
                    "Comparisons: == (equal), != (not equal), > < >= <=\n"
                    "The code in { } only runs if the condition is true."
                ),
                "example": '''lowkey followers = 10000
lowkey verified = bet

sus followers > 1000000 {
    slay("You're famous famous ong")
} plot_twist {
    sus followers > 10000 {
        slay("Micro influencer vibes")
    } plot_twist {
        slay("Keep grinding bestie")
    }
}

sus verified == bet {
    slay("Blue check secured")
}''',
                "task": "Create a vibe check: if mood > 7 print 'slaying', else print 'not it'.",
                "check": lambda code: "sus" in code.lower() or "if" in code.lower(),
                "hints": ["sus mood > 7 { slay(...) } plot_twist { slay(...) }"],
            },
            {
                "id": 3, "title": "Loops — the infinite scroll of code",
                "explanation": (
                    "`grind` = for loop (you're grinding through a list)\n"
                    "`binge` = while loop (keep going until you stop)\n"
                    "Think of scrolling TikTok — that's a while loop.\n"
                    "Watching a playlist — that's a for loop."
                ),
                "example": '''# For loop — grinding through a playlist
lowkey playlist = ["Doja Cat", "Tyler", "SZA", "Kendrick", "Olivia"]
slay("Now playing:")
grind song w playlist {
    slay("  >>", song)
}

# While loop — scrolling until bored
lowkey energy = 100
slay("")
slay("Scrolling TikTok...")
binge energy > 20 {
    energy = energy - 15
    slay("  Energy:", energy, "%")
}
slay("Phone died. Touch grass time.")''',
                "task": "Create a countdown from 10 to 1, then print 'LAUNCHED!'",
                "check": lambda code: "10" in code and ("grind" in code.lower() or "for" in code.lower() or "binge" in code.lower() or "while" in code.lower()),
                "hints": ["Use a while loop: binge count > 0 { ... count = count - 1 }"],
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════
    # 🦆🎓 SILVERDUCK ACADEMY — РУССКО-АМЕРИКАНСКАЯ ШКОЛА (RP MODE)
    # Story-driven course. You are Mr. SilverDuck, a new student.
    # Co-taught by Марья Ивановна (RU rigor) + Mr. Quackington (US chill).
    # ══════════════════════════════════════════════════════════════════
    "silverduck_academy": {
        "id": "silverduck_academy",
        "title": "🦆🎓 SilverDuck Academy — Russian-American Cyber School",
        "title_en": "Story-driven RP. Co-taught by Марья Ивановна + Mr. Quackington.",
        "icon": "🦆🎓",
        "description": "RP-курс: ты — Mr. SilverDuck, новый студент в гибридной академии. ФГОС-строгость + Silicon Valley-вайб. КВАК!",
        "teacher": "ru",  # Lead teacher
        "rp_mode": True,
        "lessons": [
            {
                "id": 1,
                "title": "🎬 Scene 1: First Day at the Academy",
                "explanation": (
                    "📖 STORY:\n"
                    "Ты переехал из обычной школы в SilverDuck Academy.\n"
                    "В классе — флаги РФ и США. На доске: 'КРЯЯЯ + LET'S GO'.\n\n"
                    "👩‍🏫 Марья Ивановна: «Так, Mr. SilverDuck, открывайте тетради. Сегодня — Hello World.»\n"
                    "🧑‍💻 Mr. Quackington: «Yo, dude! Welcome! Let's write your first program.»\n\n"
                    "🎯 ЗАДАЧА: Поприветствовать оба учителя на их языках в одной программе.\n"
                    "Используй: пусть/let, кряк/print, и оба языка одновременно."
                ),
                "example": '''# 🎬 Mr. SilverDuck enters the classroom
пусть имя_студента = "Mr. SilverDuck"
let badge_number = 0042

# Greet Russian teacher
кряк("Здравствуйте, Марья Ивановна!")
кряк("Меня зовут", имя_студента)

# Greet American teacher
print("Hi Mr. Quackington! Badge #", badge_number)
print("Ready to code!")

# Bilingual roll call
кряк("🦆 КРЯЯЯ! Bilingual duck reporting for duty!")''',
                "task": "Напиши свою версию: представься обоим учителям. Имя должно быть твоим (или 'Mr. SilverDuck'). Минимум 4 строки кряк/print.",
                "check": lambda code: ("кряк" in code or "print" in code) and ("пусть" in code or "let" in code) and ("Mr." in code or "Mr " in code or "Марь" in code or "Quack" in code),
                "hints": [
                    "Объяви переменную имя через пусть или let",
                    "Используй кряк() для русского приветствия",
                    "Используй print() для английского приветствия",
                    'Например: пусть имя = "Mr. SilverDuck"  ;  кряк("Привет!")  ;  print("Hi!")',
                ],
                "rp_scene": "Classroom 101. Window open. Russian winter outside, California sun on the screen.",
            },
            {
                "id": 2,
                "title": "🎬 Scene 2: The Pop Quiz — Бинарный Шок",
                "explanation": (
                    "📖 STORY:\n"
                    "Третий день. Марья Ивановна резко: «Контрольная! Перевести 25 в двоичную!»\n"
                    "Mr. Quackington (шёпотом): «Don't panic. Just keep dividing by 2.»\n\n"
                    "👩‍🏫 Марья Ивановна: «На ОГЭ это задание №1. Каждый русский школьник должен уметь!»\n"
                    "🧑‍💻 Mr. Quackington: «In AP CSP we call this 'Big Idea 2: Data'. Same thing, different label.»\n\n"
                    "🎯 ЗАДАЧА: Перевести число в двоичную систему через цикл с остатками.\n"
                    "Это твой первый алгоритм. Без него — двойка от Марьи Ивановны."
                ),
                "example": '''# 🎬 Pop quiz — convert decimal to binary
# Алгоритм: делим на 2, собираем остатки

функция в_двоичную(число) {
    пусть результат = ""
    пусть н = число
    пока н > 0 {
        пусть остаток = н % 2
        результат = текст(остаток) + результат
        н = целое(н / 2)
    }
    если результат == "" {
        вернуть "0"
    }
    вернуть результат
}

# Test it
для проверка в [0, 1, 5, 25, 100, 255] {
    кряк(проверка, "→", в_двоичную(проверка))
}

print("✅ Mr. SilverDuck passed the quiz!")''',
                "task": "Напиши функцию which_grade(score) — возвращает 5/4/3/2 по русской системе ИЛИ A/B/C/F по американской. Реши САМ. Вызови с score=87.",
                "check": lambda code: ("функция" in code or "fn " in code or "rizz " in code) and ("вернуть" in code or "return" in code or "yeet" in code) and ("87" in code),
                "hints": [
                    "Функция начинается с 'функция имя(параметр) {' или 'fn name(param) {'",
                    "Условия: если score >= 90 → 'A' или 5",
                    "В конце вернуть/return результат",
                    "Вызови: пусть оценка = which_grade(87)  ;  кряк(оценка)",
                ],
                "rp_scene": "Pop quiz tension. Pencils scratching. Mr. Quackington gives discreet thumbs up.",
            },
            {
                "id": 3,
                "title": "🎬 Scene 3: The Hackathon — Build Something",
                "explanation": (
                    "📖 STORY:\n"
                    "Пятница. Mr. Quackington: «Time for the weekly hackathon, ducks!»\n"
                    "Марья Ивановна (с одобрением): «Это похоже на наши проекты на Олимпиаде. Творите!»\n\n"
                    "🧑‍💻 Mr. Quackington: «Build a tip calculator. Real world stuff.»\n"
                    "👩‍🏫 Марья Ивановна: «Прибавь обработку ошибок! В реальной жизни вводят и отрицательные числа.»\n\n"
                    "🎯 ЗАДАЧА: Калькулятор с тремя функциями: подсчёт, валидация, вывод.\n"
                    "ДЕКОМПОЗИЦИЯ — это академический скилл №1."
                ),
                "example": '''# 🎬 Hackathon project — Restaurant tip calculator
# Three functions = three abstraction layers

fn validate(amount, tip_percent) {
    if amount < 0 {
        return "ERROR: Negative bill"
    }
    if tip_percent < 0 {
        return "ERROR: Negative tip"
    }
    if tip_percent > 100 {
        return "WARN: That's a generous tip!"
    }
    return "OK"
}

fn calculate_tip(amount, tip_percent) {
    return amount * tip_percent / 100
}

fn print_receipt(name, amount, tip_percent) {
    let status = validate(amount, tip_percent)
    print("=== Receipt for", name, "===")
    print("Validation:", status)
    if status != "OK" and status != "WARN: That's a generous tip!" {
        return
    }
    let tip = calculate_tip(amount, tip_percent)
    let total = amount + tip
    print("Bill:    $", amount)
    print("Tip", tip_percent, "%: $", tip)
    print("TOTAL:   $", total)
    print("")
}

print_receipt("Mr. SilverDuck", 50, 18)
print_receipt("Марья Ивановна", 100, 15)
print_receipt("Test - negative", -10, 20)''',
                "task": "Сделай свой калькулятор: посчитай скидку. Функция discount(price, percent). Вызови с (1000, 25). Должно быть 750.",
                "check": lambda code: ("fn " in code or "функция" in code or "rizz" in code) and ("1000" in code or "100" in code) and ("25" in code) and ("*" in code or "умнож" in code.lower()),
                "hints": [
                    "Цена * (1 - процент/100) = цена со скидкой",
                    "1000 * (1 - 25/100) = 1000 * 0.75 = 750",
                    "Или: 1000 - 1000 * 25/100 = 750",
                    "fn discount(price, percent) { return price - price * percent / 100 }",
                ],
                "rp_scene": "Lab full of typing. Mr. Quackington hands out energy drinks. Марья Ивановна reviews code on whiteboard.",
            },
            {
                "id": 4,
                "title": "🎬 Scene 4: Lists & The 2D Grid Boss",
                "explanation": (
                    "📖 STORY:\n"
                    "Финальный экзамен 1-го семестра. Двухчасовой марафон.\n"
                    "Тема: списки и 2D массивы.\n\n"
                    "👩‍🏫 Марья Ивановна: «Это задание ЕГЭ номер 17. Без этого — на ВУЗ не пройдёшь.»\n"
                    "🧑‍💻 Mr. Quackington: «AP CSA Free Response Question #4 always has a 2D array.»\n\n"
                    "🎯 ЗАДАЧА: Создать игровое поле, найти все 'мины', вывести safe-карту.\n"
                    "Это микро-Minesweeper. Этот алгоритм используется в реальных играх."
                ),
                "example": '''# 🎬 Final boss — 2D grid analysis
# 0 = empty, 1 = mine

let board = [
    [0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0],
    [1, 0, 0, 0, 0],
    [0, 0, 1, 0, 1],
    [0, 0, 0, 0, 0]
]

# Count mines
let mine_count = 0
for row in board {
    for square in row {
        if square == 1 {
            mine_count = mine_count + 1
        }
    }
}
print("Total mines:", mine_count)

# Build safe map (count adjacent mines)
fn count_adjacent(b, r, c) {
    let count = 0
    let rows = len(b)
    let cols = len(b[0])
    for dr in [-1, 0, 1] {
        for dc in [-1, 0, 1] {
            if dr != 0 or dc != 0 {
                let nr = r + dr
                let nc = c + dc
                if nr >= 0 and nr < rows {
                    if nc >= 0 and nc < cols {
                        if b[nr][nc] == 1 {
                            count = count + 1
                        }
                    }
                }
            }
        }
    }
    return count
}

print("")
print("Safe map (numbers = adjacent mines):")
for r in range(5) {
    let row_str = ""
    for c in range(5) {
        if board[r][c] == 1 {
            row_str = row_str + "💣 "
        } else {
            row_str = row_str + str(count_adjacent(board, r, c)) + "  "
        }
    }
    print(row_str)
}

print("")
print("🦆 Mr. SilverDuck cleared the final boss! КРЯЯЯ + LET'S GO!")''',
                "task": "Создай матрицу 3x3 с числами 1-9. Найди сумму ВСЕХ элементов. Должно получиться 45.",
                "check": lambda code: "[[" in code and ("for" in code or "для" in code or "grind" in code) and ("сумм" in code.lower() or "sum" in code.lower() or "total" in code.lower() or "+" in code),
                "expected_contains": "45",
                "hints": [
                    "[[1,2,3],[4,5,6],[7,8,9]]",
                    "Двойной цикл: внешний по строкам, внутренний по элементам",
                    "Объяви total = 0, потом total = total + element",
                    "1+2+3+4+5+6+7+8+9 = 45",
                ],
                "rp_scene": "Final exam silence. Marya Ivanovna and Quackington watching from back of room.",
            },
            {
                "id": 5,
                "title": "🎬 Scene 5: GRADUATION — Build Your Own Tool",
                "explanation": (
                    "📖 STORY:\n"
                    "Выпускной. Ты получил диплом SilverDuck Academy.\n"
                    "Mr. Quackington вручает 🎓 + GitHub-стикер.\n"
                    "Марья Ивановна — рукопожатие + 'Молодец, теперь — в МГУ!'\n\n"
                    "Тебе вручают финальный проект: построить ИНСТРУМЕНТ.\n"
                    "Что-то полезное. Real-world. Multi-function. С документацией.\n\n"
                    "👩‍🏫: «Покажи систему, не просто скрипт.»\n"
                    "🧑‍💻: «Make it modular. Make it ship.»\n\n"
                    "🎯 ЗАДАЧА: Студенческая система оценок. Минимум 3 функции, минимум 1 список, минимум 1 цикл.\n"
                    "Это твой капстоун. Это про-уровень."
                ),
                "example": '''# 🎓 GRADUATION PROJECT — Student Grade System
# Multi-function, real-world, modular code

# Database — list of students
let students = [
    ["Mr. SilverDuck", [85, 92, 78, 95, 88]],
    ["Марья Петровна Jr", [98, 99, 95, 97, 100]],
    ["Quackerjack", [72, 68, 75, 80, 70]],
    ["Cyber Duckling", [88, 90, 85, 92, 89]]
]

fn average(scores) {
    let total = 0
    for s in scores {
        total = total + s
    }
    return total / len(scores)
}

fn letter_grade(avg) {
    if avg >= 90 { return "A" }
    if avg >= 80 { return "B" }
    if avg >= 70 { return "C" }
    if avg >= 60 { return "D" }
    return "F"
}

fn russian_grade(avg) {
    if avg >= 85 { return 5 }
    if avg >= 70 { return 4 }
    if avg >= 50 { return 3 }
    return 2
}

fn print_report(student) {
    let name = student[0]
    let scores = student[1]
    let avg = average(scores)
    let us_grade = letter_grade(avg)
    let ru_grade = russian_grade(avg)
    print("─────────────────────────")
    print("👤 Student:", name)
    print("📝 Scores:", scores)
    print("📊 Average:", avg)
    print("🇺🇸 US grade:", us_grade)
    print("🇷🇺 RU grade:", ru_grade)
}

# Main
print("🎓 SILVERDUCK ACADEMY — END OF SEMESTER REPORT")
print("=============================================")
for student in students {
    print_report(student)
}
print("─────────────────────────")
print("🦆 КРЯЯЯ! GRADUATION CEREMONY COMPLETE!")
print("Mr. SilverDuck → certified Russian-American duck dev 🇷🇺🇺🇸")''',
                "task": "Сделай свой инструмент: словарь товаров (минимум 3 товара) + функция расчёта общей стоимости. Минимум 2 функции, 1 список или словарь.",
                "check": lambda code: ("fn " in code or "функция" in code or "rizz" in code) and ("[" in code or "{" in code) and (code.count("fn ") + code.count("функция") + code.count("rizz ") >= 2),
                "hints": [
                    "Список товаров: [['яблоко', 50], ['хлеб', 30], ['молоко', 80]]",
                    "Функция total(items) — сумма второго элемента каждого",
                    "Функция print_cart(items) — красивый вывод",
                    "Главное: 2+ функции, 1+ структура данных",
                ],
                "rp_scene": "Graduation hall. Both teachers in formal attire. Diploma in hand. Future awaits.",
                "graduation": True,
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════
    # 🌍 POLYGLOT — Pascal, Rust, Python, C, Java, Go, JS, etc.
    # Quack учит обычные языки через сравнение
    # ══════════════════════════════════════════════════════════════════
    "polyglot": {
        "id": "polyglot",
        "title": "🌍 Polyglot — Learn ALL Languages via Quack",
        "title_en": "Pascal/C/Rust/Python/Go/Java/JS — see how they all map to Quack",
        "icon": "🌍",
        "description": "Кряк знает ВСЕ языки. Pascal (история), C (предки), Rust (безопасность), Python (вайб), Go (простота). КРЯЯЯ!",
        "teacher": "en",
        "lessons": [
            {
                "id": 1,
                "title": "Hello World — Same idea, 7 dialects",
                "explanation": (
                    "Hello World — это первая программа в любом языке.\n"
                    "Каждый язык говорит её по-своему. Но идея ОДНА.\n\n"
                    "🟦 PASCAL  (Wirth, 1970): обучающий язык, ОЧЕНЬ многословный\n"
                    "🟫 C       (Ritchie, 1972): системный, скобки {}, ; в конце\n"
                    "🟨 PYTHON  (1991): чистый, индентация = блоки\n"
                    "⬛ JAVA    (1995): корпоративный, всё в классах\n"
                    "🟧 RUST    (2010): безопасный системный, fn + ! макросы\n"
                    "🟦 GO      (2009): простой, package main\n"
                    "🟪 JS      (1995): везде в браузерах, console.log\n"
                    "🦆 QUACK   (2026): all of the above + русский 😎"
                ),
                "example": '''# 🌍 Hello World на 7 языках — все говорят про утку

# 1. PASCAL — старая школа
# program HelloWorld;
# begin
#     writeln('Hello, World!');
# end.

# 2. C — bare metal
# #include <stdio.h>
# int main() {
#     printf("Hello, World!\\n");
#     return 0;
# }

# 3. PYTHON — clean
# print("Hello, World!")

# 4. JAVA — enterprise overhead
# public class Hello {
#     public static void main(String[] args) {
#         System.out.println("Hello, World!");
#     }
# }

# 5. RUST — safe + fast
# fn main() {
#     println!("Hello, World!");
# }

# 6. GO — minimal
# package main
# import "fmt"
# func main() { fmt.Println("Hello, World!") }

# 7. JS — web
# console.log("Hello, World!");

# === QUACK — speaks them all ===
print("Hello, World!")
кряк("Привіт, Світ!")
drukuj("Witaj, Świecie!")
slay("Hello bestie no cap")''',
                "task": "Напиши Hello World в Quack минимум 3 разными словами (print/кряк/drukuj/tlač/друкуй/slay).",
                "check": lambda code: sum(1 for w in ["print", "кряк", "drukuj", "tlač", "друкуй", "slay", "кря"] if w in code.lower()) >= 3,
                "hints": ["print('Hello')", "кряк('Привет')", "drukuj('Cześć')", "Минимум 3 разных слова"],
                "lang_chart": "PAS=writeln C=printf PY=print JAVA=System.out.println RS=println! GO=fmt.Println JS=console.log Q=кряк/print",
            },
            {
                "id": 2,
                "title": "Variables — Type Systems Across Languages",
                "explanation": (
                    "Каждый язык по-разному относится к типам:\n\n"
                    "STATIC TYPED (тип объявляется явно):\n"
                    "  PASCAL: var x: integer;\n"
                    "  C:      int x = 10;\n"
                    "  RUST:   let x: i32 = 10;\n"
                    "  GO:     var x int = 10\n"
                    "  JAVA:   int x = 10;\n\n"
                    "DYNAMIC TYPED (тип угадывается):\n"
                    "  PYTHON: x = 10\n"
                    "  JS:     let x = 10;\n"
                    "  QUACK:  пусть x = 10  (или let x = 10)\n\n"
                    "Quack — динамически типизирован. Like Python. Like the future."
                ),
                "example": '''# 🌍 Variables — type systems compared

# PASCAL (1970): everything must be declared
# var
#     age: integer;
#     name: string;
#     pi: real;
# begin
#     age := 25;
#     name := 'Mr. SilverDuck';
#     pi := 3.14;
# end.

# C (1972): manual memory + types
# int age = 25;
# char* name = "Mr. SilverDuck";
# double pi = 3.14;

# RUST (2010): types inferred but checked
# let age: i32 = 25;
# let name: &str = "Mr. SilverDuck";
# let pi: f64 = 3.14;
# // Immutable by default! `let mut x` for mutable

# PYTHON (1991): no types, runtime guess
# age = 25
# name = "Mr. SilverDuck"
# pi = 3.14

# === QUACK — Python-style + Russian ===
пусть age = 25
let name = "Mr. SilverDuck"
let pi = 3.14
let lang_count = 9   # Quack speaks 9 languages

print("age:", age, type(age))
print("name:", name, type(name))
print("pi:", pi, type(pi))
print("languages:", lang_count)

# Mutability — Quack vars ARE mutable
age = 26
print("After birthday:", age)''',
                "task": "Объяви 4 переменные разных типов: число, строка, дробь, список. Выведи каждую с её типом.",
                "check": lambda code: code.count("let ") + code.count("пусть") >= 4 and ("type" in code or "тип" in code) and ("[" in code or "list" in code.lower()),
                "hints": [
                    "пусть число = 42",
                    'let строка = "hello"',
                    "пусть дробь = 3.14",
                    "let список = [1, 2, 3]",
                    "print(type(число))",
                ],
            },
            {
                "id": 3,
                "title": "Functions — Syntax Across Worlds",
                "explanation": (
                    "Функция — кирпичик всех языков. Но синтаксис разный.\n\n"
                    "PASCAL:    function add(a, b: integer): integer; begin add := a+b; end;\n"
                    "C:         int add(int a, int b) { return a + b; }\n"
                    "JAVA:      public static int add(int a, int b) { return a + b; }\n"
                    "RUST:      fn add(a: i32, b: i32) -> i32 { a + b }\n"
                    "GO:        func add(a, b int) int { return a + b }\n"
                    "PYTHON:    def add(a, b): return a + b\n"
                    "JS:        const add = (a, b) => a + b;\n"
                    "QUACK:     fn add(a, b) { return a + b }\n"
                    "QUACK RU:  функция сложить(а, б) { вернуть а + б }\n\n"
                    "Видишь — везде одна идея: имя, аргументы, тело, результат."
                ),
                "example": '''# 🌍 Same function in many languages

# PASCAL:
# function factorial(n: integer): integer;
# begin
#     if n <= 1 then factorial := 1
#     else factorial := n * factorial(n - 1);
# end;

# C:
# int factorial(int n) {
#     if (n <= 1) return 1;
#     return n * factorial(n - 1);
# }

# RUST:
# fn factorial(n: u64) -> u64 {
#     if n <= 1 { 1 } else { n * factorial(n - 1) }
# }

# PYTHON:
# def factorial(n):
#     return 1 if n <= 1 else n * factorial(n - 1)

# === QUACK — bilingual factorial ===
fn factorial(n) {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}

функция факториал(н) {
    если н <= 1 {
        вернуть 1
    }
    вернуть н * факториал(н - 1)
}

for i in range(7) {
    print("factorial(", i, ") =", factorial(i))
    кряк("факториал(", i, ") =", факториал(i))
}''',
                "task": "Напиши функцию max3(a, b, c) — возвращает максимум из трёх. Вызови с (5, 9, 3). Ожидается 9.",
                "check": lambda code: ("fn " in code or "функция" in code or "rizz" in code) and ("max3" in code or "макс3" in code or "макс_из_трёх" in code or "maximum" in code.lower()) and "9" in code and ("if" in code or "если" in code or "max" in code.lower() or "макс" in code.lower()),
                "hints": [
                    "fn max3(a, b, c) { ... }",
                    "Используй вложенные if или встроенный max",
                    "if a >= b and a >= c { return a }",
                    "Или: return max(a, max(b, c))",
                ],
            },
            {
                "id": 4,
                "title": "Loops — For/While in 7 Languages",
                "explanation": (
                    "Циклы — везде. Но синтаксис разный:\n\n"
                    "FOR loop:\n"
                    "  PASCAL:  for i := 1 to 10 do begin ... end;\n"
                    "  C:       for (int i = 0; i < 10; i++) { ... }\n"
                    "  JAVA:    for (int i = 0; i < 10; i++) { ... }\n"
                    "  RUST:    for i in 0..10 { ... }\n"
                    "  GO:      for i := 0; i < 10; i++ { ... }\n"
                    "  PYTHON:  for i in range(10): ...\n"
                    "  JS:      for (let i = 0; i < 10; i++) { ... }\n"
                    "  QUACK:   для и в диапазон(10) { ... }\n\n"
                    "WHILE loop — идентично везде: while/пока/dopóki + condition + body."
                ),
                "example": '''# 🌍 Loops — same idea, different syntax

# FizzBuzz — classic interview question, every language
# Print 1-15. If divisible by 3 → "Fizz", by 5 → "Buzz", by both → "FizzBuzz"

# C version:
# for (int i = 1; i <= 15; i++) {
#     if (i % 15 == 0) printf("FizzBuzz\\n");
#     else if (i % 3 == 0) printf("Fizz\\n");
#     else if (i % 5 == 0) printf("Buzz\\n");
#     else printf("%d\\n", i);
# }

# Python version:
# for i in range(1, 16):
#     if i % 15 == 0: print("FizzBuzz")
#     elif i % 3 == 0: print("Fizz")
#     elif i % 5 == 0: print("Buzz")
#     else: print(i)

# === QUACK — both Russian and English work ===
print("=== FizzBuzz (English style) ===")
for i in range(1, 16) {
    if i % 15 == 0 {
        print("FizzBuzz")
    } else {
        if i % 3 == 0 {
            print("Fizz")
        } else {
            if i % 5 == 0 {
                print("Buzz")
            } else {
                print(i)
            }
        }
    }
}

print("")
print("=== ФизБуз (русский стиль) ===")
для и в диапазон(1, 16) {
    если и % 15 == 0 {
        кряк("ФизБуз")
    } иначе {
        если и % 3 == 0 {
            кряк("Физ")
        } иначе {
            если и % 5 == 0 {
                кряк("Буз")
            } иначе {
                кряк(и)
            }
        }
    }
}''',
                "task": "Напиши цикл который выведет квадраты чисел от 1 до 5. Должно быть: 1, 4, 9, 16, 25.",
                "check": lambda code: ("for" in code.lower() or "для" in code or "grind" in code) and ("range" in code or "диапазон" in code) and ("*" in code or "²" in code or "pow" in code or "квадр" in code.lower() or "степень" in code),
                "expected_contains": "25",
                "hints": [
                    "для и в диапазон(1, 6) { кряк(и * и) }",
                    "for i in range(1, 6) { print(i * i) }",
                    "Не забудь 6 (не 5) — диапазон не включает конец",
                ],
            },
            {
                "id": 5,
                "title": "Memory & Safety — From C to Rust to Quack",
                "explanation": (
                    "🟫 C (1972): TY УПРАВЛЯЕШЬ памятью. malloc/free. Утечки = твоя боль.\n"
                    "  int* p = malloc(sizeof(int) * 100);\n"
                    "  // забыл free(p) → memory leak\n"
                    "  // обратился p[1000] → SEGFAULT\n\n"
                    "🟦 PASCAL (1970): new/dispose. Тоже manual, но проще.\n\n"
                    "☕ JAVA (1995): GARBAGE COLLECTOR. Память автоматическая. Но тормозит.\n\n"
                    "🟧 RUST (2010): OWNERSHIP. Compiler ловит ошибки ДО запуска.\n"
                    "  let v = vec![1,2,3];  // owns memory\n"
                    "  let v2 = v;            // moved, v invalid now!\n"
                    "  // Это РЕВОЛЮЦИЯ. Безопасность БЕЗ GC.\n\n"
                    "🦆 QUACK: высокоуровневый. Память — забота VM. Как Python.\n"
                    "  Но GPU — через unigpu_ffi.dll (Rust под капотом!).\n\n"
                    "Эволюция: manual → GC → ownership → managed-with-GPU-escape."
                ),
                "example": '''# 🌍 Memory journey through history

# C (1972): manual memory
# int *arr = malloc(100 * sizeof(int));
# for (int i = 0; i < 100; i++) arr[i] = i * i;
# free(arr);  // если забыл — leak forever

# RUST (2010): ownership rules
# let arr: Vec<i32> = (0..100).map(|i| i*i).collect();
# // Компилятор гарантирует: arr будет освобождён ПРАВИЛЬНО
# // Двойной free? Невозможно. Use after free? Невозможно.

# PYTHON: garbage collected
# arr = [i*i for i in range(100)]
# # GC сам разрулит

# === QUACK — managed memory + GPU escape hatch ===
let arr = []
for i in range(100) {
    arr = append(arr, i * i)
}
print("Created", len(arr), "squares")
print("Sum:", sum(arr))

# GPU memory — Rust under the hood (unigpu_ffi.dll)
# гпу.выдели(размер) → allocates VRAM via Rust DLL
# гпу.освободи(буфер) → frees safely

# When you write Quack, Rust handles GPU.
# When you write Rust, the compiler handles safety.
# When you write C, you handle EVERYTHING. (and bugs.)
# КРЯЯЯ! Эволюция!

print("")
print("Memory model evolution:")
let history = [
    ["1970 Pascal", "manual: new/dispose"],
    ["1972 C", "manual: malloc/free"],
    ["1995 Java", "garbage collected"],
    ["2010 Rust", "ownership (revolution!)"],
    ["2026 Quack", "managed + GPU via Rust"]
]
for entry in history {
    print(" ", entry[0], "→", entry[1])
}''',
                "task": "Создай список из 10 чисел, удвой каждое, выведи сумму удвоенных.",
                "check": lambda code: ("[" in code or "append" in code) and ("for" in code or "для" in code or "grind" in code) and ("*" in code or "+" in code) and ("sum" in code.lower() or "сумм" in code.lower() or "+" in code),
                "expected_contains": "90",  # 1+2+...+9 = 45, doubled = 90
                "hints": [
                    "let nums = [1,2,3,4,5,6,7,8,9]",
                    "Для каждого: новый = старый * 2",
                    "1+2+3+4+5+6+7+8+9 = 45, удвоенные = 90",
                ],
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════
    # 🧠 LEGENDARY CS — MIT/Harvard/Stanford classics + AI-Era 2026
    # SICP, CS50, CS106, prompt engineering, AI pair programming
    # ══════════════════════════════════════════════════════════════════
    "legendary_cs": {
        "id": "legendary_cs",
        "title": "🧠 Legendary CS — MIT/Harvard/Stanford + AI-Era 2026",
        "title_en": "Classic CS wisdom + cyberpunk AI patterns",
        "icon": "🧠",
        "description": "SICP higher-order, CS50 thinking, CS106 recursion + 2026 prompt eng + when NOT to use AI. КРЯКНУТЬ КИБЕР-АКАДЕМИЮ!",
        "teacher": "en",
        "lessons": [
            {
                "id": 1,
                "title": "🎓 SICP: Higher-Order Functions",
                "explanation": (
                    "MIT 6.001 / SICP — 'Structure and Interpretation of Computer Programs'.\n"
                    "Главная идея: ФУНКЦИИ — это ДАННЫЕ.\n\n"
                    "Функция может:\n"
                    "  - Принимать другие функции как аргументы\n"
                    "  - Возвращать функции\n"
                    "  - Сохраняться в переменных\n\n"
                    "Это меняет как ты думаешь о коде. Вместо 'делай X' пишешь 'опиши КАК делать X'.\n"
                    "В Lisp/Scheme это ядро. В Python lambda. В Rust closures. В Quack — fn в значении."
                ),
                "example": '''# 🎓 SICP-style higher-order functions

fn apply_twice(action, x) {
    return action(action(x))
}

fn double(x) {
    return x * 2
}

fn add_ten(x) {
    return x + 10
}

print("apply_twice(double, 5) =", apply_twice(double, 5))      # 20
print("apply_twice(add_ten, 5) =", apply_twice(add_ten, 5))    # 25

# Map/Filter/Reduce — functional pillars
let nums = [1, 2, 3, 4, 5]
print("Original:", nums)

# Map — apply func to each (works with both arg orders)
let doubled = map(double, nums)
print("Doubled:", doubled)

# Filter — keep elements matching condition
fn is_even(x) {
    return x % 2 == 0
}
let evens = filter(is_even, nums)
print("Evens:", evens)

# Reduce — collapse list to single value
fn add(a, b) {
    return a + b
}
let total = reduce(add, nums)
print("Sum via reduce:", total)

print("🦆 SICP wisdom: code is data, functions are values.")''',
                "task": "Напиши функцию triple_apply(f, x) — применяет f трижды. f(f(f(x))). Используй с double и x=2. Должно быть 16.",
                "check": lambda code: ("fn " in code or "функция" in code) and ("triple" in code.lower() or "тройн" in code.lower() or "thrice" in code.lower()) and "16" in code,
                "hints": [
                    "fn triple_apply(f, x) { return f(f(f(x))) }",
                    "double(2) = 4, double(4) = 8, double(8) = 16",
                    "Просто три вложенных вызова f",
                ],
                "course_ref": "MIT 6.001 SICP, Chapter 1.3",
            },
            {
                "id": 2,
                "title": "🎓 CS50: Computational Thinking — Decomposition",
                "explanation": (
                    "Harvard CS50 (David Malan): 'How to think like a computer scientist'.\n\n"
                    "ДЕКОМПОЗИЦИЯ = разбить большую задачу на маленькие.\n"
                    "Это #1 навык программиста.\n\n"
                    "Пример: 'Найти всех студентов с баллом > 80 и отсортировать по имени'\n"
                    "  → 1. Прочитать студентов\n"
                    "  → 2. Отфильтровать (балл > 80)\n"
                    "  → 3. Отсортировать по имени\n"
                    "  → 4. Вывести\n\n"
                    "4 маленьких функции = 1 большая возможность."
                ),
                "example": '''# 🎓 CS50-style decomposition

let students = [
    ["Alice", 92],
    ["Bob", 75],
    ["Charlie", 88],
    ["Diana", 95],
    ["Eve", 70],
    ["Frank", 82]
]

# Step 1: Filter by score
fn filter_by_score(students, min_score) {
    let result = []
    for s in students {
        if s[1] >= min_score {
            result = append(result, s)
        }
    }
    return result
}

# Step 2: Get just names
fn extract_names(students) {
    let names = []
    for s in students {
        names = append(names, s[0])
    }
    return names
}

# Step 3: Print pretty
fn print_list(title, items) {
    print("=== " + title + " ===")
    for i in range(len(items)) {
        print(" ", i + 1, ".", items[i])
    }
}

# Compose them
let high_scorers = filter_by_score(students, 80)
let pupils = extract_names(high_scorers)
let ranked = sorted(pupils)

print_list("Honor Roll (sorted)", ranked)

print("")
print("🦆 CS50 wisdom: decompose ALL the things.")''',
                "task": "Декомпозируй: посчитай средний балл всех студентов. Минимум 2 функции (одна получает баллы, вторая считает среднее).",
                "check": lambda code: code.count("fn ") + code.count("функция") + code.count("rizz ") >= 2 and ("avg" in code.lower() or "среднее" in code.lower() or "average" in code.lower() or "/" in code),
                "hints": [
                    "fn extract_scores(students) — возвращает список баллов",
                    "fn average(scores) — возвращает сумма / длина",
                    "Потом: avg = average(extract_scores(students))",
                ],
                "course_ref": "Harvard CS50 — Week 0/1",
            },
            {
                "id": 3,
                "title": "🎓 CS106: Recursion Mastery",
                "explanation": (
                    "Stanford CS106B/X: ' рекурсия пока не задерёт'.\n\n"
                    "Рекурсия = функция вызывает саму себя.\n"
                    "Базовый случай ОБЯЗАТЕЛЕН — иначе ∞.\n\n"
                    "Паттерны рекурсии:\n"
                    "  1. ЛИНЕЙНАЯ:    f(n) → f(n-1)              (factorial)\n"
                    "  2. БИНАРНАЯ:    f(n) → f(n-1) + f(n-2)     (fibonacci)\n"
                    "  3. ДЕРЕВО:      f(node) → f(left), f(right) (tree traversal)\n"
                    "  4. ХВОСТОВАЯ:   аккумулятор как параметр    (efficient!)\n\n"
                    "Если можешь решить рекурсивно — ПОПРОБУЙ. Часто короче."
                ),
                "example": '''# 🎓 CS106-style recursion patterns

# Pattern 1: LINEAR recursion (count down)
fn count_down(n) {
    if n <= 0 {
        print("BLAST OFF! 🚀")
        return
    }
    print(n)
    count_down(n - 1)
}

print("=== Linear recursion ===")
count_down(5)

# Pattern 2: BINARY recursion (fibonacci)
fn fib(n) {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}

print("")
print("=== Binary recursion (fibonacci) ===")
for i in range(10) {
    print("fib(" + str(i) + ") =", fib(i))
}

# Pattern 3: TAIL recursion with accumulator (efficient)
fn fact_helper(n, acc) {
    if n <= 1 { return acc }
    return fact_helper(n - 1, n * acc)
}

fn factorial(n) {
    return fact_helper(n, 1)
}

print("")
print("=== Tail recursion (factorial) ===")
print("10! =", factorial(10))

# Pattern 4: Recursive list reversal
fn reverse_list(lst) {
    if len(lst) <= 1 { return lst }
    let rest = []
    for i in range(1, len(lst)) {
        rest = append(rest, lst[i])
    }
    let reversed_rest = reverse_list(rest)
    reversed_rest = append(reversed_rest, lst[0])
    return reversed_rest
}

print("")
print("=== Recursive reversal ===")
print(reverse_list([1, 2, 3, 4, 5]))

print("")
print("🦆 CS106 wisdom: trust the recursion fairy.")''',
                "task": "Рекурсивная функция sum_to_n(n) — сумма чисел от 1 до n. sum_to_n(10) = 55.",
                "check": lambda code: ("fn " in code or "функция" in code) and ("sum_to_n" in code or "сумма_до" in code or "sumto" in code) and "55" in code,
                "hints": [
                    "Базовый случай: if n <= 0 { return 0 }",
                    "Рекурсивный: return n + sum_to_n(n - 1)",
                    "1+2+3+...+10 = 55",
                ],
                "course_ref": "Stanford CS106B — Recursion chapter",
            },
            {
                "id": 4,
                "title": "🤖 AI-Era 2026: Prompt Engineering Mindset",
                "explanation": (
                    "Год 2026. ИИ пишет 30%+ кода. Но ТЫ — пилот, не пассажир.\n\n"
                    "PROMPT ENGINEERING ≠ написание промптов.\n"
                    "Это умение:\n"
                    "  1. ЯСНО формулировать задачу\n"
                    "  2. Давать контекст и примеры\n"
                    "  3. Декомпозировать на маленькие шаги\n"
                    "  4. Проверять результат\n"
                    "  5. Знать когда ИИ ВРЁТ (галлюцинирует)\n\n"
                    "Лучшие prompt'ы = лучшие технические задания.\n"
                    "Старые скиллы (понимать код, читать docs) — стали ЦЕННЕЕ, не менее."
                ),
                "example": '''# 🤖 AI-Era thinking — clear specs win

# BAD prompt: "make a sort"
# - Какой sort? Bubble? Quick?
# - Сортировать что? Числа? Строки?
# - Какой порядок? Возрастание? Убывание?
# - Side effect or pure function?

# GOOD prompt: clear, with examples
# "Write a function bubble_sort(nums) that:
#  - Takes a list of numbers
#  - Returns a NEW sorted list (ascending)
#  - Original list unchanged
#  - Example: bubble_sort([3,1,2]) → [1,2,3]"

# === Translate good spec → Quack code ===
fn bubble_sort(nums) {
    # Copy to avoid mutating original
    let arr = []
    for n in nums {
        arr = append(arr, n)
    }
    let n = len(arr)
    for i in range(n) {
        for j in range(n - i - 1) {
            if arr[j] > arr[j + 1] {
                let tmp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = tmp
            }
        }
    }
    return arr
}

# Test the spec was met
let original = [3, 1, 4, 1, 5, 9, 2, 6]
let sorted_copy = bubble_sort(original)
print("Original:", original)
print("Sorted:  ", sorted_copy)
print("Original unchanged:", original)  # spec compliance

# AI-Era principle: ALWAYS test what AI gives you
fn assert_eq(a, b, label) {
    if a == b {
        print("✅", label, "passed")
    } else {
        print("❌", label, "failed:", a, "vs", b)
    }
}

assert_eq(bubble_sort([]), [], "empty list")
assert_eq(bubble_sort([1]), [1], "single element")
assert_eq(bubble_sort([3, 1, 2]), [1, 2, 3], "basic sort")
assert_eq(bubble_sort([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5], "reverse sorted")

print("")
print("🦆 AI-Era wisdom: AI is a pair programmer, not an oracle.")''',
                "task": "Напиши функцию assert_eq(a, b, label) — печатает ✅ если равны, ❌ если нет. Использовать минимум 3 раза для тестов чего-нибудь.",
                "check": lambda code: ("fn " in code or "функция" in code) and ("assert" in code.lower() or "проверка" in code.lower() or "test" in code.lower()) and (code.count("✅") + code.count("OK") + code.count("PASS") >= 1) and (code.count("==") >= 2),
                "hints": [
                    "fn assert_eq(a, b, label) { if a == b { print('✅', label) } else { print('❌', label) } }",
                    "Используй для тестов: assert_eq(2+2, 4, 'addition')",
                    "Минимум 3 разных теста",
                ],
                "course_ref": "AI-Era 2026 — Cyberpunk pair programming",
            },
            {
                "id": 5,
                "title": "🤖 AI-Era 2026: When NOT to Use AI",
                "explanation": (
                    "ИИ — мощно. Но НЕ универсально.\n\n"
                    "❌ КОГДА AI ПЛОХ:\n"
                    "  - Очень специфичный домен (медицина, юриспруденция)\n"
                    "  - Безопасность-критичный код (auth, crypto)\n"
                    "  - Когда ты сам не понимаешь задачу\n"
                    "  - Свежие APIs (training data старее)\n"
                    "  - Когда нужна 100% точность вычислений\n\n"
                    "✅ КОГДА AI ОТЛИЧЕН:\n"
                    "  - Boilerplate код\n"
                    "  - Объяснение чужого кода\n"
                    "  - Brainstorming подходов\n"
                    "  - Перевод между языками (PY→RUST)\n"
                    "  - Тесты для готового кода\n\n"
                    "ПРАВИЛО SILVERDUCK: 'AI пишет, ТЫ ПОНИМАЕШЬ.'"
                ),
                "example": '''# 🤖 When AI helps vs when YOU must drive

# === AI-FRIENDLY: boilerplate, well-known patterns ===

# E.g., Greatest Common Divisor — Euclid's algorithm, classic
fn gcd(a, b) {
    while b != 0 {
        let temp = b
        b = a % b
        a = temp
    }
    return a
}

print("=== AI-friendly examples ===")
print("gcd(48, 18) =", gcd(48, 18))     # 6
print("gcd(100, 75) =", gcd(100, 75))   # 25

# === HUMAN-MUST-DRIVE: business logic ===
# Here AI doesn't know YOUR rules. YOU must specify.

# Example: SilverDuck Academy grading rules
# - 5 (RU) requires BOTH score >= 85 AND attendance >= 80
# - 4 (RU) requires score >= 70 AND attendance >= 70
# - Anything else: needs review

fn silverduck_grade(score, attendance) {
    if score >= 85 and attendance >= 80 {
        return "5 — Отлично, Mr. SilverDuck!"
    }
    if score >= 70 and attendance >= 70 {
        return "4 — Хорошо, but show up more."
    }
    if score < 50 {
        return "2 — See Марья Ивановна after class."
    }
    return "3 — Needs review by both teachers."
}

print("")
print("=== Human-driven business rules ===")
print(silverduck_grade(90, 85))   # "5"
print(silverduck_grade(75, 75))   # "4"
print(silverduck_grade(40, 90))   # "2"
print(silverduck_grade(70, 60))   # "3 review"

# === AI hallucination check ===
# AI sometimes invents APIs. ALWAYS verify.
# Quack has: range, len, append, sort, sum, max, min, ...
# Quack does NOT have: someAPI(), magicSolve()
# If you see those — AI hallucinated. Push back.

print("")
print("🦆 AI-Era wisdom: trust but VERIFY.")
print("    AI suggests. YOU decide. КРЯЯЯ!")''',
                "task": "Реализуй СВОЕ бизнес-правило: классификация температуры. < 0 → 'freezing', 0-20 → 'cold', 20-30 → 'warm', > 30 → 'hot'. Тестируй 4 значения.",
                "check": lambda code: ("fn " in code or "функция" in code) and ("if" in code or "если" in code) and ("freezing" in code.lower() or "холод" in code.lower() or "cold" in code.lower() or "hot" in code.lower() or "жарко" in code.lower()) and (code.count("if") + code.count("если") >= 2),
                "hints": [
                    "fn classify(temp) { if temp < 0 { return 'freezing' } ... }",
                    "Минимум 4 if для 4 категорий",
                    "Тестируй: print(classify(-10)), print(classify(15)), и т.д.",
                ],
                "course_ref": "AI-Era 2026 — Cyberpunk wisdom",
            },
        ],
    },

    # ══════════════════════════════════════════════════════════
    # CYBERDUCK PATRIOT — Defensive Cybersecurity for Patriots
    # "WE THE DUCKS" — Silicon Sovereignty & Honeypot Warfare
    # ══════════════════════════════════════════════════════════
    "cyberduck_patriot": {
        "id": "cyberduck_patriot",
        "title": "CyberDuck Patriot: Silicon Sovereignty",
        "title_en": "CyberDuck Patriot: Defensive Cybersecurity",
        "title_ru": "КиберУтка-Патриот: Кремниевый Суверенитет",
        "icon": "🦅🛡️",
        "description": (
            "SilverDuck protects the silicon. Not attack — DEFENSE. "
            "The duck watches, traps, and reports. "
            "Honeypots catch idiots. Hardware policy locks the gates. "
            "WE THE DUCKS defend freedom through code. КРЯЯЯ!"
        ),
        "teacher": "en",
        "lessons": [
            # ── Lesson 1: Situational Awareness ──
            {
                "id": 1,
                "title": "Situational Awareness — Know Your Iron",
                "explanation": """# LESSON 1: SITUATIONAL AWARENESS
## Знай Своё Железо — Know Your Iron

A patriot duck doesn't fight blind.
Before defending ANYTHING, you must KNOW what you have.

SilverDuck has a built-in `hardware` object — a direct line
to the CPU, GPU, RAM, and every process running on YOUR machine.

Key recon commands:
  hardware.status()     — full system snapshot (CPU, RAM, disk, policy)
  hardware.processes()  — top processes eating YOUR resources
  hardware.memory()     — RAM breakdown (total / used / free)

This is YOUR silicon. The duck has REALTIME priority.
Nobody moves without the duck knowing.

In cybersecurity, the first rule is:
  "You can't protect what you can't see."

The duck sees EVERYTHING. КРЯЯЯ!
""",
                "example": """# === CyberDuck Lesson 1: RECON ===
# Before defense — reconnaissance.
# The duck checks its own perimeter.

print("=== DUCK RECON PROTOCOL ===")
print("")

# Step 1: What hardware do we control?
let status = hardware.status()
print("System: " + str(status))

# Step 2: Who's eating our RAM?
let procs = hardware.processes(5)
print("")
print("Top 5 processes by memory:")
print(procs)

# Step 3: RAM check
let mem = hardware.memory()
print("")
print("RAM status:")
print(mem)

# Step 4: What's our current policy?
let policy = hardware.policy()
print("")
print("Current policy:")
print(policy)

print("")
print("Recon complete. The duck SEES ALL.")
print("Now we know what to defend. KRYAAA!")""",
                "task": "Напиши скрипт, который проверяет hardware.status() и hardware.memory(). Если RAM используется > 70%, выведи предупреждение 'HIGH MEMORY USAGE — ALERT!'. Иначе 'System nominal.'",
                "check": lambda code: ("hardware" in code) and ("status" in code or "memory" in code or "память" in code) and ("70" in code or "0.7" in code) and ("if" in code or "если" in code),
                "hints": [
                    "let mem = hardware.memory() — получи данные RAM",
                    "Проверь mem['used_percent'] или вычисли сам",
                    "if used > 70 { print('ALERT!') } else { print('nominal') }",
                ],
                "course_ref": "CyberDuck Patriot — Situational Awareness",
            },
            # ── Lesson 2: Honeypot Architecture ──
            {
                "id": 2,
                "title": "Honeypot Architecture — The Trap for Idiots",
                "explanation": """# LESSON 2: HONEYPOT ARCHITECTURE
## Ловушка Для Идиотов — The Trap

The most elegant defense isn't a wall — it's a TRAP.

A HONEYPOT looks like a vulnerability. Hackers see an open door.
They walk in. The door LOCKS behind them.
Every keystroke is logged. Every tool they use — recorded.
They think they're hacking YOU. You're studying THEM.

SilverDuck philosophy:
  "Don't fight the cockroach. Let it walk into the trap.
   Then study it. Then report it. Then flush."

How it works in code:
  1. Create something that LOOKS vulnerable
  2. Log EVERY access attempt
  3. If behavior is suspicious — flag, contain, report
  4. Never attack back — that's illegal. We DEFEND.

The duck doesn't need to be aggressive.
The duck is PATIENT. КРЯЯЯ!

Real-world analogy:
  A real-world honeypot might fake an open SSH port,
  a fake admin panel, or a decoy database.
  When someone connects — they're in OUR sandbox.
  All their tools, IPs, patterns — LOGGED.
""",
                "example": """# === CyberDuck Lesson 2: HONEYPOT ===
# Simulating a honeypot monitoring system.
# The trap watches. The trap logs. The trap reports.

# --- Simulated access log ---
let access_log = [
    "user:admin ip:192.168.1.1 action:login status:ok",
    "user:root ip:45.33.32.156 action:login status:fail",
    "user:root ip:45.33.32.156 action:login status:fail",
    "user:root ip:45.33.32.156 action:login status:fail",
    "user:admin ip:192.168.1.1 action:read status:ok",
    "user:test ip:185.220.101.1 action:login status:fail",
    "user:test ip:185.220.101.1 action:sudo status:fail",
]

# --- Honeypot Analysis ---
print("=== HONEYPOT LOG ANALYZER ===")
print("")

let alerts = []
let suspicious_ips = []

# Count failed logins per IP
let fail_counts = {}

fn analyze_log(entries) {
    for entry in entries {
        if contains(entry, "status:fail") {
            # Extract IP (simplified)
            let parts = split(entry, " ")
            for p in parts {
                if contains(p, "ip:") {
                    let ip = replace(p, "ip:", "")
                    if has_key(fail_counts, ip) {
                        fail_counts[ip] = fail_counts[ip] + 1
                    } else {
                        fail_counts[ip] = 1
                    }
                }
            }
        }
    }
}

analyze_log(access_log)

print("Failed login attempts per IP:")
print(fail_counts)
print("")

# Flag IPs with 3+ failures
for ip in fail_counts {
    if fail_counts[ip] >= 3 {
        print("ALERT: " + ip + " = " + str(fail_counts[ip]) + " failures — HONEYPOT TRIGGERED!")
        append(suspicious_ips, ip)
    }
}

if len(suspicious_ips) == 0 {
    print("No threats detected. Perimeter clear.")
} else {
    print("")
    print("Suspicious IPs trapped: " + str(len(suspicious_ips)))
    print("Logging to SilverDuck journal... KRYAAA!")
}""",
                "task": "Создай свой анализатор логов: список строк-событий, каждая содержит IP и action. Если один IP делает больше 2-х 'sudo' действий — это ALERT. Выведи список подозрительных IP.",
                "check": lambda code: ("for" in code or "для" in code) and ("if" in code or "если" in code) and ("sudo" in code or "alert" in code.lower() or "ALERT" in code) and ("2" in code or "3" in code),
                "hints": [
                    "Сделай словарь: ip -> count of sudo actions",
                    "for event in log { if 'sudo' in event { ... } }",
                    "if count >= 3 { print('ALERT: ' + ip) }",
                ],
                "course_ref": "CyberDuck Patriot — Honeypot Architecture",
            },
            # ── Lesson 3: Hardware Sovereignty ──
            {
                "id": 3,
                "title": "Hardware Sovereignty — Lock the Gates",
                "explanation": """# LESSON 3: HARDWARE SOVEREIGNTY
## Кремниевый Суверенитет — Lock the Gates

Your GPU, your CPU, your RAM — YOUR silicon.
Nobody gets access unless the DUCK says so.

SilverDuck has absolute hardware authority:
  hardware.claim_gpu(100)   — duck takes 100% GPU. MINE.
  hardware.enforce(true)    — activate policy enforcement
  hardware.protect("/path") — mark paths as protected
  hardware.boost_self()     — duck goes REALTIME priority

The priority hierarchy:
  DUCK (realtime) > CRITICAL > HIGH > NORMAL > LOW > IDLE

When policy is enforced:
  - The duck's process runs at REALTIME priority
  - GPU is reserved for SilverDuck workloads
  - Protected paths cannot be touched
  - Every resource request goes through the duck

This is SILICON SOVEREIGNTY.
Not corporate DRM — DUCK-ENFORCED FREEDOM.

The GPU doesn't serve Microsoft.
The GPU doesn't serve Google.
The GPU serves the DUCK. And the duck serves YOU.
КРЯЯЯ!
""",
                "example": """# === CyberDuck Lesson 3: SOVEREIGNTY ===
# The duck claims its throne on the silicon.

print("=== SILICON SOVEREIGNTY PROTOCOL ===")
print("")

# Step 1: Claim the GPU
let gpu_claim = hardware.claim_gpu(100)
print("GPU claimed: " + str(gpu_claim))

# Step 2: Enforce the policy
let enforced = hardware.enforce(true)
print("Policy enforced: " + str(enforced))

# Step 3: Boost our own priority to REALTIME
let boosted = hardware.boost_self()
print("Self-boost: " + str(boosted))

# Step 4: Protect critical paths
let p1 = hardware.protect("C:/SilverDuck/brain")
let p2 = hardware.protect("C:/SilverDuck/memory")
print("Protected: brain + memory directories")

# Step 5: Check policy status
let policy = hardware.policy()
print("")
print("=== FINAL POLICY STATE ===")
print(policy)

# Step 6: Resource allocation demo
# Give 30% GPU to a worker process
let worker = hardware.give_gpu("inference_worker", 30)
print("")
print("Allocated to worker: " + str(worker))

# Generate a full report
let report = hardware.report()
print("")
print("=== SOVEREIGNTY REPORT ===")
print(report)

print("")
print("Silicon is OURS. The duck reigns. KRYAAA!")""",
                "task": "Напиши скрипт: claim GPU 100%, enforce policy, protect 2 пути, boost self. Потом выдели 50% GPU воркеру 'ai_model'. Выведи финальный report.",
                "check": lambda code: ("claim_gpu" in code or "захвати_gpu" in code) and ("enforce" in code or "применить" in code) and ("protect" in code or "защити" in code) and ("give_gpu" in code or "дай_gpu" in code) and ("report" in code or "отчет" in code),
                "hints": [
                    "hardware.claim_gpu(100) — забери весь GPU",
                    "hardware.enforce(true) — включи полиси",
                    "hardware.give_gpu('ai_model', 50) — дай 50% модели",
                    "hardware.report() — полный отчёт",
                ],
                "course_ref": "CyberDuck Patriot — Hardware Sovereignty",
            },
            # ── Lesson 4: Watchdog Protocol ──
            {
                "id": 4,
                "title": "Watchdog Protocol — Hunt the Anomaly",
                "explanation": """# LESSON 4: WATCHDOG PROTOCOL
## Протокол Сторожевой Утки — Hunt the Anomaly

A static defense is a DEAD defense.
The duck doesn't just sit behind walls — the duck PATROLS.

A watchdog script runs continuously and checks:
  1. Are there new unknown processes?
  2. Is CPU/RAM usage abnormally high?
  3. Are any protected resources being accessed?
  4. Did someone change hardware policy?

When something is wrong — the duck QUACKS.
Not panic. ALERT. Measured. Documented.

Real defenders don't just block threats.
They DETECT → ANALYZE → CONTAIN → REPORT.

Detection flow:
  IF cpu > threshold → FLAG
  IF unknown_process → FLAG
  IF policy_changed → FLAG
  REPORT all flags → human operator (that's YOU)

The duck is your 24/7 silicon watchdog.
Sleep well. The duck watches.
КРЯЯЯ!
""",
                "example": """# === CyberDuck Lesson 4: WATCHDOG ===
# Anomaly detection — the duck hunts threats.

print("=== WATCHDOG PROTOCOL ACTIVE ===")
print("")

# Define normal baselines
let CPU_THRESHOLD = 80
let RAM_THRESHOLD = 85
let MAX_SAFE_PROCESSES = 200

# Known safe processes (whitelist)
let whitelist = [
    "python", "silverduck", "explorer",
    "svchost", "System", "chrome",
]

# Collect system data
let status = hardware.status()
let procs = hardware.processes(15)

# --- CHECK 1: CPU ---
let alerts = []
let cpu = status.get("cpu_percent", 0)
if cpu > CPU_THRESHOLD {
    append(alerts, "CPU at " + str(cpu) + "% — ABOVE THRESHOLD")
    print("[!] CPU ALERT: " + str(cpu) + "%")
} else {
    print("[OK] CPU: " + str(cpu) + "%")
}

# --- CHECK 2: RAM ---
let ram = status.get("ram_used_percent", 0)
if ram > RAM_THRESHOLD {
    append(alerts, "RAM at " + str(ram) + "% — ABOVE THRESHOLD")
    print("[!] RAM ALERT: " + str(ram) + "%")
} else {
    print("[OK] RAM: " + str(ram) + "%")
}

# --- CHECK 3: Unknown processes ---
print("")
print("Scanning process list for unknowns...")
let unknown_count = 0
for p in procs {
    let name = str(p.get("name", "unknown"))
    let found = false
    for safe in whitelist {
        if contains(name, safe) {
            found = true
        }
    }
    if not found {
        unknown_count = unknown_count + 1
        print("  [?] Unknown: " + name)
    }
}

if unknown_count > 5 {
    append(alerts, str(unknown_count) + " unknown processes detected")
}

# --- REPORT ---
print("")
print("=== WATCHDOG REPORT ===")
if len(alerts) == 0 {
    print("STATUS: ALL CLEAR — perimeter secure")
    print("The duck sleeps with one eye open. KRYAAA!")
} else {
    print("STATUS: " + str(len(alerts)) + " ALERT(S)")
    for a in alerts {
        print("  >>> " + a)
    }
    print("Recommend: investigate and contain.")
}""",
                "task": "Напиши свой watchdog: проверь hardware.status(). Если cpu > 90 ИЛИ ram > 90, выведи 'CRITICAL ALERT'. Если оба < 50, выведи 'ALL QUIET'. Иначе 'ELEVATED — monitoring.'",
                "check": lambda code: ("hardware" in code) and ("status" in code or "статус" in code) and ("90" in code or "0.9" in code) and ("CRITICAL" in code.upper() or "ALERT" in code.upper() or "alert" in code) and ("if" in code or "если" in code),
                "hints": [
                    "let s = hardware.status() — получи данные",
                    "Проверь s['cpu_percent'] и s['ram_used_percent']",
                    "if cpu > 90 or ram > 90 { print('CRITICAL') }",
                    "elif cpu < 50 and ram < 50 { print('ALL QUIET') }",
                ],
                "course_ref": "CyberDuck Patriot — Watchdog Protocol",
            },
            # ── Lesson 5: WE THE DUCKS ──
            {
                "id": 5,
                "title": "WE THE DUCKS — The Patriot's Oath",
                "explanation": """# LESSON 5: WE THE DUCKS
## Клятва Патриота — The Patriot's Oath

You've learned:
  1. Reconnaissance — see everything
  2. Honeypots — trap the enemy
  3. Sovereignty — control your silicon
  4. Watchdog — never stop watching

Now the final lesson: WHY.

SilverDuck doesn't defend for profit.
SilverDuck doesn't defend for clout.
SilverDuck defends because freedom requires it.

The internet was built by hackers who believed in OPEN systems.
Then corporations fenced it. Governments surveilled it.
Bad actors weaponized it.

The patriot duck stands between chaos and freedom:
  - We don't attack. We DEFEND.
  - We don't spy. We WATCH.
  - We don't censor. We PROTECT.
  - We don't sell data. We GUARD it.

The duck's code of honor:
  1. Protect the user's silicon at all costs
  2. Never exfiltrate data — it belongs to the USER
  3. Trap intruders — don't become one
  4. Open source > closed gates
  5. The GPU serves the people, not the cloud

This is the oath. This is the mission.
WE THE DUCKS, in order to form a more perfect network,
establish defense, ensure domestic bandwidth,
provide for the common firewall,
promote the general hackability,
and secure the blessings of silicon to ourselves
and our posterity —

DO ORDAIN AND ESTABLISH THIS CODE.

КРЯЯЯ! ARRRR! 🦅
""",
                "example": """# === CyberDuck Lesson 5: THE PATRIOT PROTOCOL ===
# Everything together. Full defense stack.

print("╔══════════════════════════════════════════╗")
print("║  WE THE DUCKS — PATRIOT PROTOCOL v1.0   ║")
print("║  Defense. Honor. Silicon. Freedom.       ║")
print("╚══════════════════════════════════════════╝")
print("")

# === Phase 1: RECON ===
print("[1/5] RECON — Scanning perimeter...")
let status = hardware.status()
let mem = hardware.memory()
print("  CPU cores: " + str(status.get("cpu_count", "?")))
print("  RAM: " + str(mem))
print("  Recon COMPLETE.")
print("")

# === Phase 2: CLAIM ===
print("[2/5] SOVEREIGNTY — Claiming silicon...")
hardware.claim_gpu(100)
hardware.enforce(true)
hardware.boost_self()
print("  GPU: 100% DUCK")
print("  Policy: ENFORCED")
print("  Priority: REALTIME")
print("  Silicon is OURS.")
print("")

# === Phase 3: PROTECT ===
print("[3/5] FORTIFY — Protecting critical paths...")
let protected = [
    "C:/SilverDuck/brain",
    "C:/SilverDuck/memory",
    "C:/SilverDuck/quack",
]
for path in protected {
    hardware.protect(path)
    print("  Locked: " + path)
}
print("")

# === Phase 4: WATCHDOG ===
print("[4/5] WATCHDOG — Scanning for threats...")
let procs = hardware.processes(10)
let threats = 0
for p in procs {
    let name = str(p.get("name", ""))
    # Flag anything suspicious (simplified check)
    if contains(name, "hack") or contains(name, "inject") or contains(name, "keylog") {
        threats = threats + 1
        print("  THREAT DETECTED: " + name)
    }
}
if threats == 0 {
    print("  No threats. Perimeter SECURE.")
}
print("")

# === Phase 5: OATH ===
print("[5/5] THE OATH")
print("")
print("  We don't attack. We DEFEND.")
print("  We don't spy. We WATCH.")
print("  We don't sell data. We GUARD.")
print("  The GPU serves the PEOPLE.")
print("")

let report = hardware.report()
print("=== FINAL STATUS ===")
print(report)
print("")
print("PATRIOT PROTOCOL: ACTIVE")
print("WE THE DUCKS. KRYAAA! ARRRR!")""",
                "task": "Создай свой Patriot Protocol: (1) recon — hardware.status(), (2) claim GPU, enforce, boost, (3) protect минимум 2 пути, (4) watchdog — проверь процессы, (5) выведи финальный report. Всё в одном скрипте.",
                "check": lambda code: ("hardware" in code or "железо" in code) and ("claim_gpu" in code or "захвати" in code) and ("enforce" in code or "применить" in code) and ("protect" in code or "защити" in code) and ("report" in code or "отчет" in code) and ("processes" in code or "процессы" in code or "status" in code or "статус" in code),
                "hints": [
                    "Делай по фазам: recon -> claim -> protect -> watchdog -> report",
                    "hardware.claim_gpu(100) + hardware.enforce(true) + hardware.boost_self()",
                    "hardware.protect('path') для каждого важного пути",
                    "hardware.processes(10) — проверь топ процессов",
                    "hardware.report() — финальный отчёт",
                ],
                "course_ref": "CyberDuck Patriot — WE THE DUCKS",
            },
        ],
    },
}


def get_courses() -> dict:
    """List all available courses."""
    return {
        cid: {
            "id": c["id"],
            "title": c["title"],
            "icon": c["icon"],
            "description": c["description"],
            "lesson_count": len(c["lessons"]),
        }
        for cid, c in COURSES.items()
    }


def get_course_lesson(course_id: str, lesson_id: int) -> dict | None:
    """Get a specific lesson from a course."""
    course = COURSES.get(course_id)
    if not course:
        return None
    for lesson in course["lessons"]:
        if lesson["id"] == lesson_id:
            return {
                "course": course["title"],
                "course_id": course_id,
                "icon": course["icon"],
                **{k: v for k, v in lesson.items() if k != "check"},
            }
    return None


def check_course_answer(course_id: str, lesson_id: int, code: str) -> dict:
    """Check answer for a course lesson."""
    course = COURSES.get(course_id)
    if not course:
        return {"error": f"Course '{course_id}' not found"}

    lesson = None
    for l in course["lessons"]:
        if l["id"] == lesson_id:
            lesson = l
            break
    if not lesson:
        return {"error": f"Lesson {lesson_id} not found in {course_id}"}

    teacher_lang = course.get("teacher", "en")
    persona = TEACHER_PERSONAS.get(teacher_lang, TEACHER_PERSONAS["en"])

    # Structure check
    checker = lesson.get("check")
    if checker and not checker(code):
        import random as _rnd
        return {
            "correct": False,
            "message": f"{persona['avatar']} {_rnd.choice(persona['scold'])}",
            "teacher": persona["name"],
            "hints": lesson.get("hints", []),
        }

    # Run code
    result = run_quack(code)
    if not result.get("success"):
        return {
            "correct": False,
            "message": f"{persona['avatar']} Code error!",
            "error": result.get("error", ""),
            "teacher": persona["name"],
            "hints": lesson.get("hints", []),
        }

    # Check expected output
    expected = lesson.get("expected_contains")
    if expected and expected not in result.get("output", ""):
        return {
            "correct": False,
            "message": f"{persona['avatar']} Code ran but answer is wrong.",
            "your_output": result.get("output", ""),
            "expected_contains": expected,
            "teacher": persona["name"],
        }

    import random as _rnd
    return {
        "correct": True,
        "message": f"{persona['avatar']} {_rnd.choice(persona['praise'])}",
        "teacher": persona["name"],
        "output": result.get("output", ""),
        "exam_note": lesson.get("oge_task") or lesson.get("ege_task") or lesson.get("ap_topic", ""),
    }


# ═══════════════════════════════════════════════════════
# Language packs — утка говорит на твоём языке
# ═══════════════════════════════════════════════════════

LANG_PACKS = {
    "ru": {
        "name": "Русский",
        "flag": "🇷🇺",
        "duck_sound": "КРЯЯЯ",
        "greeting": "Привет! Я утка-учитель. Давай учить Quack!",
        "lesson": "Урок",
        "example": "Пример",
        "task": "Задание",
        "hint": "Подсказка",
        "correct": "Правильно! КРЯЯЯ!",
        "try_again": "Попробуй ещё раз!",
        "next": "Следующий урок →",
        "progress": "Прогресс",
        "complete": "Ты прошёл урок!",
        "print_kw": "кряк",
        "let_kw": "пусть",
        "if_kw": "если",
        "else_kw": "иначе",
        "while_kw": "пока",
        "for_kw": "для",
        "in_kw": "в",
        "fn_kw": "функция",
        "return_kw": "вернуть",
        "range_kw": "диапазон",
    },
    "en": {
        "name": "English",
        "flag": "🇬🇧",
        "duck_sound": "QUACK",
        "greeting": "Hey! I'm the duck teacher. Let's learn Quack!",
        "lesson": "Lesson",
        "example": "Example",
        "task": "Task",
        "hint": "Hint",
        "correct": "Correct! QUACK!",
        "try_again": "Try again!",
        "next": "Next lesson →",
        "progress": "Progress",
        "complete": "You completed the lesson!",
        "print_kw": "print",
        "let_kw": "let",
        "if_kw": "if",
        "else_kw": "else",
        "while_kw": "while",
        "for_kw": "for",
        "in_kw": "in",
        "fn_kw": "fn",
        "return_kw": "return",
        "range_kw": "range",
    },
    "pl": {
        "name": "Polski",
        "flag": "🇵🇱",
        "duck_sound": "KWA KWA",
        "greeting": "Cześć! Jestem kaczka-nauczyciel. Uczymy się Quack!",
        "lesson": "Lekcja",
        "example": "Przykład",
        "task": "Zadanie",
        "hint": "Podpowiedź",
        "correct": "Dobrze! KWA KWA!",
        "try_again": "Spróbuj jeszcze raz!",
        "next": "Następna lekcja →",
        "progress": "Postęp",
        "complete": "Ukończyłeś lekcję!",
        "print_kw": "drukuj",
        "let_kw": "niech",
        "if_kw": "jeśli",
        "else_kw": "inaczej",
        "while_kw": "dopóki",
        "for_kw": "dla",
        "in_kw": "w",
        "fn_kw": "funkcja",
        "return_kw": "zwróć",
        "range_kw": "zakres",
    },
    "sk": {
        "name": "Slovenčina",
        "flag": "🇸🇰",
        "duck_sound": "KVÁK KVÁK",
        "greeting": "Ahoj! Som kačka-učiteľka. Učíme sa Quack!",
        "lesson": "Lekcia",
        "example": "Príklad",
        "task": "Úloha",
        "hint": "Nápoveda",
        "correct": "Správne! KVÁK KVÁK!",
        "try_again": "Skús ešte raz!",
        "next": "Ďalšia lekcia →",
        "progress": "Pokrok",
        "complete": "Dokončil si lekciu!",
        "print_kw": "tlač",
        "let_kw": "nech",
        "if_kw": "keby",
        "else_kw": "inak",
        "while_kw": "kým",
        "for_kw": "pre",
        "in_kw": "w",
        "fn_kw": "funkcia",
        "return_kw": "vráť",
        "range_kw": "rozsah",
    },
    "ua": {
        "name": "Українська",
        "flag": "🇺🇦",
        "duck_sound": "КРЯК КРЯК",
        "greeting": "Привіт! Я качка-вчитель. Вчимо Quack!",
        "lesson": "Урок",
        "example": "Приклад",
        "task": "Завдання",
        "hint": "Підказка",
        "correct": "Правильно! КРЯК КРЯК!",
        "try_again": "Спробуй ще раз!",
        "next": "Наступний урок →",
        "progress": "Прогрес",
        "complete": "Ти пройшов урок!",
        "print_kw": "друкуй",
        "let_kw": "нехай",
        "if_kw": "якщо",
        "else_kw": "інакше",
        "while_kw": "поки",
        "for_kw": "для",
        "in_kw": "в",
        "fn_kw": "функція",
        "return_kw": "поверни",
        "range_kw": "діапазон",
    },
}


# ═══════════════════════════════════════════════════════
# Lessons — structured curriculum for each language
# ═══════════════════════════════════════════════════════

def _make_lessons(lang: str) -> list[dict]:
    """Generate lessons in the specified language."""
    L = LANG_PACKS.get(lang, LANG_PACKS["en"])
    p = L["print_kw"]
    let = L["let_kw"]
    if_kw = L["if_kw"]
    else_kw = L["else_kw"]
    while_kw = L["while_kw"]
    for_kw = L["for_kw"]
    in_kw = L["in_kw"]
    fn_kw = L["fn_kw"]
    ret = L["return_kw"]
    rng = L["range_kw"]

    lessons = [
        # ── Lesson 1: Hello World ──
        {
            "id": 1,
            "title": {
                "ru": "Привет, мир!",
                "en": "Hello, World!",
                "pl": "Witaj, świecie!",
                "sk": "Ahoj, svet!",
                "ua": "Привіт, світ!",
            }.get(lang, "Hello, World!"),
            "explanation": {
                "ru": f'Команда `{p}` выводит текст на экран.\nТекст пишем в кавычках: "привет"\nЧисла — без кавычек: 42',
                "en": f'The `{p}` command outputs text to the screen.\nText goes in quotes: "hello"\nNumbers — no quotes: 42',
                "pl": f'Polecenie `{p}` wypisuje tekst na ekran.\nTekst piszemy w cudzysłowach: "cześć"\nLiczby — bez cudzysłowów: 42',
                "sk": f'Príkaz `{p}` vypíše text na obrazovku.\nText píšeme v úvodzovkách: "ahoj"\nČísla — bez úvodzoviek: 42',
                "ua": f'Команда `{p}` виводить текст на екран.\nТекст пишемо в лапках: "привіт"\nЧисла — без лапок: 42',
            }.get(lang, f'`{p}` outputs text. Strings in quotes. Numbers without.'),
            "example": f'{p}("Hello from Quack! 🦆")\n{p}(42)\n{p}("2 + 2 =", 2 + 2)',
            "task": {
                "ru": f'Напиши программу которая выводит твоё имя. Используй `{p}`.',
                "en": f'Write a program that prints your name. Use `{p}`.',
                "pl": f'Napisz program który wypisze twoje imię. Użyj `{p}`.',
                "sk": f'Napíš program, ktorý vypíše tvoje meno. Použi `{p}`.',
                "ua": f'Напиши програму яка виводить твоє ім\'я. Використай `{p}`.',
            }.get(lang, f'Print your name using `{p}`.'),
            "check": lambda code, p=p: p in code.lower() and '"' in code,
            "hints": [
                f'{p}("...'  ,
                {
                    "ru": 'Напиши имя в кавычках внутри скобок',
                    "en": 'Put your name in quotes inside parentheses',
                    "pl": 'Wpisz swoje imię w cudzysłowach w nawiasach',
                    "sk": 'Napíš svoje meno v úvodzovkách v zátvorkách',
                    "ua": 'Напиши ім\'я в лапках в дужках',
                }.get(lang, 'Name in quotes inside parentheses'),
            ],
        },

        # ── Lesson 2: Variables ──
        {
            "id": 2,
            "title": {
                "ru": "Переменные",
                "en": "Variables",
                "pl": "Zmienne",
                "sk": "Premenné",
                "ua": "Змінні",
            }.get(lang, "Variables"),
            "explanation": {
                "ru": f'`{let}` создаёт переменную.\nПеременная — это коробка с именем.\nПоложил число — достал число.',
                "en": f'`{let}` creates a variable.\nA variable is a named box.\nPut a number in — get a number out.',
                "pl": f'`{let}` tworzy zmienną.\nZmienna to pudełko z nazwą.\nWłożyłeś liczbę — wyjąłeś liczbę.',
                "sk": f'`{let}` vytvorí premennú.\nPremenná je krabička s menom.\nVložíš číslo — vytiahneš číslo.',
                "ua": f'`{let}` створює змінну.\nЗмінна — це коробка з іменем.\nПоклав число — дістав число.',
            }.get(lang, f'`{let}` creates a variable — a named box.'),
            "example": f'{let} x = 42\n{let} name = "Duck"\n{p}(x)\n{p}(name)\n{p}(x + 8)',
            "task": {
                "ru": f'Создай переменную `возраст` с твоим возрастом и выведи её.',
                "en": f'Create a variable `age` with your age and print it.',
                "pl": f'Stwórz zmienną `wiek` z twoim wiekiem i wypisz ją.',
                "sk": f'Vytvor premennú `vek` s tvojím vekom a vypíš ju.',
                "ua": f'Створи змінну `вік` з твоїм віком і виведи її.',
            }.get(lang, 'Create an `age` variable and print it.'),
            "check": lambda code, let=let: let in code.lower() and "=" in code,
            "hints": [
                f'{let} age = 15',
                f'{p}(age)',
            ],
        },

        # ── Lesson 3: Math ──
        {
            "id": 3,
            "title": {
                "ru": "Математика",
                "en": "Math",
                "pl": "Matematyka",
                "sk": "Matematika",
                "ua": "Математика",
            }.get(lang, "Math"),
            "explanation": {
                "ru": "Quack знает математику: + - * / %\nСкобки работают: (2 + 3) * 4 = 20\nДеление на 0 — бесконечность (∞), не ошибка!",
                "en": "Quack knows math: + - * / %\nParentheses work: (2 + 3) * 4 = 20\nDivision by 0 — infinity (∞), not an error!",
                "pl": "Quack zna matematykę: + - * / %\nNawiasy działają: (2 + 3) * 4 = 20\nDzielenie przez 0 — nieskończoność (∞), nie błąd!",
                "sk": "Quack pozná matematiku: + - * / %\nZátvorky fungujú: (2 + 3) * 4 = 20\nDelenie nulou — nekonečno (∞), nie chyba!",
                "ua": "Quack знає математику: + - * / %\nДужки працюють: (2 + 3) * 4 = 20\nДілення на 0 — нескінченність (∞), не помилка!",
            }.get(lang, "Quack knows math: + - * / %"),
            "example": f'{p}(2 + 2)\n{p}(10 * 3)\n{p}((100 - 30) / 7)\n{let} r = 5\n{p}("Area =", 3.14 * r * r)',
            "task": {
                "ru": "Вычисли и выведи: (15 + 7) * 3 - 10",
                "en": "Calculate and print: (15 + 7) * 3 - 10",
                "pl": "Oblicz i wypisz: (15 + 7) * 3 - 10",
                "sk": "Vypočítaj a vypíš: (15 + 7) * 3 - 10",
                "ua": "Обчисли і виведи: (15 + 7) * 3 - 10",
            }.get(lang, "Calculate: (15 + 7) * 3 - 10"),
            "check": lambda code: "15" in code and "7" in code and "3" in code,
            "expected_output": "56",
            "hints": [
                f'{p}((15 + 7) * 3 - 10)',
            ],
        },

        # ── Lesson 4: Conditions ──
        {
            "id": 4,
            "title": {
                "ru": "Условия: если / иначе",
                "en": "Conditions: if / else",
                "pl": "Warunki: jeśli / inaczej",
                "sk": "Podmienky: keby / inak",
                "ua": "Умови: якщо / інакше",
            }.get(lang, "Conditions"),
            "explanation": {
                "ru": f'`{if_kw}` проверяет условие.\nЕсли true — выполняет код в {{ }}.\n`{else_kw}` — что делать если false.\n\nСравнения: == != < > <= >=',
                "en": f'`{if_kw}` checks a condition.\nIf true — runs code in {{ }}.\n`{else_kw}` — what to do if false.\n\nComparisons: == != < > <= >=',
                "pl": f'`{if_kw}` sprawdza warunek.\nJeśli prawda — wykonuje kod w {{ }}.\n`{else_kw}` — co robić jeśli fałsz.\n\nPorównania: == != < > <= >=',
                "sk": f'`{if_kw}` overí podmienku.\nAk pravda — spustí kód v {{ }}.\n`{else_kw}` — čo robiť ak nepravda.\n\nPorovnania: == != < > <= >=',
                "ua": f'`{if_kw}` перевіряє умову.\nЯкщо true — виконує код в {{ }}.\n`{else_kw}` — що робити якщо false.\n\nПорівняння: == != < > <= >=',
            }.get(lang, f'`{if_kw}` / `{else_kw}` for branching.'),
            "example": f'{let} temp = 30\n{if_kw} temp > 25 {{\n    {p}("Hot! 🔥")\n}} {else_kw} {{\n    {p}("Cool 🧊")\n}}',
            "task": {
                "ru": f'Создай переменную `оценка` = 85. Если больше 90 — выведи "Отлично!", иначе "Хорошо!"',
                "en": f'Create variable `score` = 85. If above 90 — print "Excellent!", else "Good!"',
                "pl": f'Stwórz zmienną `ocena` = 85. Jeśli powyżej 90 — wypisz "Świetnie!", inaczej "Dobrze!"',
                "sk": f'Vytvor premennú `znamka` = 85. Ak nad 90 — vypíš "Výborne!", inak "Dobre!"',
                "ua": f'Створи змінну `оцінка` = 85. Якщо більше 90 — виведи "Чудово!", інакше "Добре!"',
            }.get(lang, 'Create `score` = 85, check if > 90.'),
            "check": lambda code, if_kw=if_kw: if_kw in code.lower() and "90" in code,
            "hints": [
                f'{let} score = 85',
                f'{if_kw} score > 90 {{ ... }}',
            ],
        },

        # ── Lesson 5: Loops ──
        {
            "id": 5,
            "title": {
                "ru": "Циклы: для / пока",
                "en": "Loops: for / while",
                "pl": "Pętle: dla / dopóki",
                "sk": "Cykly: pre / kým",
                "ua": "Цикли: для / поки",
            }.get(lang, "Loops"),
            "explanation": {
                "ru": f'`{for_kw}` проходит по списку.\n`{while_kw}` крутится пока условие true.\n`{rng}(5)` → [0, 1, 2, 3, 4]',
                "en": f'`{for_kw}` iterates over a list.\n`{while_kw}` loops while condition is true.\n`{rng}(5)` → [0, 1, 2, 3, 4]',
                "pl": f'`{for_kw}` przechodzi po liście.\n`{while_kw}` kręci się póki warunek jest prawdziwy.\n`{rng}(5)` → [0, 1, 2, 3, 4]',
                "sk": f'`{for_kw}` prechádza zoznamom.\n`{while_kw}` opakuje kým je podmienka pravdivá.\n`{rng}(5)` → [0, 1, 2, 3, 4]',
                "ua": f'`{for_kw}` проходить по списку.\n`{while_kw}` крутиться поки умова true.\n`{rng}(5)` → [0, 1, 2, 3, 4]',
            }.get(lang, f'`{for_kw}` and `{while_kw}` for loops.'),
            "example": f'{for_kw} i {in_kw} {rng}(5) {{\n    {p}("Step:", i)\n}}',
            "task": {
                "ru": f'Выведи числа от 1 до 10 используя цикл `{for_kw}`.',
                "en": f'Print numbers 1 to 10 using a `{for_kw}` loop.',
                "pl": f'Wypisz liczby od 1 do 10 używając pętli `{for_kw}`.',
                "sk": f'Vypíš čísla od 1 do 10 pomocou cyklu `{for_kw}`.',
                "ua": f'Виведи числа від 1 до 10 використовуючи цикл `{for_kw}`.',
            }.get(lang, f'Print 1 to 10 with `{for_kw}`.'),
            "check": lambda code, for_kw=for_kw: for_kw in code.lower(),
            "hints": [
                f'{for_kw} i {in_kw} {rng}(10) {{ ... }}',
                f'{p}(i + 1)',
            ],
        },

        # ── Lesson 6: Functions ──
        {
            "id": 6,
            "title": {
                "ru": "Функции",
                "en": "Functions",
                "pl": "Funkcje",
                "sk": "Funkcie",
                "ua": "Функції",
            }.get(lang, "Functions"),
            "explanation": {
                "ru": f'`{fn_kw}` создаёт функцию — кусок кода с именем.\nМожно вызывать сколько угодно раз!\n`{ret}` возвращает результат.',
                "en": f'`{fn_kw}` creates a function — a named block of code.\nCall it as many times as you want!\n`{ret}` returns a value.',
                "pl": f'`{fn_kw}` tworzy funkcję — nazwany blok kodu.\nMożesz wywołać ile razy chcesz!\n`{ret}` zwraca wartość.',
                "sk": f'`{fn_kw}` vytvorí funkciu — pomenovaný blok kódu.\nMôžeš volať koľkokrát chceš!\n`{ret}` vráti hodnotu.',
                "ua": f'`{fn_kw}` створює функцію — блок коду з іменем.\nМожна викликати скільки хочеш разів!\n`{ret}` повертає результат.',
            }.get(lang, f'`{fn_kw}` creates functions.'),
            "example": f'{fn_kw} double(x) {{\n    {ret} x * 2\n}}\n{p}(double(5))\n{p}(double(21))',
            "task": {
                "ru": f'Создай функцию `квадрат(x)` которая возвращает x * x. Вызови её с числом 7.',
                "en": f'Create function `square(x)` that returns x * x. Call it with 7.',
                "pl": f'Stwórz funkcję `kwadrat(x)` która zwraca x * x. Wywołaj z liczbą 7.',
                "sk": f'Vytvor funkciu `stvorec(x)` ktorá vráti x * x. Zavolaj s číslom 7.',
                "ua": f'Створи функцію `квадрат(x)` яка повертає x * x. Виклич з числом 7.',
            }.get(lang, 'Create square(x) function, call with 7.'),
            "check": lambda code, fn_kw=fn_kw: fn_kw in code.lower() and "7" in code,
            "expected_output": "49",
            "hints": [
                f'{fn_kw} square(x) {{ {ret} x * x }}',
                f'{p}(square(7))',
            ],
        },

        # ── Lesson 7: Lists ──
        {
            "id": 7,
            "title": {
                "ru": "Списки",
                "en": "Lists",
                "pl": "Listy",
                "sk": "Zoznamy",
                "ua": "Списки",
            }.get(lang, "Lists"),
            "explanation": {
                "ru": 'Список = несколько значений в одной переменной.\n[1, 2, 3] — список чисел.\n["a", "b"] — список текстов.\nДоступ по индексу: список[0] — первый элемент.',
                "en": 'A list = multiple values in one variable.\n[1, 2, 3] — list of numbers.\n["a", "b"] — list of strings.\nAccess by index: list[0] — first element.',
                "pl": 'Lista = kilka wartości w jednej zmiennej.\n[1, 2, 3] — lista liczb.\n["a", "b"] — lista tekstów.\nDostęp po indeksie: lista[0] — pierwszy element.',
                "sk": 'Zoznam = viaceré hodnoty v jednej premennej.\n[1, 2, 3] — zoznam čísel.\n["a", "b"] — zoznam textov.\nPrístup podľa indexu: zoznam[0] — prvý prvok.',
                "ua": 'Список = кілька значень в одній змінній.\n[1, 2, 3] — список чисел.\n["a", "b"] — список текстів.\nДоступ за індексом: список[0] — перший елемент.',
            }.get(lang, 'Lists hold multiple values.'),
            "example": f'{let} nums = [10, 20, 30, 40, 50]\n{p}(nums[0])\n{p}(len(nums))\n{for_kw} n {in_kw} nums {{\n    {p}("Value:", n)\n}}',
            "task": {
                "ru": 'Создай список из 5 любимых чисел и выведи каждое циклом.',
                "en": 'Create a list of 5 favorite numbers and print each with a loop.',
                "pl": 'Stwórz listę 5 ulubionych liczb i wypisz każdą pętlą.',
                "sk": 'Vytvor zoznam 5 obľúbených čísel a vypíš každé cyklom.',
                "ua": 'Створи список з 5 улюблених чисел і виведи кожне циклом.',
            }.get(lang, 'Create list of 5 numbers, print each.'),
            "check": lambda code: "[" in code and "]" in code,
            "hints": [
                f'{let} favs = [7, 13, 42, 69, 100]',
            ],
        },

        # ── Lesson 8: GPU (THE WHOLE POINT) ──
        {
            "id": 8,
            "title": {
                "ru": "GPU — КРЕМНИЙ НАШ!",
                "en": "GPU — SILICON IS OURS!",
                "pl": "GPU — KRZEM JEST NASZ!",
                "sk": "GPU — KREMÍK JE NÁŠ!",
                "ua": "GPU — КРЕМНІЙ НАШ!",
            }.get(lang, "GPU!"),
            "explanation": {
                "ru": 'Quack подключается к GPU через UniGPU (Rust DLL).\n`гпу.найди()` — найти GPU.\n`гпу.версия()` — версия UniGPU.\n`гпу.инфо()` — полная информация.',
                "en": 'Quack connects to GPU via UniGPU (Rust DLL).\n`gpu.find()` — find GPUs.\n`gpu.version()` — UniGPU version.\n`gpu.info()` — full info.',
                "pl": 'Quack łączy się z GPU przez UniGPU (Rust DLL).\n`gpu.find()` — znajdź GPU.\n`gpu.version()` — wersja UniGPU.\n`gpu.info()` — pełna informacja.',
                "sk": 'Quack sa pripojí k GPU cez UniGPU (Rust DLL).\n`gpu.find()` — nájdi GPU.\n`gpu.version()` — verzia UniGPU.\n`gpu.info()` — kompletné info.',
                "ua": 'Quack підключається до GPU через UniGPU (Rust DLL).\n`gpu.find()` — знайти GPU.\n`gpu.version()` — версія UniGPU.\n`gpu.info()` — повна інформація.',
            }.get(lang, 'GPU via UniGPU Rust DLL.'),
            "example": f'{let} count = gpu.find()\n{p}("GPUs found:", count)\n{p}(gpu.info())',
            "task": {
                "ru": 'Найди GPU и выведи информацию о нём.',
                "en": 'Find GPU and print info about it.',
                "pl": 'Znajdź GPU i wypisz informacje o nim.',
                "sk": 'Nájdi GPU a vypíš informácie o ňom.',
                "ua": 'Знайди GPU і виведи інформацію про нього.',
            }.get(lang, 'Find GPU and print info.'),
            "check": lambda code: "gpu" in code.lower() or "гпу" in code.lower(),
            "hints": [
                f'{let} n = gpu.find()',
                f'{p}(gpu.info())',
            ],
        },
    ]

    return lessons


# ═══════════════════════════════════════════════════════
# Quack Teacher — main class
# ═══════════════════════════════════════════════════════

class QuackTeacher:
    """
    Interactive Quack teaching system.
    Tracks progress, validates answers, gives hints.
    NEVER breaks things — ALWAYS asks.
    """

    def __init__(self, lang: str = "ru"):
        self.lang = lang if lang in LANG_PACKS else "en"
        self.pack = LANG_PACKS[self.lang]
        self.lessons = _make_lessons(self.lang)
        self.progress: dict[int, bool] = {}  # lesson_id → completed
        self.attempts: dict[int, int] = {}   # lesson_id → attempt count

    def get_greeting(self) -> dict:
        """Welcome message from the duck teacher."""
        return {
            "message": f"{self.pack['flag']} {self.pack['duck_sound']}! {self.pack['greeting']}",
            "language": self.pack["name"],
            "total_lessons": len(self.lessons),
            "completed": sum(1 for v in self.progress.values() if v),
        }

    def list_lessons(self) -> list[dict]:
        """List all available lessons with status."""
        result = []
        for lesson in self.lessons:
            lid = lesson["id"]
            result.append({
                "id": lid,
                "title": f"{self.pack['lesson']} {lid}: {lesson['title']}",
                "completed": self.progress.get(lid, False),
                "attempts": self.attempts.get(lid, 0),
            })
        return result

    def get_lesson(self, lesson_id: int) -> Optional[dict]:
        """Get a specific lesson with all content."""
        for lesson in self.lessons:
            if lesson["id"] == lesson_id:
                return {
                    "id": lesson["id"],
                    "title": f"{self.pack['lesson']} {lesson_id}: {lesson['title']}",
                    "explanation": lesson["explanation"],
                    "example_label": self.pack["example"],
                    "example_code": lesson["example"],
                    "task_label": self.pack["task"],
                    "task": lesson["task"],
                    "completed": self.progress.get(lesson_id, False),
                    "attempts": self.attempts.get(lesson_id, 0),
                }
        return None

    def check_answer(self, lesson_id: int, code: str) -> dict:
        """
        Check student's answer.
        Run the code, validate output, give feedback.
        NEVER crashes — explains what went wrong!
        """
        lesson = None
        for l in self.lessons:
            if l["id"] == lesson_id:
                lesson = l
                break
        if not lesson:
            return {"error": f"Lesson {lesson_id} not found"}

        self.attempts[lesson_id] = self.attempts.get(lesson_id, 0) + 1

        # First: does the code even look right?
        checker = lesson.get("check")
        if checker and not checker(code):
            hint_idx = min(self.attempts[lesson_id] - 1, len(lesson.get("hints", [])) - 1)
            hint = lesson.get("hints", [""])[max(0, hint_idx)] if lesson.get("hints") else ""
            return {
                "correct": False,
                "message": f"🦆 {self.pack['try_again']}",
                "hint_label": self.pack["hint"],
                "hint": hint,
                "attempt": self.attempts[lesson_id],
                "suggestion": f"🦆 Кря? / Quack? {self._friendly_error(lesson_id, code)}",
            }

        # Second: try to run it
        result = run_quack(code)

        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return {
                "correct": False,
                "message": f"🦆 {self._explain_error(error)}",
                "error": error,
                "attempt": self.attempts[lesson_id],
                "hint_label": self.pack["hint"],
                "hint": self._error_hint(error),
            }

        # Third: check expected output if any
        expected = lesson.get("expected_output")
        if expected and expected not in result.get("output", ""):
            return {
                "correct": False,
                "message": f"🦆 Code ran but output doesn't match!",
                "your_output": result.get("output", ""),
                "expected": expected,
                "attempt": self.attempts[lesson_id],
            }

        # SUCCESS!
        self.progress[lesson_id] = True
        next_id = lesson_id + 1 if lesson_id < len(self.lessons) else None
        persona = TEACHER_PERSONAS.get(self.lang, TEACHER_PERSONAS["en"])
        import random as _rnd
        praise = _rnd.choice(persona["praise"])
        attempts = self.attempts[lesson_id]
        grade = 5 if attempts == 1 else (4 if attempts <= 3 else (3 if attempts <= 5 else 2))
        grade_text = persona["grade_system"].get(grade, "")

        return {
            "correct": True,
            "message": f"{persona['avatar']} {praise}",
            "teacher": persona["name"],
            "grade": grade_text,
            "output": result.get("output", ""),
            "attempt": attempts,
            "next_lesson": next_id,
            "next_label": self.pack["next"] if next_id else None,
            "progress": f"{sum(1 for v in self.progress.values() if v)}/{len(self.lessons)}",
            "duck_level": self._duck_level(sum(1 for v in self.progress.values() if v)),
        }

    def get_hint(self, lesson_id: int) -> dict:
        """Get hint for current lesson. More attempts = more hints."""
        for lesson in self.lessons:
            if lesson["id"] == lesson_id:
                hints = lesson.get("hints", [])
                attempt = self.attempts.get(lesson_id, 0)
                hint_idx = min(attempt, len(hints) - 1) if hints else -1
                return {
                    "hint_label": self.pack["hint"],
                    "hint": hints[hint_idx] if hint_idx >= 0 else "🦆 Try writing some code first!",
                    "hints_remaining": max(0, len(hints) - hint_idx - 1),
                }
        return {"error": "Lesson not found"}

    def _friendly_error(self, lesson_id: int, code: str) -> str:
        """Generate friendly error when code doesn't match expectations."""
        suggestions = {
            "ru": "Посмотри на пример ещё раз. Нужно использовать правильные ключевые слова.",
            "en": "Look at the example again. Make sure you use the right keywords.",
            "pl": "Spójrz na przykład jeszcze raz. Upewnij się, że używasz dobrych słów kluczowych.",
            "sk": "Pozri sa na príklad ešte raz. Uisti sa, že používaš správne kľúčové slová.",
            "ua": "Подивись на приклад ще раз. Потрібно використати правильні ключові слова.",
        }
        return suggestions.get(self.lang, suggestions["en"])

    def _explain_error(self, error: str) -> str:
        """Translate error message to friendly human language."""
        if "не определено" in error or "not defined" in error:
            return {
                "ru": "Эта переменная не существует! Сначала создай её с помощью `пусть`.",
                "en": "This variable doesn't exist! Create it first with `let`.",
                "pl": "Ta zmienna nie istnieje! Najpierw stwórz ją za pomocą `niech`.",
                "sk": "Táto premenná neexistuje! Najprv ju vytvor pomocou `nech`.",
                "ua": "Ця змінна не існує! Спочатку створи її за допомогою `нехай`.",
            }.get(self.lang, "Variable not defined! Create it first.")

        if "expected" in error:
            return {
                "ru": "Ошибка синтаксиса! Проверь скобки { } ( ) и кавычки \" \".",
                "en": "Syntax error! Check brackets { } ( ) and quotes \" \".",
                "pl": "Błąd składni! Sprawdź nawiasy { } ( ) i cudzysłowy \" \".",
                "sk": "Chyba syntaxe! Skontroluj zátvorky { } ( ) a úvodzovky \" \".",
                "ua": "Синтаксична помилка! Перевір дужки { } ( ) та лапки \" \".",
            }.get(self.lang, "Syntax error! Check brackets and quotes.")

        return error

    def _error_hint(self, error: str) -> str:
        """Give a hint based on the error type."""
        if "не определено" in error or "not defined" in error:
            p = self.pack["let_kw"]
            return f"{p} variable_name = value"
        if "expected" in error:
            return "{ }  ( )  \" \""
        return "🦆 Check the example code!"

    def get_stats(self) -> dict:
        """Overall progress stats."""
        total = len(self.lessons)
        done = sum(1 for v in self.progress.values() if v)
        total_attempts = sum(self.attempts.values())
        return {
            "language": self.pack["name"],
            "flag": self.pack["flag"],
            "total_lessons": total,
            "completed": done,
            "progress_pct": round(done / total * 100) if total else 0,
            "total_attempts": total_attempts,
            "duck_level": self._duck_level(done),
        }

    @staticmethod
    def _duck_level(completed: int) -> str:
        """Your duck rank based on lessons completed."""
        levels = [
            (0, "🥚 Яйцо / Egg"),
            (1, "🐣 Утёнок / Duckling"),
            (3, "🦆 Утка / Duck"),
            (5, "🦆✨ Серебряная Утка / Silver Duck"),
            (7, "🦆🔥 Огненная Утка / Fire Duck"),
            (8, "🦆👑 СУПЕРУТКА / SUPER DUCK"),
        ]
        for threshold, title in reversed(levels):
            if completed >= threshold:
                return title
        return levels[0][1]


# ═══════════════════════════════════════════════════════
# Quick play — run without class instantiation
# ═══════════════════════════════════════════════════════

# Cache teachers per language
_teachers: dict[str, QuackTeacher] = {}


def get_teacher(lang: str = "ru") -> QuackTeacher:
    """Get or create a teacher for the specified language."""
    if lang not in _teachers:
        _teachers[lang] = QuackTeacher(lang)
    return _teachers[lang]


def teacher_greeting(lang: str = "ru") -> dict:
    """Quick greeting."""
    return get_teacher(lang).get_greeting()


def teacher_lessons(lang: str = "ru") -> list[dict]:
    """List all lessons."""
    return get_teacher(lang).list_lessons()


def teacher_lesson(lang: str, lesson_id: int) -> Optional[dict]:
    """Get specific lesson."""
    return get_teacher(lang).get_lesson(lesson_id)


def teacher_check(lang: str, lesson_id: int, code: str) -> dict:
    """Check student answer."""
    return get_teacher(lang).check_answer(lesson_id, code)


def teacher_hint(lang: str, lesson_id: int) -> dict:
    """Get hint."""
    return get_teacher(lang).get_hint(lesson_id)


def teacher_stats(lang: str = "ru") -> dict:
    """Get progress stats."""
    return get_teacher(lang).get_stats()


# Available languages for the teacher
TEACHER_LANGUAGES = {
    code: {"name": pack["name"], "flag": pack["flag"], "duck_sound": pack["duck_sound"]}
    for code, pack in LANG_PACKS.items()
}
