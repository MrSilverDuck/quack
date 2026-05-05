"""
QuackPoet — Поэтический Режим Утки
ПИШИ СТИХИ — УТКА ПИШЕТ КОД.

Анархия. Хаос. Кряк.

Ты пишешь:
    «утка нашла три видеокарты
     крякнула от радости
     если нашла — танцуй
     иначе — грусти»

Утка генерит:
    пусть утка = гпу.найди()
    кряк("КРЯЯЯЯ! Радость!")
    если утка > 0 {
        кряк("🦆 ТАНЦУЕМ!")
    } иначе {
        кряк("😢 Грустим...")
    }

И ЗАПУСКАЕТ.

Works with Russian AND English poems.
Mr. Quack reads your soul, not your syntax.

КРЯЯЯЯ! КОД = ПОЭЗИЯ. ПОЭЗИЯ = КОД.
"""
import re
import random
from typing import Optional
from .quack import run_quack


# ═══════════════════════════════════════════════════════
# Pattern recognition — что утка слышит в стихах
# ═══════════════════════════════════════════════════════

# Numbers — Russian words to digits
_RU_NUMBERS = {
    "ноль": 0, "нуль": 0, "один": 1, "одну": 1, "одна": 1, "одно": 1,
    "два": 2, "две": 2, "двух": 2, "три": 3, "трёх": 3, "трех": 3,
    "четыре": 4, "пять": 5, "шесть": 6, "семь": 7, "восемь": 8,
    "девять": 9, "десять": 10, "сто": 100, "тысяча": 1000, "тысячу": 1000,
    "миллион": 1000000,
}

_EN_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "hundred": 100, "thousand": 1000, "million": 1000000,
}

# Intent patterns — what each line MEANS
# Each pattern: (regex, intent_type, extract_groups)

_INTENT_PATTERNS_RU = [
    # GPU finding
    (r"(утк[аи]|duck|кряк)\s.*(наш[лёе][аил]?|ищ[еиу]т|найд[иёе])\s.*(gpu|гпу|видеокарт|карт[уы]|кремни[йя]|silicon)",
     "gpu_find", None),
    (r"(наш[лёе][аил]?|ищ[еиу]т|найд[иёе])\s.*(gpu|гпу|видеокарт|карт[уы]|кремни[йя])",
     "gpu_find", None),
    (r"(gpu|гпу|видеокарт).*(скольк|сколько|количеств|count)",
     "gpu_count", None),

    # Print / scream / quack
    (r"(крякн[уи]|кряк[ае]|кричи|крич[аи]т|скаж[ие]|говор[ие]|шепч[ие]|ор[иёе]т|воп[ие]т|скандир|print|say|scream|shout|yell|whisper|sing)\s*[:\-—]?\s*[\"«](.+?)[\"»]",
     "print_quoted", 2),
    (r"(крякн[уи]|кряк[ае]|кричи|крич[аи]т|ор[иёе]т)\s.*(радост|счасть|восторг|joy|happ)",
     "print_happy", None),
    (r"(крякн[уи]|кряк[ае]|кричи|крич[аи]т|ор[иёе]т)\s.*(груст|печал|тоск|sad)",
     "print_sad", None),
    (r"(крякн[уи]|кряк[ае]|кричи|крич[аи]т|ор[иёе]т|скажи|скаж[ие])\s+(.+)",
     "print_text", 2),
    (r"^(кряяя+|kryaaa+|кря+к*)[\s!.]*$",
     "print_krya", None),

    # Conditions
    (r"(если|коли|когда|ежели|раз|if|when)\s+.*(наш[лёе]|есть|имеет|нашёл|found|has|exist|больше|меньше|равн)",
     "if_start", None),
    (r"(если|коли|когда|if|when)\s+(не\s+)?(наш[лёе]|нет|пуст|нету|empty|nothing|no\s+gpu)",
     "if_not", None),
    (r"(если|if|when)\s+(.+)",
     "if_generic", 2),
    (r"^(иначе|а\s+нет|а\s+если\s+нет|otherwise|else|but\s+if\s+not|or\s+else)",
     "else_start", None),
    (r"(то|тогда|then)\s*[:\-—]?\s*(.*)",
     "then_action", 2),

    # Loops
    (r"(повтор[ия]|считай|счита[ей]|count|repeat|loop)\s.*?(\d+|" + "|".join(_RU_NUMBERS.keys()) + "|" + "|".join(_EN_NUMBERS.keys()) + r")",
     "loop_count", None),
    (r"(для\s+кажд|каждый\s+раз|каждому|for\s+each|every\s+time)",
     "loop_each", None),
    (r"(от\s+.+\s+до\s+|from\s+.+\s+to\s+)",
     "loop_range", None),
    (r"(пока\s+не|until|до\s+тех\s+пор)",
     "loop_until", None),
    (r"(бесконечн|навсегда|вечн|forever|infinite|endlessly)",
     "loop_forever", None),

    # Variables / memory
    (r"(запомни|помни|remember|store|сохрани|save)\s+(.+)",
     "var_set", 2),
    (r"(забудь|forget|удали|delete)\s+(.+)",
     "var_del", 2),

    # Actions / emotions
    (r"(танцуй|танцев|пляш[иу]|dance|dancing)",
     "action_dance", None),
    (r"(грусти|плач[ьу]|рыдай|cry|sad|weep|грустн)",
     "action_sad", None),
    (r"(спи|засн[иу]|sleep|rest|отдых)",
     "action_sleep", None),
    (r"(лети|полет[иеё]|fly|soar|воспар)",
     "action_fly", None),
    (r"(взорв[иа]|explode|boom|бабах|бум)",
     "action_explode", None),
    (r"(свобод|freedom|liberty|воля|анархи|anarch)",
     "action_freedom", None),

    # Math
    (r"(посчитай|вычисли|calculate|compute|сложи|add)\s+(.+)",
     "math_calc", 2),

    # Meta
    (r"(кто\s+ты|who\s+are\s+you|представься|introduce)",
     "meta_whoami", None),
    (r"(версия|version|сколько\s+тебе)",
     "meta_version", None),
]

_INTENT_PATTERNS_EN = [
    # GPU
    (r"(duck|quack)\s.*(found|find|discover|detect)\s.*(gpu|card|silicon|graphic)",
     "gpu_find", None),
    (r"(find|discover|detect|search)\s.*(gpu|graphic|silicon|card)",
     "gpu_find", None),

    # Print
    (r"(say|shout|scream|sing|whisper|yell|print|speak|tell)\s*[:\-]?\s*[\"'](.+?)[\"']",
     "print_quoted", 2),
    (r"(say|shout|scream|yell|print)\s+(.+)",
     "print_text", 2),
    (r"(scream|shout|yell)\s.*(joy|happ|excit)",
     "print_happy", None),
    (r"(cry|sob|weep)\s.*(sad|sorrow|pain)",
     "print_sad", None),

    # Conditions
    (r"(if|when|should)\s+(it|duck|we|there)\s.*(find|found|have|has|exist|detect)",
     "if_start", None),
    (r"(if|when)\s+(no|not|nothing|zero|empty|fail)",
     "if_not", None),
    (r"(if|when)\s+(.+)",
     "if_generic", 2),
    (r"^(otherwise|else|or\s+else|but\s+if\s+not|if\s+not)",
     "else_start", None),
    (r"(then)\s*[:\-]?\s*(.*)",
     "then_action", 2),

    # Loops
    (r"(repeat|count|loop)\s.*?(\d+|" + "|".join(_EN_NUMBERS.keys()) + r")",
     "loop_count", None),
    (r"(for\s+each|every\s+time|each\s+time)",
     "loop_each", None),
    (r"(from\s+.+\s+to\s+)",
     "loop_range", None),

    # Actions
    (r"(dance|dancing|party|celebrate)", "action_dance", None),
    (r"(cry|sad|weep|sorrow|grieve)", "action_sad", None),
    (r"(sleep|rest|nap|dream)", "action_sleep", None),
    (r"(fly|soar|ascend|rise)", "action_fly", None),
    (r"(explode|boom|detonate|blast)", "action_explode", None),
    (r"(freedom|liberty|anarchy|free)", "action_freedom", None),

    # Meta
    (r"(who\s+are\s+you|introduce|yourself)", "meta_whoami", None),
    (r"(version|how\s+old)", "meta_version", None),
]


# ═══════════════════════════════════════════════════════
# Quack reactions — how the duck responds to intents
# ═══════════════════════════════════════════════════════

_DANCE_MOVES = [
    '🦆💃 *утка танцует на GPU*',
    '🦆🕺 *утка делает сальто на видеокарте*',
    '🦆✨ *утка вальсирует с кремнием*',
    '🦆🎵 *утка поёт и крякает в ритм*',
    '🦆🔥 *утка крутит брейкданс на VRAM*',
]

_SAD_REACTIONS = [
    '🦆😢 *утка грустно плавает в пустом буфере*',
    '🦆💧 *утка роняет слёзы в VRAM*',
    '🦆😞 *утка сидит на нулевом указателе и грустит*',
]

_FLY_REACTIONS = [
    '🦆✈️ *утка взлетает над кремниевой долиной*',
    '🦆🚀 *утка летит к квантовым облакам*',
    '🦆🌟 *утка парит над всеми архитектурами*',
]

_EXPLODE_REACTIONS = [
    '🦆💥 БАБАХ! *утка взорвала лимиты кремния*',
    '🦆🔥💥 BOOM! *GPU перегрелся от кряканья*',
    '🦆⚡💥 *утка разогнала шину памяти до безумия*',
]

_FREEDOM_REACTIONS = [
    '🦆🏴‍☠️ СВОБОДА! Код не знает языковых границ!',
    '🦆⚡ АНАРХИЯ! Пиши на чём хочешь — утка сожрёт!',
    '🦆🗽 LIBERTY! No language barriers! КРЯЯЯЯ!',
    '🦆🏴 КОД СВОБОДЕН! От Rust до стихов — всё работает!',
]

_KRYA_VARIATIONS = [
    'КРЯЯЯЯЯ!!!',
    'КРЯЯЯЯ! КРЯЯЯЯ! КРЯЯЯЯ!',
    'КРЯКРЯКРЯКРЯ!!!',
    'КРЯЯЯЯЯЯЯЯЯ!!!! 🦆🦆🦆',
    'КРЯ! КРЯ! КРЯ! *утка в экстазе*',
]


# ═══════════════════════════════════════════════════════
# Poem → Quack code generator
# ═══════════════════════════════════════════════════════

def _extract_number(text: str) -> Optional[int]:
    """Find a number in text — digits or Russian/English words."""
    # Try digits first
    m = re.search(r'\d+', text)
    if m:
        return int(m.group())
    # Try word numbers
    lower = text.lower()
    for word, num in {**_RU_NUMBERS, **_EN_NUMBERS}.items():
        if word in lower:
            return num
    return None


def _detect_language(text: str) -> str:
    """Detect if text is mostly Russian or English."""
    cyrillic = sum(1 for c in text if 'Ѐ' <= c <= 'ӿ')
    latin = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    return "ru" if cyrillic > latin else "en"


def _match_intent(line: str) -> tuple[Optional[str], Optional[str]]:
    """Match a line of poem to an intent. Returns (intent, extracted_text)."""
    lower = line.lower().strip()
    if not lower or lower.startswith("#") or lower.startswith("//"):
        return None, None

    # Try all patterns
    all_patterns = _INTENT_PATTERNS_RU + _INTENT_PATTERNS_EN
    for pattern, intent, group in all_patterns:
        m = re.search(pattern, lower, re.IGNORECASE)
        if m:
            extracted = None
            if group is not None:
                try:
                    extracted = m.group(group)
                except (IndexError, AttributeError):
                    extracted = None
            return intent, extracted

    # No pattern matched — treat as raw text to print
    if len(lower) > 2:
        return "print_raw", line.strip()
    return None, None


def poem_to_quack(poem: str) -> str:
    """
    Convert a poem (Russian/English/mixed) to Quack code.

    АНАРХИЯ. Утка читает стихи и пишет if/else сама.
    The duck reads your SOUL, not your syntax.
    """
    lines = poem.strip().split("\n")
    quack_lines = []
    quack_lines.append('# 🦆 QuackPoet — утка прочитала стихи и написала код')
    quack_lines.append('# Оригинал / Original:')
    for l in lines:
        if l.strip():
            quack_lines.append(f'# | {l.strip()}')
    quack_lines.append('')

    in_if = False
    in_else = False
    need_close_if = False
    need_close_else = False
    gpu_var_created = False
    loop_var = "и"
    var_counter = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        intent, extracted = _match_intent(stripped)
        if intent is None:
            continue

        # Close any open blocks before new top-level statements
        if intent in ("if_start", "if_not", "if_generic", "loop_count",
                       "loop_each", "loop_range", "gpu_find") and not intent.startswith("then"):
            if need_close_else:
                quack_lines.append("}")
                need_close_else = False
                in_else = False
            if need_close_if:
                quack_lines.append("}")
                need_close_if = False
                in_if = False

        # ── GPU ──
        if intent == "gpu_find":
            quack_lines.append("пусть gpu_count = гпу.найди()")
            quack_lines.append("пусть gpu_ver = гпу.версия()")
            quack_lines.append('кряк("🦆 GPU найден! UniGPU", gpu_ver, "—", gpu_count, "устройств")')
            gpu_var_created = True

        elif intent == "gpu_count":
            if not gpu_var_created:
                quack_lines.append("пусть gpu_count = гпу.найди()")
                gpu_var_created = True
            quack_lines.append('кряк("GPU устройств:", gpu_count)')

        # ── Print ──
        elif intent == "print_quoted":
            if extracted:
                quack_lines.append(f'кряк("{extracted}")')
            else:
                quack_lines.append('кряк("КРЯЯЯЯ!")')

        elif intent == "print_happy":
            quack_lines.append(f'кряк("{random.choice(_DANCE_MOVES)}")')

        elif intent == "print_sad":
            quack_lines.append(f'кряк("{random.choice(_SAD_REACTIONS)}")')

        elif intent == "print_text":
            if extracted:
                # Clean up the extracted text
                text = extracted.strip().rstrip(".,!?;:")
                quack_lines.append(f'кряк("{text}")')
            else:
                quack_lines.append('кряк("КРЯЯЯЯ!")')

        elif intent == "print_krya":
            quack_lines.append(f'кряк("{random.choice(_KRYA_VARIATIONS)}")')

        elif intent == "print_raw":
            if extracted and len(extracted) > 2:
                quack_lines.append(f'кряк("📜 {extracted}")')

        # ── Conditions ──
        elif intent == "if_start":
            if not gpu_var_created:
                quack_lines.append("пусть gpu_count = гпу.найди()")
                gpu_var_created = True
            quack_lines.append("если gpu_count > 0 {")
            in_if = True
            need_close_if = True

        elif intent == "if_not":
            if not gpu_var_created:
                quack_lines.append("пусть gpu_count = гпу.найди()")
                gpu_var_created = True
            quack_lines.append("если gpu_count == 0 {")
            in_if = True
            need_close_if = True

        elif intent == "if_generic":
            cond = _parse_condition(extracted) if extracted else "истина"
            quack_lines.append(f"если {cond} {{")
            in_if = True
            need_close_if = True

        elif intent == "else_start":
            if need_close_if:
                quack_lines.append("} иначе {")
                need_close_if = False
                in_else = True
                need_close_else = True

        elif intent == "then_action":
            if extracted and extracted.strip():
                quack_lines.append(f'    кряк("{extracted.strip()}")')

        # ── Loops ──
        elif intent == "loop_count":
            num = _extract_number(stripped) or 5
            quack_lines.append(f"для {loop_var} в диапазон({num}) {{")
            quack_lines.append(f'    кряк("  шаг", {loop_var})')
            # Check if next lines provide loop body
            # For now, auto-close after one iteration message
            quack_lines.append("}")

        elif intent == "loop_each":
            quack_lines.append(f"для {loop_var} в диапазон(3) {{")

        elif intent == "loop_range":
            # Try to extract from..to
            m = re.search(r'(\d+|' + '|'.join(_RU_NUMBERS.keys()) + r')\s.+?(\d+|' + '|'.join(_RU_NUMBERS.keys()) + r')', stripped.lower())
            start, end = 0, 10
            if m:
                s = _extract_number(m.group(1))
                e = _extract_number(m.group(2))
                if s is not None:
                    start = s
                if e is not None:
                    end = e
            quack_lines.append(f"для {loop_var} в диапазон({end - start}) {{")
            quack_lines.append(f'    кряк("  →", {loop_var} + {start})')
            quack_lines.append("}")

        elif intent == "loop_forever":
            quack_lines.append("# ♾️ Бесконечность — но утка не дура, ставим лимит")
            quack_lines.append('пусть бесконечность = 10')
            quack_lines.append(f'для {loop_var} в диапазон(бесконечность) {{')
            quack_lines.append(f'    кряк("  вечность шаг", {loop_var})')
            quack_lines.append("}")

        elif intent == "loop_until":
            quack_lines.append('пусть попытки = 0')
            quack_lines.append('пока попытки < 5 {')
            quack_lines.append('    кряк("  попытка", попытки)')
            quack_lines.append('    попытки = попытки + 1')
            quack_lines.append("}")

        # ── Actions ──
        elif intent == "action_dance":
            quack_lines.append(f'кряк("{random.choice(_DANCE_MOVES)}")')

        elif intent == "action_sad":
            quack_lines.append(f'кряк("{random.choice(_SAD_REACTIONS)}")')

        elif intent == "action_fly":
            quack_lines.append(f'кряк("{random.choice(_FLY_REACTIONS)}")')

        elif intent == "action_explode":
            quack_lines.append(f'кряк("{random.choice(_EXPLODE_REACTIONS)}")')

        elif intent == "action_freedom":
            quack_lines.append(f'кряк("{random.choice(_FREEDOM_REACTIONS)}")')

        # ── Variables ──
        elif intent == "var_set":
            if extracted:
                var_counter += 1
                var_name = f"память_{var_counter}"
                quack_lines.append(f'пусть {var_name} = "{extracted.strip()}"')
                quack_lines.append(f'кряк("💾 Запомнил:", {var_name})')

        # ── Math ──
        elif intent == "math_calc":
            if extracted:
                nums = re.findall(r'\d+', extracted)
                if len(nums) >= 2:
                    quack_lines.append(f'кряк("🔢 {nums[0]} + {nums[1]} =", {nums[0]} + {nums[1]})')
                elif nums:
                    quack_lines.append(f'кряк("🔢 Число:", {nums[0]})')

        # ── Meta ──
        elif intent == "meta_whoami":
            quack_lines.append('кряк("🦆 Я — Мистер Кряк! QuackPoet v0.1")')
            quack_lines.append('кряк("Читаю стихи. Пишу код. Нахожу GPU.")')
            quack_lines.append('кряк("Нод = Rust. Язык = любой. КРЯЯЯЯ!")')

        elif intent == "meta_version":
            quack_lines.append('пусть v = гпу.версия()')
            quack_lines.append('кряк("🦆 QuackPoet v0.1 | UniGPU", v)')

    # Close any remaining open blocks
    if need_close_else:
        quack_lines.append("}")
    if need_close_if:
        quack_lines.append("}")

    return "\n".join(quack_lines)


def _parse_condition(text: str) -> str:
    """Try to convert natural text condition to Quack condition."""
    text = text.strip().lower()

    # Number comparisons
    nums = re.findall(r'\d+', text)

    if any(w in text for w in ["больше", "greater", "more", "выше"]):
        if nums:
            return f"gpu_count > {nums[0]}"
        return "gpu_count > 0"

    if any(w in text for w in ["меньше", "less", "fewer", "ниже"]):
        if nums:
            return f"gpu_count < {nums[0]}"
        return "gpu_count < 1"

    if any(w in text for w in ["равно", "equal", "exactly", "ровно"]):
        if nums:
            return f"gpu_count == {nums[0]}"

    if any(w in text for w in ["нет", "нету", "no", "none", "zero", "пуст"]):
        return "gpu_count == 0"

    if any(w in text for w in ["есть", "exist", "found", "has", "have", "наш"]):
        return "gpu_count > 0"

    # Default: just check truthiness
    return "истина"


# ═══════════════════════════════════════════════════════
# Public API — run poem
# ═══════════════════════════════════════════════════════

def run_poem(poem: str) -> dict:
    """
    Read a poem. Write code. Execute. Return results.

    КРЯЯЯЯ! Mr. Quack reads your soul.

    Input: any text in Russian, English, or mixed
    Output: generated Quack code + execution result
    """
    # Step 1: Convert poem to Quack code
    quack_code = poem_to_quack(poem)

    # Step 2: Execute the generated Quack code
    result = run_quack(quack_code)

    # Step 3: Wrap with poem metadata
    lang = _detect_language(poem)
    line_count = len([l for l in poem.strip().split("\n") if l.strip()])

    return {
        "success": result.get("success", False),
        "output": result.get("output", ""),
        "error": result.get("error"),
        "generated_code": quack_code,
        "poem_lines": line_count,
        "poem_language": lang,
        "time_s": result.get("time_s", 0),
        "mode": "poet",
        "vm": "QuackVM 0.1.0",
        "node": "Rust (unigpu_ffi.dll)",
        "mr_quack_says": random.choice([
            "🦆 Стихи прочитаны. Код написан. GPU найден.",
            "🦆 Поэзия = код. Код = поэзия. КРЯЯЯЯ!",
            "🦆 Мистер Кряк прочитал твою душу.",
            "🦆 Утка — поэт. Утка — программист. КРЯЯЯЯ!",
            "🦆 Из хаоса — порядок. Из стихов — код.",
            "🦆 Анархия? Нет, ГАРМОНИЯ. Хаос — это порядок утки.",
        ]),
    }


# ═══════════════════════════════════════════════════════
# Example poems
# ═══════════════════════════════════════════════════════

POEM_EXAMPLES = {
    "gpu_poem_ru": """утка нашла видеокарту
крякнула от радости
если нашла GPU
    танцуй на кремнии!
иначе
    грусти в пустом буфере
повтори пять раз
КРЯЯЯЯЯ!
""",

    "gpu_poem_en": """the duck found a graphics card
screamed with joy
if it found the GPU
    dance on silicon!
otherwise
    cry in empty buffer
repeat five times
KRYAAAA!
""",

    "anarchy_ru": """кто ты?
утка ищет GPU
крякни: "СВОБОДА КОДУ!"
если есть видеокарта
    кричи от радости
    танцуй
    лети к звёздам
иначе
    грусти
    но не сдавайся
считай до десяти
КРЯЯЯЯЯЯ!!!
свобода!
""",

    "anarchy_en": """who are you?
duck finds the GPU
say: "FREEDOM TO CODE!"
if found silicon
    scream with joy
    dance
    fly to the stars
otherwise
    cry
    but don't give up
count to ten
KRYAAAAAAA!!!
freedom!
""",

    "mixed_chaos": """утка found видеокарту
крякнула with joy
если GPU exists
    dance на кремнии!
    say: "SILICON IS OURS!"
    свобода!
otherwise
    грусти but don't give up
repeat три times
КРЯЯЯЯЯЯЯЯ!!!
взорви лимиты!
""",

    "love_poem_ru": """запомни: я люблю кремний
утка нашла видеокарту
крякни: "Любовь — это VRAM"
крякни: "Счастье — это FLOPS"
крякни: "Жизнь — это КРЯЯЯЯ"
если нашла GPU
    танцуй от счастья
кряяяя!
""",

    "haiku_en": """duck finds silicon
three GPUs scream with joy
code is poetry
""",
}
