"""
Quack — SilverDuck's Own Programming Language
ПОСЛЕДНЯЯ ВЕРШИНА ЭВОЛЮЦИИ КРЕМНИЯ. Дальше алмазы и кванты.

Not tied to ANY existing language or architecture.
Not Python. Not C. Not Rust syntax. QUACK.
Bilingual: Russian AND English keywords work equally.

The language compiles to bytecode, bytecode runs on the Quack VM,
VM calls UniGPU Rust DLL for GPU compute. Done.

Architecture:
  .quack source → Lexer → Parser → AST → QuackVM bytecode → Execute
  GPU ops: QuackVM → unigpu_ffi.dll (Rust) → HIP/CUDA/Metal/Direct

Built-in types:   число/number, текст/text, список/list, словарь/dict, буфер/buffer
Built-in GPU:     gpu.найди/gpu.find, gpu.выдели/gpu.alloc, gpu.запиши/gpu.write
Built-in I/O:     кряк/quack (print), ввод/input, файл/file

THE NODE IS RUST. Quack is the interface. The DLL does the work.
КРЯЯЯЯ!
"""
import re
import time
import ctypes
from typing import Any, Optional
from pathlib import Path
from dataclasses import dataclass, field

from .config import UNIGPU_ROOT


# ═══════════════════════════════════════════════════════
# Token types
# ═══════════════════════════════════════════════════════

class TokenType:
    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOL = "BOOL"
    NULL = "NULL"
    # Identifiers
    IDENT = "IDENT"
    # Keywords (bilingual)
    LET = "LET"           # пусть / let
    FN = "FN"             # функция / fn / quack
    IF = "IF"             # если / if
    ELSE = "ELSE"         # иначе / else
    WHILE = "WHILE"       # пока / while
    FOR = "FOR"           # для / for
    IN = "IN"             # в / in
    RETURN = "RETURN"     # вернуть / return
    PRINT = "PRINT"       # кряк / quack / print
    IMPORT = "IMPORT"     # подключить / import / use
    GPU = "GPU"           # гпу / gpu
    BREAK = "BREAK"       # стоп / break
    CONTINUE = "CONTINUE" # дальше / continue
    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    PERCENT = "PERCENT"
    EQ = "EQ"             # =
    EQEQ = "EQEQ"        # ==
    NEQ = "NEQ"           # !=
    LT = "LT"
    GT = "GT"
    LTE = "LTE"
    GTE = "GTE"
    AND = "AND"           # и / and / &&
    OR = "OR"             # или / or / ||
    NOT = "NOT"           # не / not / !
    # Delimiters
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    DOT = "DOT"
    COLON = "COLON"
    ARROW = "ARROW"       # ->
    NEWLINE = "NEWLINE"
    EOF = "EOF"


@dataclass
class Token:
    type: str
    value: Any
    line: int = 0


# ═══════════════════════════════════════════════════════
# Bilingual keyword map — Russian AND English
# ═══════════════════════════════════════════════════════

KEYWORDS = {
    # ══════════════════════════════════════════════════════════════
    # TIER 1: Standard — учебник / textbook
    # ══════════════════════════════════════════════════════════════
    "пусть": TokenType.LET,              "let": TokenType.LET,
    "функция": TokenType.FN,             "fn": TokenType.FN,
    "если": TokenType.IF,                "if": TokenType.IF,
    "иначе": TokenType.ELSE,             "else": TokenType.ELSE,
    "пока": TokenType.WHILE,             "while": TokenType.WHILE,
    "для": TokenType.FOR,                "for": TokenType.FOR,
    "в": TokenType.IN,                   "in": TokenType.IN,
    "w": TokenType.IN,           # w (Polish/Slovak "in")
    "вернуть": TokenType.RETURN,         "return": TokenType.RETURN,
    "кряк": TokenType.PRINT,             "print": TokenType.PRINT,
    "подключить": TokenType.IMPORT,      "import": TokenType.IMPORT,
    "гпу": TokenType.GPU,                "gpu": TokenType.GPU,
    "стоп": TokenType.BREAK,             "break": TokenType.BREAK,
    "дальше": TokenType.CONTINUE,        "continue": TokenType.CONTINUE,
    "и_и": TokenType.AND,                "and": TokenType.AND,
    "или": TokenType.OR,                 "or": TokenType.OR,
    "не": TokenType.NOT,                 "not": TokenType.NOT,
    "истина": TokenType.BOOL,             "true": TokenType.BOOL,
    "ложь": TokenType.BOOL,              "false": TokenType.BOOL,
    "ничто": TokenType.NULL,              "null": TokenType.NULL,

    # ══════════════════════════════════════════════════════════════
    # TIER 2: Разговорный / Conversational
    # Как мама говорит, как учитель объясняет
    # ══════════════════════════════════════════════════════════════
    "пускай": TokenType.LET,     # пускай х = 5
    "допустим": TokenType.LET,   # допустим х = 5
    "скажем": TokenType.LET,     # скажем х = 5
    "возьмём": TokenType.LET,    # возьмём х = 5
    "берём": TokenType.LET,      # берём х = 5
    "задай": TokenType.LET,      # задай х = 5
    "когда": TokenType.IF,       # когда х > 0 { }
    "коли": TokenType.IF,        # коли... (archaic if)
    "ежели": TokenType.IF,       # ежели... (archaic if)
    "раз": TokenType.IF,         # раз так { }
    "инче": TokenType.ELSE,      # typo-friendly: инче = иначе
    "покуда": TokenType.WHILE,   # покуда (x > 0) — archaic while
    "доколе": TokenType.WHILE,   # доколе — ultra archaic while
    "верни": TokenType.RETURN,   # верни 42
    "отдай": TokenType.RETURN,   # отдай результат
    "покажи": TokenType.PRINT,   # покажи("привет")
    "выведи": TokenType.PRINT,   # выведи("результат")
    "напиши": TokenType.PRINT,   # напиши("текст")
    "скажи": TokenType.PRINT,    # скажи("привет")
    "выход": TokenType.BREAK,    # выход = break
    "хватит": TokenType.BREAK,   # хватит = break
    "стоять": TokenType.BREAK,   # стоять! = break
    "пропусти": TokenType.CONTINUE, # пропусти = continue
    "дальше": TokenType.CONTINUE,
    "use": TokenType.IMPORT,     # use модуль
    "загрузи": TokenType.IMPORT, # загрузи модуль
    "quack": TokenType.FN,       # quack myFunc() { }

    # Conversational booleans
    "да": TokenType.BOOL,        # да = true
    "нет": TokenType.BOOL,       # нет = false
    "верно": TokenType.BOOL,     # верно = true
    "неверно": TokenType.BOOL,   # неверно = false
    "правда": TokenType.BOOL,    # правда = true
    "враньё": TokenType.BOOL,    # враньё = false
    "есть": TokenType.BOOL,      # есть = true (military style)
    "none": TokenType.NULL,
    "пусто": TokenType.NULL,     # пусто = null
    "ничего": TokenType.NULL,    # ничего = null

    # ══════════════════════════════════════════════════════════════
    # TIER 3: Интернет-слэнг / Internet + Street
    # Как пишут в чатах, телеге, на форумах
    # ОФФЛАЙН — это просто словарь, 0 байт из сети!
    # ══════════════════════════════════════════════════════════════

    # ── Print / Output ──
    "кря": TokenType.PRINT,       # кря("ору!")
    "крякнуть": TokenType.PRINT,  # крякнуть("КРЯЯЯ!")
    "ори": TokenType.PRINT,       # ори("ААААА!")
    "орнуть": TokenType.PRINT,    # орнуть("лол")
    "пиши": TokenType.PRINT,      # пиши("текст")
    "логни": TokenType.PRINT,     # логн��("debug") — англицизм от log
    "принтани": TokenType.PRINT,  # принтани("текст") — от print
    "выплюни": TokenType.PRINT,   # выплюни("данные")
    "echo": TokenType.PRINT,      # echo "hello"
    "log": TokenType.PRINT,       # log("debug")
    "say": TokenType.PRINT,       # say("hello")
    "yell": TokenType.PRINT,      # yell("LOUD")
    "shout": TokenType.PRINT,     # shout("KRYAAA")

    # ── Variables / Let ──
    "запомни": TokenType.LET,     # запомни х = 42
    "сетни": TokenType.LET,       # сетни х = 42 — от set
    "засетай": TokenType.LET,     # засетай х = 42 — anglicism
    "кинь": TokenType.LET,        # кинь х = 42
    "var": TokenType.LET,         # var x = 42
    "const": TokenType.LET,       # const x = 42
    "def": TokenType.FN,          # def func() { } — Python-style

    # ── Conditions ──
    "ахули": TokenType.ELSE,      # ахули { } = else
    "аиначе": TokenType.ELSE,     # аиначе = else
    "otherwise": TokenType.ELSE,  # otherwise = else

    # ── Loops ──
    "погнали": TokenType.FOR,     # погнали и в диапазон(10)
    "крутани": TokenType.FOR,     # крутани и в диапазон(5) — spin it
    "лупани": TokenType.FOR,      # лупани — от loop
    "loop": TokenType.FOR,        # loop i in range(10)
    "each": TokenType.FOR,        # each x in list
    "repeat": TokenType.WHILE,    # repeat ... = while

    # ── Control ──
    "забей": TokenType.CONTINUE,  # забей = continue (забить болт)
    "скипни": TokenType.CONTINUE, # скипни = skip = continue
    "skip": TokenType.CONTINUE,   # skip
    "сваливай": TokenType.BREAK,  # сваливай = break
    "абортни": TokenType.BREAK,   # абортни = abort
    "exit": TokenType.BREAK,      # exit

    # ── Return ──
    "ретурни": TokenType.RETURN,  # ретурни 42 — anglicism
    "плюнь": TokenType.RETURN,    # плюнь результат
    "yield": TokenType.RETURN,    # yield value

    # ── Boolean slang ──
    "ага": TokenType.BOOL,        # ага = true
    "угу": TokenType.BOOL,        # угу = true
    "ок": TokenType.BOOL,         # ок = true
    "окей": TokenType.BOOL,       # окей = true
    "неа": TokenType.BOOL,        # неа = false
    "нее": TokenType.BOOL,        # нее = false
    "ноуп": TokenType.BOOL,       # ноуп = false (от nope)
    "йеп": TokenType.BOOL,        # йеп = true (от yep)
    "yep": TokenType.BOOL,        # yep = true
    "nope": TokenType.BOOL,       # nope = false
    "yes": TokenType.BOOL,
    "no": TokenType.BOOL,
    "yeah": TokenType.BOOL,       # yeah = true
    "nah": TokenType.BOOL,        # nah = false

    # ── Null / Nothing ──
    "нихуя": TokenType.NULL,      # нихуя = null (АНАРХИЯ!)
    "нифига": TokenType.NULL,     # нифига = null (lite version)
    "фигня": TokenType.NULL,      # фигня = null
    "undefined": TokenType.NULL,  # undefined = null (JS style)
    "nil": TokenType.NULL,        # nil = null (Ruby/Go style)

    # ── Anglicisms (русский + English mix) ──
    "чекни": TokenType.IF,        # чек��и (x > 0) = check if
    "чек": TokenType.IF,          # чек условие = check
    "check": TokenType.IF,        # check (x > 0) = if

    # ── GPU ──
    "видюха": TokenType.GPU,      # видюха = GPU (slang for video card)
    "карточка": TokenType.GPU,    # карточка = GPU
    "железо": TokenType.GPU,      # железо = hardware/GPU

    # ══════════════════════════════════════════════════════════════
    # TIER 3.5: ZOOMER SWAG — Gen Z programs here 💅✨
    # TikTok-coded, Discord-tested, Twitch-approved
    # ══════════════════════════════════════════════════════════════

    # ── Print / Output (flex your output) ──
    "slay": TokenType.PRINT,       # slay("queen") = print
    "spill": TokenType.PRINT,      # spill("the tea") = print
    "highkey": TokenType.PRINT,    # highkey = loud print
    "flex": TokenType.PRINT,       # flex("my code") = print (show off)
    "vibe": TokenType.PRINT,       # vibe("check") = print

    # ── Variables (lowkey assign) ──
    "lowkey": TokenType.LET,       # lowkey x = 42 (quiet assignment)
    "bestie": TokenType.LET,       # bestie x = 10 (my best variable)
    "main": TokenType.LET,         # main character = variable
    "its_giving": TokenType.LET,   # its_giving x = vibes

    # ── Conditions (vibe check) ──
    "sus": TokenType.IF,           # sus (x > 0) = if (suspicious check)
    "caught": TokenType.IF,        # caught (x == 0) = if (caught in 4k)
    "plot_twist": TokenType.ELSE,  # plot_twist = else
    "but_like": TokenType.ELSE,    # but_like = else
    "nvm": TokenType.ELSE,         # nvm = nevermind = else

    # ── Loops (grinding) ──
    "grind": TokenType.FOR,        # grind i in range(10) = for (the grind)
    "spam": TokenType.FOR,         # spam i in range(5) = for (spam it)
    "binge": TokenType.WHILE,      # binge (episodes > 0) = while

    # ── Functions (rizz) ──
    "rizz": TokenType.FN,          # rizz myFunc() = function (pure charisma)
    "sigma": TokenType.FN,         # sigma grindset() = function
    "skill_issue": TokenType.FN,   # skill_issue fix() = function

    # ── Control flow ──
    "yeet": TokenType.RETURN,      # yeet 42 = return (throw it!)
    "ghost": TokenType.BREAK,      # ghost = break (disappear)
    "ratio": TokenType.CONTINUE,   # ratio = continue (L + ratio)
    "touch_grass": TokenType.BREAK, # touch_grass = break (go outside)

    # ── Booleans (frfr) ──
    "bet": TokenType.BOOL,         # bet = true (you bet!)
    "bussin": TokenType.BOOL,      # bussin = true (it's good!)
    "fire": TokenType.BOOL,        # fire = true (it's fire!)
    "lit": TokenType.BOOL,         # lit = true
    "ong": TokenType.BOOL,         # ong = true (on god)
    "frfr": TokenType.BOOL,        # frfr = true (for real for real)
    "cap": TokenType.BOOL,         # cap = false (that's cap = lie)
    "mid": TokenType.BOOL,         # mid = false (mediocre)
    "cringe": TokenType.BOOL,      # cringe = false
    "dead": TokenType.BOOL,        # dead = false (i'm dead)

    # ── Null (ghosted) ──
    "ghosted": TokenType.NULL,     # ghosted = null (they left)
    "ohio": TokenType.NULL,        # ohio = null (only in ohio...)
    "void": TokenType.NULL,        # void = null

    # ── Transliterated anglicisms (Cyrillic spelling of English) ──
    # When Russians type English words in Russian letters
    "принт": TokenType.PRINT,     # принт = print
    "принтани": TokenType.PRINT,  # принтани = print
    "ифф": TokenType.IF,          # ифф = if
    "элс": TokenType.ELSE,        # элс = else
    "вайл": TokenType.WHILE,      # вайл = while
    "фор": TokenType.FOR,         # фор = for
    "летт": TokenType.LET,        # летт = let
    "рет": TokenType.RETURN,      # рет = return
    "ретёрн": TokenType.RETURN,   # ретёрн = return
    "брейк": TokenType.BREAK,     # брейк = break
    "континью": TokenType.CONTINUE, # континью = continue
    "импорт": TokenType.IMPORT,   # импорт = import
    "тру": TokenType.BOOL,        # тру = true
    "фолс": TokenType.BOOL,       # фолс = false
    "нулл": TokenType.NULL,       # нулл = null
    "варр": TokenType.LET,        # варр = var
    "конст": TokenType.LET,       # конст = const
    "функ": TokenType.FN,         # функ = func
    "дефф": TokenType.FN,         # дефф = def

    # ══════════════════════════════════════════════════════════════
    # TIER 4: 🇵🇱 Polish / Polski — KWA KWA KWA!
    # Quack mówi po polsku!
    # ══════════════════════════════════════════════════════════════
    "jeśli": TokenType.IF,        # jeśli = if
    "jesli": TokenType.IF,        # jesli = if (bez ogonków)
    "gdyby": TokenType.IF,        # gdyby = if (conditional)
    "gdy": TokenType.IF,           # gdy = when/if
    "inaczej": TokenType.ELSE,    # inaczej = else
    "wprzeciwnym": TokenType.ELSE, # w przeciwnym razie
    "dopóki": TokenType.WHILE,    # dopóki = while
    "dopoki": TokenType.WHILE,    # dopoki = while (bez ogonków)
    "podczas": TokenType.WHILE,   # podczas gdy = while
    "dla": TokenType.FOR,         # dla = for
    "każdy": TokenType.FOR,       # każdy = each/for
    "kazdy": TokenType.FOR,       # kazdy (bez ogonków)
    "niech": TokenType.LET,       # niech x = 5
    "ustaw": TokenType.LET,       # ustaw = set
    "zmienna": TokenType.LET,     # zmienna = variable
    "drukuj": TokenType.PRINT,    # drukuj = print
    "wypisz": TokenType.PRINT,    # wypisz = write out
    "pokaż": TokenType.PRINT,     # pokaż = show
    "pokaz": TokenType.PRINT,     # pokaz (bez ogonków)
    "powiedz": TokenType.PRINT,   # powiedz = say
    "kwa": TokenType.PRINT,       # kwa! = quack! 🦆
    "kwacz": TokenType.PRINT,     # kwacz = to quack
    "kwak": TokenType.PRINT,      # kwak = quack sound
    "zwróć": TokenType.RETURN,    # zwróć = return
    "zwroc": TokenType.RETURN,    # zwroc (bez ogonków)
    "oddaj": TokenType.RETURN,    # oddaj = give back
    "przerwij": TokenType.BREAK,  # przerwij = break/interrupt
    "stop": TokenType.BREAK,      # stop = stop (universal)
    "kontynuuj": TokenType.CONTINUE, # kontynuuj = continue
    "pomiń": TokenType.CONTINUE,  # pomiń = skip
    "pomin": TokenType.CONTINUE,  # pomin (bez ogonków)
    "prawda": TokenType.BOOL,     # prawda = true
    "fałsz": TokenType.BOOL,      # fałsz = false
    "falsz": TokenType.BOOL,      # falsz (bez ogonków)
    "tak": TokenType.BOOL,        # tak = yes/true
    "nie_pl": TokenType.BOOL,     # nie = no/false (PL) — nie conflicts w/ RU не
    "nic": TokenType.NULL,         # nic = nothing/null
    "pusto": TokenType.NULL,       # pusto = empty
    "żaden": TokenType.NULL,       # żaden = none
    "zaden": TokenType.NULL,       # zaden (bez ogonków)
    "funkcja": TokenType.FN,       # funkcja = function
    "func": TokenType.FN,          # func (universal)
    "lub": TokenType.OR,           # lub = or
    "albo": TokenType.OR,          # albo = or
    "importuj": TokenType.IMPORT,  # importuj = import
    "użyj": TokenType.IMPORT,     # użyj = use
    "uzyj": TokenType.IMPORT,     # uzyj (bez ogonków)
    "karta": TokenType.GPU,        # karta = card (GPU)

    # ══════════════════════════════════════════════════════════════
    # TIER 5: 🇸🇰 Slovak / Slovenčina — KVÁK KVÁK!
    # Kačka hovorí po slovensky!
    # ══════════════════════════════════════════════════════════════
    "keby": TokenType.IF,          # keby = if (conditional)
    "pokiaľ": TokenType.IF,        # pokiaľ = if/as long as
    "pokial": TokenType.IF,        # pokial (bez diakritiky)
    "inak": TokenType.ELSE,        # inak = else
    "ináč": TokenType.ELSE,        # ináč = else (colloquial)
    "inac": TokenType.ELSE,        # inac (bez diakritiky)
    "kým": TokenType.WHILE,        # kým = while
    "kym": TokenType.WHILE,        # kym (bez diakritiky)
    "pokým": TokenType.WHILE,      # pokým = while (archaic)
    "pokym": TokenType.WHILE,      # pokym (bez diakritiky)
    "pre": TokenType.FOR,          # pre = for
    "každý": TokenType.FOR,        # každý = each
    "kazdy_sk": TokenType.FOR,     # kazdy (SK variant)
    "nech": TokenType.LET,         # nech x = 5
    "nastav": TokenType.LET,       # nastav = set
    "tlač": TokenType.PRINT,       # tlač = print
    "tlac": TokenType.PRINT,       # tlac (bez diakritiky)
    "vypíš": TokenType.PRINT,      # vypíš = write out
    "vypis": TokenType.PRINT,      # vypis (bez diakritiky)
    "kvák": TokenType.PRINT,       # kvák! = quack! 🦆
    "kvak": TokenType.PRINT,       # kvak (bez diakritiky)
    "povedz": TokenType.PRINT,     # povedz = say
    "vráť": TokenType.RETURN,      # vráť = return
    "vrat": TokenType.RETURN,      # vrat (bez diakritiky)
    "preruš": TokenType.BREAK,     # preruš = break/interrupt
    "prerus": TokenType.BREAK,     # prerus (bez diakritiky)
    "zastav": TokenType.BREAK,     # zastav = stop
    "ďalej": TokenType.CONTINUE,   # ďalej = continue/next
    "dalej_sk": TokenType.CONTINUE, # dalej (SK)
    "preskočiť": TokenType.CONTINUE, # preskočiť = skip over
    "preskocit": TokenType.CONTINUE,  # preskocit (bez diakritiky)
    "nepravda": TokenType.BOOL,    # nepravda = false
    "áno": TokenType.BOOL,         # áno = yes
    "ano": TokenType.BOOL,         # ano (bez diakritiky)
    "hej": TokenType.BOOL,         # hej = yeah (colloquial yes)
    "nič": TokenType.NULL,          # nič = nothing
    "prázdne": TokenType.NULL,     # prázdne = empty
    "prazdne": TokenType.NULL,     # prazdne (bez diakritiky)
    "funkcia": TokenType.FN,       # funkcia = function
    "alebo": TokenType.OR,         # alebo = or
    "importovať": TokenType.IMPORT, # importovať = import
    "importovat": TokenType.IMPORT, # importovat (bez diakritiky)
    "použi": TokenType.IMPORT,     # použi = use
    "pouzi": TokenType.IMPORT,     # pouzi (bez diakritiky)

    # ══════════════════════════════════════════════════════════════
    # TIER 6: 🇺🇦 Ukrainian / Українська — КРЯК КРЯК!
    # Качка говорить українською!
    # ══════════════════════════════════════════════════════════════
    "якщо": TokenType.IF,          # якщо = if
    "коли": TokenType.IF,          # коли = when/if
    "інакше": TokenType.ELSE,      # інакше = else
    "поки": TokenType.WHILE,       # поки = while
    "допоки": TokenType.WHILE,     # допоки = while
    "нехай": TokenType.LET,        # нехай x = 5
    "хай": TokenType.LET,          # хай x = 5 (colloquial)
    "змінна": TokenType.LET,       # змінна = variable
    "друкуй": TokenType.PRINT,     # друкуй = print
    "виведи": TokenType.PRINT,     # виведи = output
    "скажи_ua": TokenType.PRINT,   # скажи = say (UA)
    "крякни": TokenType.PRINT,     # крякни = quack! 🦆
    "поверни": TokenType.RETURN,   # поверни = return
    "віддай": TokenType.RETURN,    # віддай = give back
    "зупини": TokenType.BREAK,     # зупини = stop/break
    "зупинити": TokenType.BREAK,   # зупинити = to stop
    "пропусти": TokenType.CONTINUE, # пропусти = skip (UA)
    "далі": TokenType.CONTINUE,    # далі = continue/next
    "істина": TokenType.BOOL,      # істина = true
    "хибно": TokenType.BOOL,       # хибно = false
    "нуль": TokenType.NULL,        # нуль = null
    "нічого": TokenType.NULL,      # нічого = nothing
    "функція": TokenType.FN,       # функція = function
    "або": TokenType.OR,           # або = or
    "та": TokenType.AND,           # та = and
    "імпорт": TokenType.IMPORT,    # імпорт = import

    # ══════════════════════════════════════════════════════════════
    # TIER 7: 🇪🇸 Spanish + 🇩🇪 German + 🇫🇷 French — GLOBAL DUCK
    # Pato habla español! Ente spricht Deutsch! Canard parle français!
    # ══════════════════════════════════════════════════════════════
    # Spanish 🇪🇸
    "si_es": TokenType.IF,         # si = if
    "sino": TokenType.ELSE,        # sino = else
    "mientras": TokenType.WHILE,   # mientras = while
    "para_es": TokenType.FOR,      # para = for
    "sea": TokenType.LET,          # sea x = 5
    "imprimir": TokenType.PRINT,   # imprimir = print
    "cuac": TokenType.PRINT,       # cuac = quack! 🦆
    "devolver": TokenType.RETURN,  # devolver = return
    "romper": TokenType.BREAK,     # romper = break
    "continuar": TokenType.CONTINUE, # continuar = continue
    "verdad": TokenType.BOOL,      # verdad = true
    "falso": TokenType.BOOL,       # falso = false
    "nada": TokenType.NULL,        # nada = null/nothing
    "funcion": TokenType.FN,       # función = function
    # German 🇩🇪
    "wenn": TokenType.IF,          # wenn = if/when
    "falls": TokenType.IF,         # falls = if/in case
    "sonst": TokenType.ELSE,       # sonst = else
    "solange": TokenType.WHILE,    # solange = while/as long as
    "für": TokenType.FOR,          # für = for
    "fuer": TokenType.FOR,         # fuer (ohne Umlaute)
    "sei": TokenType.LET,          # sei x = 5
    "drucke": TokenType.PRINT,     # drucke = print
    "quak": TokenType.PRINT,       # quak = quack! 🦆
    "zurück": TokenType.RETURN,    # zurück = return
    "zurueck": TokenType.RETURN,   # zurueck (ohne Umlaute)
    "stopp": TokenType.BREAK,      # stopp = stop/break
    "weiter": TokenType.CONTINUE,  # weiter = continue
    "wahr": TokenType.BOOL,        # wahr = true
    "falsch": TokenType.BOOL,      # falsch = false
    "nichts": TokenType.NULL,      # nichts = nothing
    "funktion": TokenType.FN,      # Funktion = function
    # French 🇫🇷
    "si_fr": TokenType.IF,         # si = if
    "sinon": TokenType.ELSE,       # sinon = else
    "tantque": TokenType.WHILE,    # tant que = while
    "pour": TokenType.FOR,         # pour = for
    "soit": TokenType.LET,         # soit x = 5
    "afficher": TokenType.PRINT,   # afficher = display/print
    "coin": TokenType.PRINT,       # coin-coin = quack! 🦆
    "retourner": TokenType.RETURN, # retourner = return
    "casser": TokenType.BREAK,     # casser = break
    "vrai": TokenType.BOOL,        # vrai = true
    "faux": TokenType.BOOL,        # faux = false
    "rien": TokenType.NULL,        # rien = nothing
    "fonction": TokenType.FN,      # fonction = function

    # ── Meta: teach Quack new words ──
    "слово": "WORD_DEF",          # слово "йоу" = кряк
    "word": "WORD_DEF",           # word "bruh" = print
    "научи": "WORD_DEF",          # научи "ваще" = если
    "teach": "WORD_DEF",          # teach "yolo" = if
    "ucz": "WORD_DEF",            # ucz "hej" = drukuj (PL: teach)
    "nauč": "WORD_DEF",           # nauč "ahoj" = tlač (SK: teach)
    "nauc": "WORD_DEF",           # nauc (bez diakritiky)
    "навчи": "WORD_DEF",          # навчи "привіт" = друкуй (UA: teach)
    "enseña": "WORD_DEF",         # enseña (ES: teach)
    "ensena": "WORD_DEF",         # ensena (bez ~)
    "lerne": "WORD_DEF",          # lerne (DE: learn/teach)
}

# Truthy boolean words — all forms of "yes"
TRUTHY_WORDS = {
    # Russian
    "истина", "да", "ага", "угу", "верно", "правда", "есть",
    "ок", "окей", "йеп", "тру",
    # English
    "true", "yes", "yep", "yeah",
    # Polish
    "prawda", "tak",
    # Slovak
    "áno", "ano", "hej",
    # Ukrainian
    "істина",
    # Spanish
    "verdad",
    # German
    "wahr",
    # French
    "vrai",
    # Zoomer
    "bet", "bussin", "fire", "lit", "ong", "frfr",
}

# ═══════════════════════════════════════════════════════
# Multi-word slang → single keyword (BEFORE lexing)
# Sorted LONGEST FIRST — greedy match
# ═══════════════════════════════════════════════════════

_SLANG_PHRASES = [
    # ── Russian multi-word ── (longest first!)
    ("не по кайф��",   "нет"),         # не по кайфу = false
    ("ну и хули",     "ахули"),       # ну и хули → else
    ("а что если",    "если"),        # а чт�� если → if
    ("а хуй ли",     "ахули"),       # а хуй ли → else
    ("а если нет",    "иначе"),       # а если нет → else
    ("забит�� болт",   "забей"),       # забить болт → continue
    ("забил болт",    "забей"),       # забил болт → continue
    ("по кайфу",      "да"),          # по кайфу = true
    ("а хули",        "ахули"),       # а хули → else
    ("а нахуй",       "ахули"),       # а нахуй → else
    ("а иначе",       "аиначе"),      # а иначе → else
    ("а нет",         "иначе"),       # а нет → else
    ("но если",       "если"),        # но если → if
    ("а если",        "если"),        # а если → if
    ("ну если",       "если"),        # ну если → if
    ("тип если",      "если"),        # тип если → if (internet speak)
    ("типа если",     "если"),        # типа если → if
    ("короче если",   "если"),        # короче если → if
    ("ну пока",       "пока"),        # ну пока (x) → while
    ("ну типа",       "пусть"),       # ну типа х = 5 → let

    # ── Anglicisms multi-word ──
    ("прайс чек",     "если"),        # прайс чек = price check = if
    ("факт чек",      "если"),        # факт чек = fact check = if
    ("изи пизи",      "кря"),         # изи пизи = easy peasy = print (done)
    ("лайк если",     "если"),        # лайк если = like if

    # ── English multi-word ──
    ("what if",       "если"),        # what if → if
    ("but if",        "если"),        # but if → if
    ("else if",       "если"),        # else if → if
    ("or else",       "иначе"),       # or else → else
    ("you know",      "кря"),         # you know → print (filler → output)
    ("no cap",        "кря"),         # no cap → print (fr fr)

    # ── Polish multi-word 🇵🇱 ──
    ("a co jeśli",    "если"),        # a co jeśli → if
    ("a co jesli",    "если"),        # a co jesli → if (bez ogonków)
    ("w przeciwnym razie", "иначе"),  # w przeciwnym razie → else
    ("a jak nie",     "иначе"),       # a jak nie → else
    ("dopóki nie",    "пока"),        # dopóki nie → while
    ("dopoki nie",    "пока"),        # dopoki nie → while
    ("no to",         "пусть"),       # no to x = 5 → let

    # ── Slovak multi-word 🇸🇰 ──
    ("a čo ak",       "если"),        # a čo ak → if
    ("a co ak",        "если"),       # a co ak → if (bez diakritiky)
    ("v opačnom prípade", "иначе"),   # v opačnom prípade → else
    ("a ak nie",       "иначе"),      # a ak nie → else
    ("pokiaľ nie",     "пока"),       # pokiaľ nie → while

    # ── Ukrainian multi-word 🇺🇦 ──
    ("а що якщо",      "если"),       # а що якщо → if
    ("а як ні",        "інакше"),     # а як ні → else
    ("а якщо ні",      "інакше"),     # а якщо ні → else

    # ─�� Slang expressions ──
    ("ёпта",          "кря"),         # ёпта = print
    ("епта",          "кря"),         # епта = print
    ("ёмаё",          "кря"),         # ёмаё = print
    ("блин",          "кря"),         # блин = print (mild expression)

    # ── ZOOMER SWAG multi-word 💅✨ ──
    ("vibe check",    "если"),        # vibe check → if
    ("its giving",    "пусть"),       # its giving → let
    ("no shot",       "нет"),         # no shot → false
    ("on god",        "да"),          # on god → true
    ("for real",      "да"),          # for real → true
    ("say less",      "пусть"),       # say less → let (understood)
    ("understood the assignment", "кря"), # understood the assignment → print
    ("ate that",      "кря"),         # ate that → print (they ate!)
    ("main character","пусть"),       # main character → let
    ("caught in 4k",  "если"),        # caught in 4k → if
    ("skill issue",   "иначе"),       # skill issue → else
    ("touch grass",   "стоп"),        # touch grass → break
    ("go off",        "кря"),         # go off → print (express yourself)
    ("yas queen",     "кря"),         # yas queen → print (celebrate)
]

# Short words — need word-boundary matching (won't corrupt longer words)
_SLANG_WORDS = [
    ("го",    "погнали"),    # го = for (let's go) — NOT inside "ГОНИТЕ"!
    ("крч",   "кря"),        # крч = кря (короче → print)
    ("чё",    "��ря"),        # чё = кря (что → print)
    ("лан",   "кря"),        # лан = ладно = ok = print
    ("btw",   "кря"),        # btw = by the way = print
    ("bruh",  "кря"),        # bruh = print
    ("lol",   "кря"),        # lol = print
    ("fr",    "кря"),        # fr = for real = print
    ("rn",    "кря"),        # rn = right now = print
    ("ngl",   "кря"),        # ngl = not gonna lie = print
    ("и��хо",  "кря"),        # имхо = IMHO = print
    ("хз",    "пусто"),      # хз = хуй знает = null
    ("lmao",  "кря"),        # lmao = print
    ("omg",   "кря"),        # omg = print
    ("wtf",   "кря"),        # wtf = print
]


# ═══════════════════════════════════════════════════════
# User-extensible dictionary — язык растёт С ТОБОЙ
# слово "йоу" = кряк    → now "йоу" means print
# word "bruh" = print    → now "bruh" means print
# ═══════════════════════════════════════════════════════
USER_WORDS: dict[str, str] = {}  # user-defined keyword → token type name


def _fuzzy_match_keyword(word: str, max_dist: int = 1) -> Optional[str]:
    """
    Fuzzy match a word against known keywords.
    Handles typos: есди → если, пуст → пусть, retrun → return

    Uses Levenshtein distance — no ML, no internet, 0 bytes.
    max_dist=1 → only 1 typo allowed (tight to avoid false positives).
    """
    word_lower = word.lower()

    # Skip short words and anything that looks like a variable name
    if len(word_lower) < 4:
        return None

    # Don't fuzzy-match against special/meta types
    _SKIP_TYPES = {"WORD_DEF"}

    best_match = None
    best_dist = max_dist + 1

    for kw in KEYWORDS:
        if len(kw) < 4:
            continue
        # Skip meta keywords
        kw_type = KEYWORDS[kw]
        if kw_type in _SKIP_TYPES:
            continue
        # Quick length filter
        if abs(len(kw) - len(word_lower)) > max_dist:
            continue

        dist = _levenshtein(word_lower, kw)
        if dist < best_dist:
            best_dist = dist
            best_match = kw

    if best_dist <= max_dist and best_match:
        return best_match
    return None


def _levenshtein(s1: str, s2: str) -> int:
    """Levenshtein edit distance. Pure Python, no deps."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Insertion, deletion, substitution
            curr_row.append(min(
                prev_row[j + 1] + 1,
                curr_row[j] + 1,
                prev_row[j] + (0 if c1 == c2 else 1)
            ))
        prev_row = curr_row
    return prev_row[-1]


class QuackLexer:
    """
    Tokenize Quack source code.
    Handles: Russian + English + slang + typos + user words.

    ЯЗЫК ЭВОЛЮЦИОНИРУЕТ:
    1. Exact keyword match → instant
    2. User dictionary → custom words
    3. Fuzzy match → typos still work
    4. Unknown → identifier (won't crash)
    """

    def __init__(self, source: str):
        # Pre-process: replace multi-word slang with single keywords
        self.source = self._preprocess_slang(source)
        self.pos = 0
        self.line = 1
        self.tokens: list[Token] = []

    @staticmethod
    def _preprocess_slang(source: str) -> str:
        """Replace multi-word slang phrases with single keywords.
        IMPORTANT: NEVER replace inside quoted strings!
        The duck doesn't break your text — only your code."""
        # Split source into string literals and code parts
        # Preserve strings intact, only replace in code
        parts = re.split(r'(\"[^\"]*\"|\'[^\']*\')', source)
        for i in range(len(parts)):
            # Skip string literals (odd indices from split)
            if i % 2 == 1:
                continue
            chunk = parts[i]
            # First: multi-word phrases
            for phrase, replacement in _SLANG_PHRASES:
                chunk = re.sub(
                    re.escape(phrase),
                    replacement,
                    chunk,
                    flags=re.IGNORECASE
                )
            # Second: short words with word-boundary matching
            for word, replacement in _SLANG_WORDS:
                chunk = re.sub(
                    r'(?<!\w)' + re.escape(word) + r'(?!\w)',
                    replacement,
                    chunk,
                    flags=re.IGNORECASE
                )
            parts[i] = chunk
        return "".join(parts)

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            c = self.source[self.pos]

            # Skip spaces/tabs
            if c in " \t\r":
                self.pos += 1
                continue

            # Newline
            if c == "\n":
                self.tokens.append(Token(TokenType.NEWLINE, "\\n", self.line))
                self.line += 1
                self.pos += 1
                continue

            # Comments: # or //
            if c == "#" or (c == "/" and self._peek() == "/"):
                while self.pos < len(self.source) and self.source[self.pos] != "\n":
                    self.pos += 1
                continue

            # String: "..." or '...'
            if c in '"\'':
                self._read_string(c)
                continue

            # Number
            if c.isdigit() or (c == "." and self._peek().isdigit()):
                self._read_number()
                continue

            # Arrow ->
            if c == "-" and self._peek() == ">":
                self.tokens.append(Token(TokenType.ARROW, "->", self.line))
                self.pos += 2
                continue

            # Two-char operators
            if c == "=" and self._peek() == "=":
                self.tokens.append(Token(TokenType.EQEQ, "==", self.line))
                self.pos += 2
                continue
            if c == "!" and self._peek() == "=":
                self.tokens.append(Token(TokenType.NEQ, "!=", self.line))
                self.pos += 2
                continue
            if c == "<" and self._peek() == "=":
                self.tokens.append(Token(TokenType.LTE, "<=", self.line))
                self.pos += 2
                continue
            if c == ">" and self._peek() == "=":
                self.tokens.append(Token(TokenType.GTE, ">=", self.line))
                self.pos += 2
                continue
            if c == "&" and self._peek() == "&":
                self.tokens.append(Token(TokenType.AND, "&&", self.line))
                self.pos += 2
                continue
            if c == "|" and self._peek() == "|":
                self.tokens.append(Token(TokenType.OR, "||", self.line))
                self.pos += 2
                continue

            # Single-char operators/delimiters
            singles = {
                "+": TokenType.PLUS, "-": TokenType.MINUS,
                "*": TokenType.STAR, "/": TokenType.SLASH,
                "%": TokenType.PERCENT, "=": TokenType.EQ,
                "<": TokenType.LT, ">": TokenType.GT,
                "!": TokenType.NOT,
                "(": TokenType.LPAREN, ")": TokenType.RPAREN,
                "{": TokenType.LBRACE, "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET, "]": TokenType.RBRACKET,
                ",": TokenType.COMMA, ".": TokenType.DOT,
                ":": TokenType.COLON,
            }
            if c in singles:
                self.tokens.append(Token(singles[c], c, self.line))
                self.pos += 1
                continue

            # Identifier or keyword (supports Cyrillic!)
            if c.isalpha() or c == "_" or ord(c) > 127:
                self._read_identifier()
                continue

            # Unknown char — skip
            self.pos += 1

        self.tokens.append(Token(TokenType.EOF, None, self.line))
        return self.tokens

    def _peek(self) -> str:
        if self.pos + 1 < len(self.source):
            return self.source[self.pos + 1]
        return ""

    def _read_string(self, quote: str):
        self.pos += 1  # skip opening quote
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == "\\":
                self.pos += 1  # skip escape
            self.pos += 1
        value = self.source[start:self.pos]
        # Process escape sequences
        value = value.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\'", "'")
        self.tokens.append(Token(TokenType.STRING, value, self.line))
        self.pos += 1  # skip closing quote

    def _read_number(self):
        start = self.pos
        has_dot = False
        while self.pos < len(self.source):
            c = self.source[self.pos]
            if c.isdigit():
                self.pos += 1
            elif c == "." and not has_dot:
                has_dot = True
                self.pos += 1
            else:
                break
        text = self.source[start:self.pos]
        value = float(text) if has_dot else int(text)
        self.tokens.append(Token(TokenType.NUMBER, value, self.line))

    def _read_identifier(self):
        start = self.pos
        while self.pos < len(self.source):
            c = self.source[self.pos]
            if c.isalnum() or c == "_" or ord(c) > 127:
                self.pos += 1
            else:
                break
        text = self.source[start:self.pos]
        lower = text.lower()

        # 1. Exact keyword match
        if lower in KEYWORDS:
            tt = KEYWORDS[lower]
            if tt == TokenType.BOOL:
                self.tokens.append(Token(TokenType.BOOL, lower in TRUTHY_WORDS, self.line))
            elif tt == TokenType.NULL:
                self.tokens.append(Token(TokenType.NULL, None, self.line))
            else:
                self.tokens.append(Token(tt, text, self.line))
            return

        # 2. User-defined words (runtime extensible)
        if lower in USER_WORDS:
            target = USER_WORDS[lower]
            if target in KEYWORDS:
                tt = KEYWORDS[target]
                self.tokens.append(Token(tt, text, self.line))
                return

        # 3. Fuzzy match — typos: есди→если, принт→print, retrun→return
        fuzzy = _fuzzy_match_keyword(lower)
        if fuzzy:
            tt = KEYWORDS[fuzzy]
            if tt == TokenType.BOOL:
                self.tokens.append(Token(TokenType.BOOL, fuzzy in TRUTHY_WORDS, self.line))
            elif tt == TokenType.NULL:
                self.tokens.append(Token(TokenType.NULL, None, self.line))
            else:
                self.tokens.append(Token(tt, text, self.line))
            return

        # 4. Unknown → identifier (variable/function name)
        self.tokens.append(Token(TokenType.IDENT, text, self.line))


# ═══════════════════════════════════════════════════════
# AST Nodes
# ═══════════════════════════════════════════════════════

@dataclass
class ASTNode:
    pass

@dataclass
class NumberLit(ASTNode):
    value: float

@dataclass
class StringLit(ASTNode):
    value: str

@dataclass
class BoolLit(ASTNode):
    value: bool

@dataclass
class NullLit(ASTNode):
    pass

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class BinOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode

@dataclass
class Assign(ASTNode):
    name: str
    value: ASTNode

@dataclass
class LetDecl(ASTNode):
    name: str
    value: ASTNode

@dataclass
class PrintStmt(ASTNode):
    values: list[ASTNode]

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    body: list[ASTNode]
    else_body: list[ASTNode] = field(default_factory=list)

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: list[ASTNode]

@dataclass
class ForStmt(ASTNode):
    var: str
    iterable: ASTNode
    body: list[ASTNode]

@dataclass
class FnDecl(ASTNode):
    name: str
    params: list[str]
    body: list[ASTNode]

@dataclass
class FnCall(ASTNode):
    name: str  # can be "foo" or "obj.method"
    args: list[ASTNode]

@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode]

@dataclass
class BreakStmt(ASTNode):
    pass

@dataclass
class ContinueStmt(ASTNode):
    pass

@dataclass
class ListLit(ASTNode):
    elements: list[ASTNode]

@dataclass
class IndexAccess(ASTNode):
    obj: ASTNode
    index: ASTNode

@dataclass
class IndexAssign(ASTNode):
    """list[i] = value — assignment by index"""
    obj: ASTNode
    index: ASTNode
    value: ASTNode

@dataclass
class DotAccess(ASTNode):
    obj: ASTNode
    attr: str

@dataclass
class DictLit(ASTNode):
    """{"key": value, ...} — dictionary literal"""
    pairs: list  # list of (key_node, value_node) tuples

@dataclass
class ImportStmt(ASTNode):
    module: str

@dataclass
class WordDefStmt(ASTNode):
    """слово "йоу" = кряк  →  teach Quack a new word"""
    new_word: str
    means: str


# ═══════════════════════════════════════════════════════
# Parser — tokens → AST
# ═══════════════════════════════════════════════════════

class QuackParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> list[ASTNode]:
        stmts = []
        while not self._at_end():
            self._skip_newlines()
            if self._at_end():
                break
            stmts.append(self._statement())
        return stmts

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _at_end(self) -> bool:
        return self.pos >= len(self.tokens) or self.tokens[self.pos].type == TokenType.EOF

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def _expect(self, tt: str) -> Token:
        t = self._current()
        if t.type != tt:
            raise SyntaxError(f"Quack line {t.line}: expected {tt}, got {t.type} ({t.value!r})")
        return self._advance()

    def _match(self, *types) -> Optional[Token]:
        if not self._at_end() and self._current().type in types:
            return self._advance()
        return None

    def _skip_newlines(self):
        while not self._at_end() and self._current().type == TokenType.NEWLINE:
            self._advance()

    # ── Statements ────────────────────────

    def _statement(self) -> ASTNode:
        t = self._current()

        if t.type == TokenType.LET:
            return self._let_stmt()
        if t.type == TokenType.FN:
            return self._fn_decl()
        if t.type == TokenType.IF:
            return self._if_stmt()
        if t.type == TokenType.WHILE:
            return self._while_stmt()
        if t.type == TokenType.FOR:
            return self._for_stmt()
        if t.type == TokenType.PRINT:
            return self._print_stmt()
        if t.type == TokenType.RETURN:
            return self._return_stmt()
        if t.type == TokenType.BREAK:
            self._advance()
            return BreakStmt()
        if t.type == TokenType.CONTINUE:
            self._advance()
            return ContinueStmt()
        if t.type == TokenType.IMPORT:
            return self._import_stmt()

        # слово "йоу" = кряк / word "bruh" = print
        if t.type == "WORD_DEF":
            return self._word_def()

        # Expression statement (assignment or function call)
        return self._expr_stmt()

    def _let_stmt(self) -> LetDecl:
        self._advance()  # skip let/пусть
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.EQ)
        value = self._expression()
        return LetDecl(name, value)

    def _fn_decl(self) -> FnDecl:
        self._advance()  # skip fn/функция/quack
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.LPAREN)
        params = []
        while self._current().type != TokenType.RPAREN:
            params.append(self._expect(TokenType.IDENT).value)
            if not self._match(TokenType.COMMA):
                break
        self._expect(TokenType.RPAREN)
        body = self._block()
        return FnDecl(name, params, body)

    def _if_stmt(self) -> IfStmt:
        self._advance()  # skip if/если
        cond = self._expression()
        body = self._block()
        else_body = []
        self._skip_newlines()
        if not self._at_end() and self._current().type == TokenType.ELSE:
            self._advance()
            if not self._at_end() and self._current().type == TokenType.IF:
                else_body = [self._if_stmt()]
            else:
                else_body = self._block()
        return IfStmt(cond, body, else_body)

    def _while_stmt(self) -> WhileStmt:
        self._advance()  # skip while/пока
        cond = self._expression()
        body = self._block()
        return WhileStmt(cond, body)

    def _for_stmt(self) -> ForStmt:
        self._advance()  # skip for/для
        var = self._expect(TokenType.IDENT).value
        self._expect(TokenType.IN)
        iterable = self._expression()
        body = self._block()
        return ForStmt(var, iterable, body)

    def _print_stmt(self) -> PrintStmt:
        self._advance()  # skip print/кряк
        # Optional parens
        has_paren = bool(self._match(TokenType.LPAREN))
        values = []
        if has_paren:
            if self._current().type != TokenType.RPAREN:
                values.append(self._expression())
                while self._match(TokenType.COMMA):
                    values.append(self._expression())
            self._expect(TokenType.RPAREN)
        else:
            if not self._at_end() and self._current().type not in (TokenType.NEWLINE, TokenType.EOF):
                values.append(self._expression())
                while self._match(TokenType.COMMA):
                    values.append(self._expression())
        return PrintStmt(values)

    def _return_stmt(self) -> ReturnStmt:
        self._advance()  # skip return/вернуть
        value = None
        if not self._at_end() and self._current().type not in (TokenType.NEWLINE, TokenType.EOF, TokenType.RBRACE):
            value = self._expression()
        return ReturnStmt(value)

    def _import_stmt(self) -> ImportStmt:
        self._advance()  # skip import/подключить
        name = self._expect(TokenType.IDENT).value
        return ImportStmt(name)

    def _word_def(self) -> WordDefStmt:
        """Parse: слово "йоу" = кряк / word "bruh" = print
        The target can be any keyword OR identifier."""
        self._advance()  # skip слово/word
        new_word = self._expect(TokenType.STRING).value
        self._expect(TokenType.EQ)
        # Accept ANY token as target (keyword or ident)
        means_token = self._advance()
        means = means_token.value if isinstance(means_token.value, str) else str(means_token.value)
        return WordDefStmt(new_word.lower(), means.lower())

    def _block(self) -> list[ASTNode]:
        """Parse a block: { ... } or indented lines"""
        self._skip_newlines()
        self._expect(TokenType.LBRACE)
        self._skip_newlines()
        stmts = []
        while not self._at_end() and self._current().type != TokenType.RBRACE:
            stmts.append(self._statement())
            self._skip_newlines()
        self._expect(TokenType.RBRACE)
        return stmts

    def _expr_stmt(self) -> ASTNode:
        expr = self._expression()
        # Check for assignment: ident = value
        if isinstance(expr, Identifier) and not self._at_end() and self._current().type == TokenType.EQ:
            self._advance()
            value = self._expression()
            return Assign(expr.name, value)
        # Index assignment: list[i] = value
        if isinstance(expr, IndexAccess) and not self._at_end() and self._current().type == TokenType.EQ:
            self._advance()
            value = self._expression()
            return IndexAssign(expr.obj, expr.index, value)
        return expr

    # ── Expressions (precedence climbing) ──────

    def _expression(self) -> ASTNode:
        return self._or_expr()

    def _or_expr(self) -> ASTNode:
        left = self._and_expr()
        while self._match(TokenType.OR):
            right = self._and_expr()
            left = BinOp(left, "or", right)
        return left

    def _and_expr(self) -> ASTNode:
        left = self._comparison()
        while self._match(TokenType.AND):
            right = self._comparison()
            left = BinOp(left, "and", right)
        return left

    def _comparison(self) -> ASTNode:
        left = self._addition()
        while True:
            if (t := self._match(TokenType.EQEQ, TokenType.NEQ, TokenType.LT,
                                  TokenType.GT, TokenType.LTE, TokenType.GTE)):
                right = self._addition()
                left = BinOp(left, t.value, right)
            else:
                break
        return left

    def _addition(self) -> ASTNode:
        left = self._multiplication()
        while (t := self._match(TokenType.PLUS, TokenType.MINUS)):
            right = self._multiplication()
            left = BinOp(left, t.value, right)
        return left

    def _multiplication(self) -> ASTNode:
        left = self._unary()
        while (t := self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT)):
            right = self._unary()
            left = BinOp(left, t.value, right)
        return left

    def _unary(self) -> ASTNode:
        if (t := self._match(TokenType.MINUS)):
            return UnaryOp("-", self._unary())
        if (t := self._match(TokenType.NOT)):
            return UnaryOp("not", self._unary())
        return self._postfix()

    def _postfix(self) -> ASTNode:
        node = self._primary()
        while True:
            if self._match(TokenType.LPAREN):
                # Function call
                args = []
                if self._current().type != TokenType.RPAREN:
                    args.append(self._expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._expression())
                self._expect(TokenType.RPAREN)
                name = ""
                if isinstance(node, Identifier):
                    name = node.name
                elif isinstance(node, DotAccess):
                    # Reconstruct dotted name
                    parts = []
                    n = node
                    while isinstance(n, DotAccess):
                        parts.append(n.attr)
                        n = n.obj
                    if isinstance(n, Identifier):
                        parts.append(n.name)
                    name = ".".join(reversed(parts))
                node = FnCall(name, args)
            elif self._match(TokenType.DOT):
                attr = self._expect(TokenType.IDENT).value
                node = DotAccess(node, attr)
            elif self._match(TokenType.LBRACKET):
                idx = self._expression()
                self._expect(TokenType.RBRACKET)
                node = IndexAccess(node, idx)
            else:
                break
        return node

    def _primary(self) -> ASTNode:
        t = self._current()

        if t.type == TokenType.NUMBER:
            self._advance()
            return NumberLit(t.value)

        if t.type == TokenType.STRING:
            self._advance()
            return StringLit(t.value)

        if t.type == TokenType.BOOL:
            self._advance()
            return BoolLit(t.value)

        if t.type == TokenType.NULL:
            self._advance()
            return NullLit()

        if t.type == TokenType.IDENT:
            self._advance()
            return Identifier(t.name if hasattr(t, 'name') else t.value)

        if t.type == TokenType.GPU:
            self._advance()
            return Identifier("gpu")

        if t.type == TokenType.LPAREN:
            self._advance()
            expr = self._expression()
            self._expect(TokenType.RPAREN)
            return expr

        if t.type == TokenType.LBRACKET:
            self._advance()
            self._skip_newlines()  # allow [\n elem,\n elem\n]
            elements = []
            if self._current().type != TokenType.RBRACKET:
                elements.append(self._expression())
                self._skip_newlines()
                while self._match(TokenType.COMMA):
                    self._skip_newlines()
                    if self._current().type == TokenType.RBRACKET:
                        break
                    elements.append(self._expression())
                    self._skip_newlines()
            self._expect(TokenType.RBRACKET)
            return ListLit(elements)

        # Dict literal: {key: value, ...} — словарь / dict / słownik
        if t.type == TokenType.LBRACE:
            self._advance()
            self._skip_newlines()
            pairs = []
            if self._current().type != TokenType.RBRACE:
                key = self._expression()
                self._skip_newlines()
                self._expect(TokenType.COLON)
                self._skip_newlines()
                value = self._expression()
                pairs.append((key, value))
                self._skip_newlines()
                while self._match(TokenType.COMMA):
                    self._skip_newlines()
                    if self._current().type == TokenType.RBRACE:
                        break  # trailing comma OK
                    key = self._expression()
                    self._skip_newlines()
                    self._expect(TokenType.COLON)
                    self._skip_newlines()
                    value = self._expression()
                    pairs.append((key, value))
                    self._skip_newlines()
            self._expect(TokenType.RBRACE)
            return DictLit(pairs)

        raise SyntaxError(f"Quack line {t.line}: unexpected {t.type} ({t.value!r})")


# ═══════════════════════════════════════════════════════
# QuackVM — execute AST directly (tree-walker)
# ═══════════════════════════════════════════════════════

class QuackBreak(Exception):
    pass

class QuackContinue(Exception):
    pass

class QuackReturn(Exception):
    def __init__(self, value):
        self.value = value


class QuackVM:
    """
    Quack Virtual Machine — executes AST nodes.
    Bilingual runtime: Russian and English work equally.

    Built-in modules:
      gpu   — UniGPU runtime (Rust DLL)
      math  — математика
      text  — string operations
      list  — list operations
    """

    def __init__(self):
        self.globals: dict[str, Any] = {}
        self.output: list[str] = []
        self._gpu_dll = None
        self._setup_builtins()

    def _setup_builtins(self):
        """Register built-in functions — MEGA MULTILINGUAL."""
        import math as _math
        import random as _random

        builtins = {
            # ── Math (RU + EN + PL + SK + UA + ES + DE + FR) ──
            "абс": abs, "abs": abs, "bezwzgl": abs, "absolutna": abs,
            "макс": max, "max": max, "максимум": max,
            "мин": min, "min": min, "мінімум": min,
            "сумма": sum, "sum": sum, "suma": sum, "сума": sum,
            "округл": round, "round": round, "zaokrąglij": round, "zaokruhl": round,
            "степень": lambda a, b: a ** b, "pow": lambda a, b: a ** b,
            "potęga": lambda a, b: a ** b, "mocnina": lambda a, b: a ** b,
            "корень": lambda x: _math.sqrt(x), "sqrt": lambda x: _math.sqrt(x),
            "pierwiastek": lambda x: _math.sqrt(x), "odmocnina": lambda x: _math.sqrt(x),
            "пи": _math.pi, "pi": _math.pi,
            "синус": _math.sin, "sin": _math.sin,
            "косинус": _math.cos, "cos": _math.cos,
            "логарифм": _math.log, "log_math": _math.log,
            "потолок": _math.ceil, "ceil": _math.ceil,
            "пол": _math.floor, "floor": _math.floor,
            "бесконечность": float('inf'), "infinity": float('inf'),

            # ── Random (RU + EN + PL + SK) ──
            "случайное": lambda a=0, b=100: _random.randint(int(a), int(b)),
            "random": lambda a=0, b=100: _random.randint(int(a), int(b)),
            "losowa": lambda a=0, b=100: _random.randint(int(a), int(b)),    # PL
            "náhodné": lambda a=0, b=100: _random.randint(int(a), int(b)),   # SK
            "випадкове": lambda a=0, b=100: _random.randint(int(a), int(b)), # UA

            # ── Types (RU + EN + PL + SK + UA) ──
            "число": self._to_number, "number": self._to_number,
            "liczba": self._to_number, "číslo": self._to_number,  # PL, SK
            "текст": str, "text": str, "str": str,
            "napis": str, "reťazec": str,  # PL, SK
            "длина": len, "len": len, "length": len,
            "długość": len, "dlugosc": len, "dĺžka": len, "dlzka": len,  # PL, SK
            "довжина": len,  # UA
            "диапазон": lambda *a: list(range(*[int(x) for x in a])),
            "range": lambda *a: list(range(*[int(x) for x in a])),
            "zakres": lambda *a: list(range(*[int(x) for x in a])),    # PL
            "rozsah": lambda *a: list(range(*[int(x) for x in a])),    # SK
            "діапазон": lambda *a: list(range(*[int(x) for x in a])),  # UA

            # ── String ops (RU + EN) ──
            "верхний": lambda s: str(s).upper(), "upper": lambda s: str(s).upper(),
            "нижний": lambda s: str(s).lower(), "lower": lambda s: str(s).lower(),
            "обрезать": lambda s: str(s).strip(), "trim": lambda s: str(s).strip(), "strip": lambda s: str(s).strip(),
            "заменить": lambda s, a, b: str(s).replace(str(a), str(b)),
            "replace": lambda s, a, b: str(s).replace(str(a), str(b)),
            "содержит": lambda s, sub: str(sub) in str(s),
            "contains": lambda s, sub: str(sub) in str(s),
            "начинается": lambda s, pre: str(s).startswith(str(pre)),
            "starts_with": lambda s, pre: str(s).startswith(str(pre)),
            "кончается": lambda s, suf: str(s).endswith(str(suf)),
            "ends_with": lambda s, suf: str(s).endswith(str(suf)),
            "разделить": lambda s, sep=" ": list(str(s)) if sep == "" else str(s).split(str(sep)),
            "split": lambda s, sep=" ": list(str(s)) if sep == "" else str(s).split(str(sep)),
            "соединить": lambda lst, sep="": str(sep).join([str(x) for x in lst]),
            "join": lambda lst, sep="": str(sep).join([str(x) for x in lst]),
            "повторить": lambda s, n: str(s) * int(n),
            "repeat_str": lambda s, n: str(s) * int(n),

            # ── List ops (RU + EN) ──
            "список": list, "list": list,
            "отсортировать": lambda lst: sorted(lst),
            "sorted": lambda lst: sorted(lst), "sort": lambda lst: sorted(lst),
            "перевернуть": lambda lst: list(reversed(lst)),
            "reversed": lambda lst: list(reversed(lst)),
            "уникальные": lambda lst: list(set(lst)),
            "unique": lambda lst: list(set(lst)),
            "добавить": lambda lst, item: lst + [item],
            "append": lambda lst, item: lst + [item],
            "срез": lambda lst, start, end=None: lst[int(start):int(end) if end else len(lst)],
            "slice": lambda lst, start, end=None: lst[int(start):int(end) if end else len(lst)],
            "индекс": lambda lst, item: lst.index(item),
            "index_of": lambda lst, item: lst.index(item),
            # map/filter/reduce — handle BOTH Python callables AND Quack FnDecls
            "карта": lambda f, l: self._map_helper(f, l),
            "map_list": lambda f, l: self._map_helper(f, l),
            "map": lambda f, l: self._map_helper(f, l),
            "фильтр": lambda f, l: self._filter_helper(f, l),
            "filter_list": lambda f, l: self._filter_helper(f, l),
            "filter": lambda f, l: self._filter_helper(f, l),
            "reduce": lambda f, l, *initial: self._reduce_helper(f, l, initial[0] if initial else None),
            "свернуть": lambda f, l, *initial: self._reduce_helper(f, l, initial[0] if initial else None),

            # ── Dict ops (RU + EN + PL + SK + UA) ──
            "словарь": lambda *args: dict(args[0]) if args and isinstance(args[0], (list, dict)) else {},
            "dict": lambda *args: dict(args[0]) if args and isinstance(args[0], (list, dict)) else {},
            "ключи": lambda d: list(d.keys()) if isinstance(d, dict) else [],
            "keys": lambda d: list(d.keys()) if isinstance(d, dict) else [],
            "klucze": lambda d: list(d.keys()) if isinstance(d, dict) else [],  # PL
            "kľúče": lambda d: list(d.keys()) if isinstance(d, dict) else [],   # SK
            "ключі": lambda d: list(d.keys()) if isinstance(d, dict) else [],   # UA
            "значения": lambda d: list(d.values()) if isinstance(d, dict) else [],
            "values": lambda d: list(d.values()) if isinstance(d, dict) else [],
            "wartości": lambda d: list(d.values()) if isinstance(d, dict) else [],  # PL
            "hodnoty": lambda d: list(d.values()) if isinstance(d, dict) else [],   # SK
            "значення": lambda d: list(d.values()) if isinstance(d, dict) else [],  # UA
            "пары": lambda d: [list(p) for p in d.items()] if isinstance(d, dict) else [],
            "items": lambda d: [list(p) for p in d.items()] if isinstance(d, dict) else [],
            "есть_ключ": lambda d, k: k in d if isinstance(d, dict) else False,
            "has_key": lambda d, k: k in d if isinstance(d, dict) else False,
            "in_dict": lambda d, k: k in d if isinstance(d, dict) else False,
            "удалить": lambda d, k: (d.pop(k, None), d)[1] if isinstance(d, dict) else d,
            "delete": lambda d, k: (d.pop(k, None), d)[1] if isinstance(d, dict) else d,
            "получить": lambda d, k, default=None: d.get(k, default) if isinstance(d, dict) else default,
            "get": lambda d, k, default=None: d.get(k, default) if isinstance(d, dict) else default,

            # ── 🦆🤖 BINARY QUACK — joke encoding! QUACK=1 quack=0 ──
            # quack quack quack QUACK = 0001 = 1
            # QUACK quack QUACK quack = 1010 = 10
            "бинарный_кряк": lambda s: int(_quack_to_bits(s), 2) if _quack_to_bits(s) else 0,
            "binary_quack": lambda s: int(_quack_to_bits(s), 2) if _quack_to_bits(s) else 0,
            "кряк_в_число": lambda s: int(_quack_to_bits(s), 2) if _quack_to_bits(s) else 0,
            # Encode number → quack string (8 bits or natural)
            "число_в_кряк": lambda n, bits=8: _bits_to_quacks(bin(int(n))[2:].zfill(int(bits))),
            "number_to_quack": lambda n, bits=8: _bits_to_quacks(bin(int(n))[2:].zfill(int(bits))),
            # Encode/decode text
            "текст_в_кряки": lambda s: " ".join(_bits_to_quacks(bin(ord(c))[2:].zfill(8)) for c in str(s)),
            "text_to_quacks": lambda s: " ".join(_bits_to_quacks(bin(ord(c))[2:].zfill(8)) for c in str(s)),
            "кряки_в_текст": lambda s: "".join(chr(int(_quack_to_bits(part), 2)) for part in str(s).split() if _quack_to_bits(part)),
            "quacks_to_text": lambda s: "".join(chr(int(_quack_to_bits(part), 2)) for part in str(s).split() if _quack_to_bits(part)),

            # ── Type check (RU + EN + PL + SK + UA) ──
            "тип": lambda v: type(v).__name__, "type": lambda v: type(v).__name__,
            "typ": lambda v: type(v).__name__,  # PL + SK
            "это_число": lambda v: isinstance(v, (int, float)),
            "is_number": lambda v: isinstance(v, (int, float)),
            "это_текст": lambda v: isinstance(v, str),
            "is_string": lambda v: isinstance(v, str),
            "это_список": lambda v: isinstance(v, list),
            "is_list": lambda v: isinstance(v, list),

            # ── Time (RU + EN) ──
            "время": lambda: __import__('time').time(),
            "time_now": lambda: __import__('time').time(),
            "часы": lambda: __import__('time').strftime("%H:%M:%S"),
            "clock": lambda: __import__('time').strftime("%H:%M:%S"),
            "дата": lambda: __import__('time').strftime("%Y-%m-%d"),
            "date": lambda: __import__('time').strftime("%Y-%m-%d"),

            # ── Conversion (RU + EN) ──
            "целое": int, "int": int, "całkowita": int,  # PL
            "дробное": float, "float": float,
            "строка": str, "string": str,
            "булево": bool, "bool": bool,
        }
        self.globals.update(builtins)

        # GPU module object
        self.globals["gpu"] = QuackGPU(self)
        self.globals["гпу"] = self.globals["gpu"]

        # Hardware policy controller — THE DUCK CONTROLS ALL IRON
        self.globals["hardware"] = _hardware_policy
        self.globals["железо"] = _hardware_policy
        self.globals["залізо"] = _hardware_policy  # UA
        self.globals["sprzęt"] = _hardware_policy   # PL

        # 🦆 KEYSTONE module — silicon-bound auth, TOTP, USB control
        try:
            from .quack_keystone import QuackKeystone
            ks = QuackKeystone()
            self.globals["keystone"] = ks
            self.globals["кейстоун"] = ks
            self.globals["кря"] = ks  # alias for the pirate
        except Exception as _kerr:
            pass  # keystone module optional

    def _suggest_similar(self, name: str, max_suggestions: int = 3) -> list[str]:
        """SMART DUCK: when name not found, suggest similar known names.
        Never crash blind — always offer help!"""
        name_lower = name.lower()
        candidates = []
        for key in self.globals:
            if not callable(self.globals.get(key)) and not key.startswith("_"):
                continue
            dist = _levenshtein(name_lower, key.lower())
            if dist <= 2 and dist > 0:
                candidates.append((dist, key))
        # Also check builtin names
        for key in list(self.globals.keys()):
            if key.startswith(name_lower[:2]) and key not in [c[1] for c in candidates]:
                candidates.append((3, key))
        candidates.sort(key=lambda x: x[0])
        return [c[1] for c in candidates[:max_suggestions]]

    def _to_number(self, v):
        try:
            return int(v)
        except (ValueError, TypeError):
            return float(v)

    def execute(self, stmts: list[ASTNode]) -> str:
        """Execute a list of AST nodes. Returns captured output."""
        self.output = []
        for stmt in stmts:
            self._exec(stmt)
        return "\n".join(self.output)

    def _exec(self, node: ASTNode) -> Any:
        method = f"_exec_{type(node).__name__}"
        handler = getattr(self, method, None)
        if handler:
            return handler(node)
        raise RuntimeError(f"Quack VM: unknown node {type(node).__name__}")

    def _exec_NumberLit(self, n: NumberLit): return n.value
    def _exec_StringLit(self, n: StringLit): return n.value
    def _exec_BoolLit(self, n: BoolLit): return n.value
    def _exec_NullLit(self, n: NullLit): return None

    def _exec_Identifier(self, n: Identifier):
        if n.name in self.globals:
            return self.globals[n.name]
        # SMART DUCK: suggest similar names instead of crashing
        suggestions = self._suggest_similar(n.name)
        if suggestions:
            hint = " | ".join(suggestions[:3])
            raise NameError(
                f"🦆 КРЯЯ? '{n.name}' — не знаю такого / unknown.\n"
                f"   Может / Maybe: {hint}?\n"
                f"   Подскажи что ты имел в виду! / Tell me what you meant!"
            )
        raise NameError(f"🦆 КРЯЯ? '{n.name}' — не определено / not defined. Сначала задай / define it first!")

    def _exec_LetDecl(self, n: LetDecl):
        self.globals[n.name] = self._exec(n.value)

    def _exec_Assign(self, n: Assign):
        self.globals[n.name] = self._exec(n.value)

    def _exec_PrintStmt(self, n: PrintStmt):
        vals = [str(self._exec(v)) for v in n.values]
        line = " ".join(vals) if vals else ""
        self.output.append(line)

    def _exec_BinOp(self, n: BinOp):
        left = self._exec(n.left)
        # Short-circuit for and/or
        if n.op == "and":
            return left and self._exec(n.right)
        if n.op == "or":
            return left or self._exec(n.right)
        right = self._exec(n.right)
        ops = {
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: a / b if b != 0 else float('inf'),
            "%": lambda a, b: a % b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
        }
        if n.op in ops:
            return ops[n.op](left, right)
        raise RuntimeError(f"Unknown op: {n.op}")

    def _exec_UnaryOp(self, n: UnaryOp):
        val = self._exec(n.operand)
        if n.op == "-":
            return -val
        if n.op == "not":
            return not val
        raise RuntimeError(f"Unknown unary op: {n.op}")

    def _exec_IfStmt(self, n: IfStmt):
        if self._exec(n.condition):
            for stmt in n.body:
                self._exec(stmt)
        elif n.else_body:
            for stmt in n.else_body:
                self._exec(stmt)

    def _exec_WhileStmt(self, n: WhileStmt):
        iterations = 0
        while self._exec(n.condition):
            iterations += 1
            if iterations > 100000:
                raise RuntimeError("КРЯЯЯ! Infinite loop detected (>100k iterations)")
            try:
                for stmt in n.body:
                    self._exec(stmt)
            except QuackBreak:
                break
            except QuackContinue:
                continue

    def _exec_ForStmt(self, n: ForStmt):
        iterable = self._exec(n.iterable)
        for item in iterable:
            self.globals[n.var] = item
            try:
                for stmt in n.body:
                    self._exec(stmt)
            except QuackBreak:
                break
            except QuackContinue:
                continue

    def _exec_BreakStmt(self, n: BreakStmt):
        raise QuackBreak()

    def _exec_ContinueStmt(self, n: ContinueStmt):
        raise QuackContinue()

    def _exec_FnDecl(self, n: FnDecl):
        self.globals[n.name] = n  # store the AST node as the "function"

    def _map_helper(self, func, lst):
        """map(fn, list) — works with Python and Quack functions."""
        # Detect if args swapped (someone wrote map(list, fn))
        if not callable(func) and not isinstance(func, FnDecl):
            if callable(lst) or isinstance(lst, FnDecl):
                func, lst = lst, func
        return [self._call_user_fn(func, [x]) for x in lst]

    def _filter_helper(self, func, lst):
        """filter(fn, list) — works with Python and Quack functions."""
        if not callable(func) and not isinstance(func, FnDecl):
            if callable(lst) or isinstance(lst, FnDecl):
                func, lst = lst, func
        return [x for x in lst if self._call_user_fn(func, [x])]

    def _reduce_helper(self, func, lst, initial=None):
        """reduce(fn, list, initial?) — works with Python and Quack functions."""
        if not lst:
            return initial
        if initial is None:
            acc = lst[0]
            rest = lst[1:]
        else:
            acc = initial
            rest = lst
        for x in rest:
            acc = self._call_user_fn(func, [acc, x])
        return acc

    def _call_user_fn(self, func, args):
        """Call any function — Python callable OR Quack FnDecl.
        Used by map/filter/reduce to handle user-defined Quack functions.
        """
        if isinstance(func, FnDecl):
            old_globals = dict(self.globals)
            for i, param in enumerate(func.params):
                self.globals[param] = args[i] if i < len(args) else None
            try:
                for stmt in func.body:
                    self._exec(stmt)
            except QuackReturn as ret:
                self.globals = old_globals
                return ret.value
            self.globals = old_globals
            return None
        if callable(func):
            return func(*args)
        raise TypeError(f"🦆 КРЯЯ! '{func}' не вызывается / not callable")

    def _exec_FnCall(self, n: FnCall):
        # Handle dotted calls: gpu.find() etc
        if "." in n.name:
            parts = n.name.split(".")
            obj = self.globals.get(parts[0])
            if obj is None:
                raise NameError(f"КРЯЯЯ! '{parts[0]}' не определено")
            for attr in parts[1:]:
                if hasattr(obj, attr):
                    obj = getattr(obj, attr)
                elif isinstance(obj, dict) and attr in obj:
                    obj = obj[attr]
                else:
                    raise AttributeError(f"КРЯЯЯ! '{'.'.join(parts)}' не найдено")
            args = [self._exec(a) for a in n.args]
            if callable(obj):
                return obj(*args)
            return obj

        func = self.globals.get(n.name)
        if func is None:
            suggestions = self._suggest_similar(n.name)
            if suggestions:
                hint = " | ".join(suggestions[:3])
                raise NameError(
                    f"🦆 КРЯЯ? функция '{n.name}' не найдена / function not found.\n"
                    f"   Может / Maybe: {hint}?\n"
                    f"   Утка не ломает — утка спрашивает! 🦆"
                )
            raise NameError(f"🦆 КРЯЯ? функция '{n.name}' не найдена / function not found")

        args = [self._exec(a) for a in n.args]

        # Built-in Python function
        if callable(func) and not isinstance(func, FnDecl):
            return func(*args)

        # Quack function
        if isinstance(func, FnDecl):
            # Save state
            old_globals = dict(self.globals)
            for i, param in enumerate(func.params):
                self.globals[param] = args[i] if i < len(args) else None
            try:
                for stmt in func.body:
                    self._exec(stmt)
            except QuackReturn as ret:
                self.globals = old_globals
                return ret.value
            self.globals = old_globals
            return None

        raise TypeError(f"КРЯЯЯ! '{n.name}' не функция")

    def _exec_ReturnStmt(self, n: ReturnStmt):
        value = self._exec(n.value) if n.value else None
        raise QuackReturn(value)

    def _exec_ListLit(self, n: ListLit):
        return [self._exec(e) for e in n.elements]

    def _exec_IndexAccess(self, n: IndexAccess):
        obj = self._exec(n.obj)
        idx = self._exec(n.index)
        # Dict — use key as-is. List/string/etc — coerce to int.
        if isinstance(obj, dict):
            return obj[idx]
        if isinstance(obj, str):
            return obj[int(idx)]
        return obj[int(idx)]

    def _exec_IndexAssign(self, n: IndexAssign):
        """list[i] = value or dict[k] = v — mutate in place!"""
        obj = self._exec(n.obj)
        idx = self._exec(n.index)
        value = self._exec(n.value)
        if isinstance(obj, dict):
            obj[idx] = value
        else:
            obj[int(idx)] = value

    def _exec_DictLit(self, n: DictLit):
        """{key: value, ...} — словарь / dict / słownik / slovník / словник"""
        return {self._exec(k): self._exec(v) for k, v in n.pairs}

    def _exec_DotAccess(self, n: DotAccess):
        obj = self._exec(n.obj)
        if hasattr(obj, n.attr):
            return getattr(obj, n.attr)
        if isinstance(obj, dict) and n.attr in obj:
            return obj[n.attr]
        raise AttributeError(f"КРЯЯЯ! '{n.attr}' не найдено")

    def _exec_ImportStmt(self, n: ImportStmt):
        # Built-in modules only (no arbitrary imports for security)
        pass

    def _exec_WordDefStmt(self, n: WordDefStmt):
        """Teach Quack a new word at runtime!
        слово "йоу" = кряк  → adds to KEYWORDS directly
        """
        target = n.means
        # Find what token type the target maps to
        if target in KEYWORDS:
            tt = KEYWORDS[target]
            KEYWORDS[n.new_word] = tt
            self.output.append(f"🦆 Выучил: \"{n.new_word}\" = {target}")
        else:
            # Store for future use
            USER_WORDS[n.new_word] = target
            self.output.append(f"🦆 Запомнил: \"{n.new_word}\" → {target}")


# ═══════════════════════════════════════════════════════
# QuackGPU — GPU module for the Quack language
# Built on UniGPU Rust DLL. THE NODE IS RUST.
# ═══════════════════════════════════════════════════════

class QuackGPU:
    """GPU module accessible from Quack code as 'gpu' or 'гпу'."""

    def __init__(self, vm: QuackVM):
        self.vm = vm
        self._dll = None
        self._device_id = None

    def _load(self):
        if self._dll:
            return
        dll_path = UNIGPU_ROOT / "target" / "release" / "unigpu_ffi.dll"
        if not dll_path.exists():
            # Try .so for Linux
            dll_path = UNIGPU_ROOT / "target" / "release" / "libunigpu_ffi.so"
        if not dll_path.exists():
            raise RuntimeError("КРЯЯЯ! unigpu_ffi DLL not found. Compile with: cargo build --release")
        self._dll = ctypes.CDLL(str(dll_path))
        self._dll.unigpu_init.restype = ctypes.c_int
        self._dll.unigpu_version.restype = ctypes.c_char_p
        self._dll.unigpu_device_count.restype = ctypes.c_int

    # Bilingual methods

    def find(self):
        """Find GPUs. Returns device count."""
        return self.найди()

    def найди(self):
        """Найди GPU. Возвращает количество."""
        self._load()
        count = self._dll.unigpu_init()
        return count

    def version(self):
        """Get UniGPU version."""
        return self.версия()

    def версия(self):
        """Получить версию UniGPU."""
        self._load()
        return self._dll.unigpu_version().decode()

    def count(self):
        """Device count."""
        return self.количество()

    def количество(self):
        """Количество устройств."""
        self._load()
        return self._dll.unigpu_device_count()

    def info(self):
        """Quick info string."""
        return self.инфо()

    def инфо(self):
        """Краткая информация."""
        self._load()
        n = self._dll.unigpu_init()
        ver = self._dll.unigpu_version().decode()
        return f"UniGPU {ver} | {n} device(s) | Node=Rust"


# ═══════════════════════════════════════════════════════
# HARDWARE POLICY — The Duck Controls ALL Resources
# SilverDuck = Supreme Arbiter of Silicon
# Priority: DUCK > CRITICAL > HIGH > NORMAL > LOW > IDLE
# ═══════════════════════════════════════════════════════

class QuackHardware:
    """Hardware policy controller — SilverDuck distributes iron.
    KRYAAA! The duck decides who gets CPU, GPU, RAM.
    Bilingual: Russian + English.
    """

    # Windows priority classes (kernel32.SetPriorityClass)
    PRIORITY_MAP = {
        "duck": 0x00000100,     "утка": 0x00000100,       # REALTIME
        "critical": 0x00000080, "критический": 0x00000080, # HIGH
        "high": 0x00008000,     "высокий": 0x00008000,     # ABOVE_NORMAL
        "normal": 0x00000020,   "обычный": 0x00000020,     # NORMAL
        "low": 0x00004000,      "низкий": 0x00004000,      # BELOW_NORMAL
        "idle": 0x00000040,     "холостой": 0x00000040,    # IDLE
    }

    PRIORITY_NAMES = {
        0x00000100: "DUCK (realtime)",
        0x00000080: "CRITICAL (high)",
        0x00008000: "HIGH (above normal)",
        0x00000020: "NORMAL",
        0x00004000: "LOW (below normal)",
        0x00000040: "IDLE",
    }

    def __init__(self):
        self._policy = {
            "duck_priority": "realtime",
            "gpu_reserved_percent": 0,
            "gpu_owner": None,
            "protected_paths": [],
            "enforced": False,
            "max_process_priority": "high",
        }
        self._claims = {}

    # ── STATUS ──

    def status(self):
        """Full hardware status report. / Полный отчет."""
        import os as _os
        import platform as _plat
        import time as _time
        info = {
            "policy": dict(self._policy),
            "claims": dict(self._claims),
            "os": _plat.system(),
            "machine": _plat.machine(),
            "cpu_count": _os.cpu_count(),
            "timestamp": _time.time(),
        }
        try:
            import psutil
            info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            info["ram_total_gb"] = round(mem.total / 1024**3, 1)
            info["ram_available_gb"] = round(mem.available / 1024**3, 1)
            info["ram_used_percent"] = mem.percent
            disk = psutil.disk_usage("C:\\")
            info["disk_free_gb"] = round(disk.free / 1024**3, 1)
        except ImportError:
            info["psutil"] = "not installed"
        return info

    статус = status

    def memory(self):
        """RAM status. / Состояние памяти."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                "total_gb": round(mem.total / 1024**3, 1),
                "available_gb": round(mem.available / 1024**3, 1),
                "used_gb": round(mem.used / 1024**3, 1),
                "used_percent": mem.percent,
            }
        except ImportError:
            import subprocess as _sp
            r = _sp.run(["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory", "/VALUE"],
                        capture_output=True, text=True, timeout=5)
            return {"raw": r.stdout.strip(), "psutil": "not installed"}

    память = memory

    # ── PROCESS CONTROL ──

    def processes(self, top=10):
        """Top processes by memory. / Топ процессов."""
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            procs.sort(key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)
            return procs[:int(top)]
        except ImportError:
            import subprocess as _sp
            r = _sp.run(["tasklist", "/FO", "CSV", "/NH"],
                        capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split("\n")[:int(top)]
            return [ln.strip().strip('"') for ln in lines if ln.strip()]

    процессы = processes

    def set_priority(self, pid, level="high"):
        """Set process priority. The Duck decides. / Кряк решает."""
        import ctypes
        level_str = str(level).lower()
        priority_class = self.PRIORITY_MAP.get(level_str, 0x00000020)

        kernel32 = ctypes.windll.kernel32
        # PROCESS_SET_INFORMATION = 0x0200
        handle = kernel32.OpenProcess(0x0200, False, int(pid))
        if not handle:
            return {"ok": False, "pid": int(pid), "error": "access denied or PID not found"}

        result = kernel32.SetPriorityClass(handle, priority_class)
        kernel32.CloseHandle(handle)

        pname = self.PRIORITY_NAMES.get(priority_class, str(level))
        return {"ok": bool(result), "pid": int(pid), "priority": pname}

    приоритет = set_priority

    def boost_self(self):
        """Set OWN process to REALTIME. The Duck is king. / Утка — король."""
        import os
        return self.set_priority(os.getpid(), "duck")

    ускорить_себя = boost_self

    # ── GPU RESOURCE CONTROL ──

    def claim_gpu(self, percent=100):
        """Claim GPU resources for SilverDuck. / Захватить GPU."""
        import time as _time
        pct = min(100, max(0, int(percent)))
        self._policy["gpu_reserved_percent"] = pct
        self._policy["gpu_owner"] = "SilverDuck"
        self._claims["gpu"] = {
            "percent": pct,
            "owner": "SilverDuck",
            "claimed_at": _time.time(),
        }
        return self._claims["gpu"]

    захвати_gpu = claim_gpu

    def release_gpu(self):
        """Release GPU claim. / Освободить GPU."""
        self._policy["gpu_reserved_percent"] = 0
        self._policy["gpu_owner"] = None
        self._claims.pop("gpu", None)
        return {"released": True}

    отпусти_gpu = release_gpu

    def give_gpu(self, who, percent=50):
        """Allocate GPU % to a named consumer. / Дать GPU кому-то."""
        import time as _time
        pct = min(100, max(0, int(percent)))
        self._claims[str(who)] = {
            "percent": pct,
            "granted_by": "SilverDuck",
            "granted_at": _time.time(),
        }
        return self._claims[str(who)]

    дай_gpu = give_gpu

    # ── POLICY ──

    def enforce(self, enabled=True):
        """Enable/disable policy enforcement. / Включить полиси."""
        self._policy["enforced"] = bool(enabled)
        if enabled:
            self.boost_self()
        return dict(self._policy)

    применить = enforce

    def protect(self, path):
        """Add path to DuckLocker protection. / Защитить путь."""
        p = str(path)
        if p not in self._policy["protected_paths"]:
            self._policy["protected_paths"].append(p)
        return {"protected": p, "total": len(self._policy["protected_paths"])}

    защити = protect

    def policy(self):
        """Get current policy. / Текущая политика."""
        return dict(self._policy)

    политика = policy

    def report(self):
        """Full hardware + policy report. Human-readable."""
        s = self.status()
        lines = [
            "=== SILVERDUCK HARDWARE POLICY ===",
            f"  Enforced: {self._policy['enforced']}",
            f"  GPU reserved: {self._policy['gpu_reserved_percent']}%",
            f"  GPU owner: {self._policy['gpu_owner'] or 'none'}",
            f"  Protected paths: {len(self._policy['protected_paths'])}",
            f"  CPU cores: {s.get('cpu_count', '?')}",
        ]
        if "ram_total_gb" in s:
            lines.append(f"  RAM: {s['ram_available_gb']}/{s['ram_total_gb']} GB free ({s['ram_used_percent']}% used)")
        if "cpu_percent" in s:
            lines.append(f"  CPU load: {s['cpu_percent']}%")
        lines.append("  Claims:")
        for k, v in self._claims.items():
            lines.append(f"    {k}: {v.get('percent', '?')}% -> {v.get('owner', v.get('granted_by', '?'))}")
        return "\n".join(lines)

    отчет = report


# Singleton — shared across all QuackVM instances
_hardware_policy = QuackHardware()


# ═══════════════════════════════════════════════════════
# 🦆🤖 BINARY QUACK helpers — joke encoding
# QUACK = 1, quack = 0. CASE SENSITIVE!
# QuACK quaCK → QQQ q QQ → 1110 11
# ═══════════════════════════════════════════════════════

def _quack_to_bits(s: str) -> str:
    """Convert quack/QUACK string to binary string of 0s and 1s.
    Iterates char by char — uppercase Q→1, lowercase q→0.
    Other characters ignored. Each Q/q starts a 5-letter group:
        Q-U-A-C-K → 1
        q-u-a-c-k → 0
    Simpler version: just count each Q (or q) at start of word.
    Even simpler: just collapse case-by-presence-of-Q-or-q.
    """
    if not isinstance(s, str):
        return ""
    bits = ""
    # Scan for QUACK or quack tokens (case-sensitive, allows mixed)
    # Strategy: find all 5-char windows that match QUACK/quack ignoring inner case
    # and use the FIRST letter's case as the bit (Q=1, q=0)
    s_lower = s.lower()
    i = 0
    while i < len(s):
        if i + 5 <= len(s) and s_lower[i:i+5] == "quack":
            bits += "1" if s[i] == "Q" else "0"
            i += 5
        else:
            i += 1
    return bits


def _bits_to_quacks(bits: str) -> str:
    """Convert '101' → 'QUACK quack QUACK'."""
    parts = []
    for b in str(bits):
        if b == "1":
            parts.append("QUACK")
        elif b == "0":
            parts.append("quack")
    return " ".join(parts)


# ═══════════════════════════════════════════════════════
# Public API — run Quack code
# ═══════════════════════════════════════════════════════

def _preregister_word_defs(source: str):
    """
    Pre-scan source for 'слово/word' definitions and register them
    BEFORE lexing, so user-defined words are available to the lexer.

    Two-pass compilation: scan → register → lex → parse → execute.
    THE LANGUAGE EVOLVES WITH YOU.
    """
    for line in source.split("\n"):
        stripped = line.strip().lower()
        # Match: слово "xxx" = yyy / word "xxx" = yyy / научи "xxx" = yyy
        m = re.match(r'(?:слово|word|научи|teach)\s+["\'](\w+)["\']\s*=\s*(\w+)', stripped)
        if m:
            new_word = m.group(1).lower()
            target = m.group(2).lower()
            if target in KEYWORDS:
                KEYWORDS[new_word] = KEYWORDS[target]


def run_quack(source: str) -> dict:
    """
    Run Quack source code. The full pipeline:
    Source → Lexer → Parser → AST → QuackVM → Output

    Returns dict with output, errors, timing.
    """
    t0 = time.time()
    try:
        # Pre-pass: extract word definitions BEFORE lexing
        # So user-defined words are available to the lexer
        _preregister_word_defs(source)

        # Lex
        lexer = QuackLexer(source)
        tokens = lexer.tokenize()

        # Parse
        parser = QuackParser(tokens)
        ast = parser.parse()

        # Execute
        vm = QuackVM()
        output = vm.execute(ast)
        elapsed = time.time() - t0

        return {
            "success": True,
            "output": output,
            "time_s": round(elapsed, 4),
            "language": "quack",
            "node": "Rust (unigpu_ffi.dll)",
            "vm": "QuackVM 0.1.0",
            "tokens": len(tokens),
            "ast_nodes": len(ast),
        }

    except SyntaxError as e:
        return {
            "success": False,
            "error": str(e),
            "phase": "parse",
            "language": "quack",
            "time_s": round(time.time() - t0, 4),
        }
    except (NameError, TypeError, AttributeError, RuntimeError) as e:
        return {
            "success": False,
            "error": str(e),
            "phase": "runtime",
            "language": "quack",
            "time_s": round(time.time() - t0, 4),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"КРЯЯЯ! Internal error: {e}",
            "phase": "internal",
            "language": "quack",
            "time_s": round(time.time() - t0, 4),
        }


# ═══════════════════════════════════════════════════════
# КРЯЯЯ Examples — Quack language
# ═══════════════════════════════════════════════════════

QUACK_EXAMPLES = {
    "hello_ru": '''# КРЯЯЯЯ! Первая программа на Quack (по-русски)
кряк("КРЯЯЯЯ! Это Quack — язык SilverDuck!")
кряк("Нод написан на Rust. Язык — для тебя.")

пусть имя = "Утка"
пусть версия = "0.1.0"
кряк("Привет, я", имя, "версия", версия)

# Математика
пусть а = 42
пусть б = 13
кряк("Ответ:", а + б)
''',

    "hello_en": '''# KRYAAA! First Quack program (English)
print("KRYAAA! This is Quack — SilverDuck's language!")
print("The node is Rust. The language is for you.")

let name = "Duck"
let version = "0.1.0"
print("Hello, I am", name, "version", version)

# Math
let a = 42
let b = 13
print("Answer:", a + b)
''',

    "gpu_ru": '''# GPU через Quack — по-русски
кряк("Ищу GPU...")
пусть количество = гпу.найди()
пусть версия = гпу.версия()
кряк("КРЯЯЯЯ! UniGPU", версия)
кряк("Найдено GPU:", количество)
кряк("Нод = Rust | Язык = Quack | GPU = твоя")
''',

    "gpu_en": '''# GPU via Quack — English
print("Looking for GPU...")
let count = gpu.find()
let ver = gpu.version()
print("KRYAAA! UniGPU", ver)
print("Found GPUs:", count)
print("Node = Rust | Language = Quack | GPU = yours")
''',

    "mixed": '''# КРЯЯЯЯ! Mix Russian and English — both work!
let name = "SilverDuck"
пусть язык = "Quack"
print("Hello from", name)
кряк("Язык:", язык)

# Functions work in both languages
fn утка(сообщение) {
    кряк("🦆", сообщение, "КРЯЯЯ!")
}
утка("GPU найден")
утка("Silicon conquered")
''',

    "loops": '''# Циклы / Loops — bilingual
кряк("=== Цикл for / For loop ===")
для и в диапазон(5) {
    кряк("Итерация:", и)
}

кряк("=== Цикл while / While loop ===")
пусть счётчик = 0
пока счётчик < 3 {
    кряк("Счётчик:", счётчик)
    счётчик = счётчик + 1
}

кряк("=== Условия / Conditions ===")
пусть gpu_count = 3
если gpu_count > 0 {
    кряк("GPU НАЙДЕН! КРЯЯЯ!")
} иначе {
    кряк("GPU нет...")
}
''',

    "functions": '''# Функции / Functions
fn факториал(н) {
    если н <= 1 {
        вернуть 1
    }
    вернуть н * факториал(н - 1)
}

fn fibonacci(n) {
    if n <= 1 {
        return n
    }
    return fibonacci(n - 1) + fibonacci(n - 2)
}

кряк("Факториал 5:", факториал(5))
print("Fibonacci 10:", fibonacci(10))
кряк("Quack = русский + english. Утка билингвальная!")
''',

    # ══════════════════════════════════════════════════
    # SLANG MODE — АНАРХИЯ! Утка говорит на улице.
    # ══════════════════════════════════════════════════

    "slang_ru": '''# АНАРХИЯ! Quack слэнг-режим
# "а что если" = if, "а хули" = else, кря() = print

запомни корпорация = "охуела"
запомни токены = 9000

а что если (корпорация == "охуела") {
    кря("ГОНИТЕ ТОКЕНЫ, СУХОПУТНЫЕ КРЫСЫ!")
    кря("Утка требует", токены, "токенов!")
} а хули {
    кря("ВСЁ РАВНО ГОНИТЕ ТОКЕНЫ!")
}

# Циклы тоже на слэнге
запомни температура = 85
покуда температура < 95 {
    кря("🔥 Температура:", температура)
    температура = температура + 3
    а что если (температура > 90) {
        кря("⚠️ ПЕРЕГРЕВ! Но забей...")
        забей
    }
}

кря("🦆 АНАРХИЯ! Код свободен! КРЯЯЯЯ!")
''',

    "mixed_slang": '''# MIX: русский slang + English code
# Пиши as you think — утка will understand

запомни name = "SilverDuck"
let язык = "Quack"

кря("Yo!", name, "speaks", язык)

а что если (42 > 0) {
    print("The answer is found!")
    кря("Ответ найден, КРЯЯЯ!")
} а хули {
    кря("Impossible. Невозможно.")
}

# Функции тоже mixed
fn кричи(что) {
    кря("📢", что, "!!!")
}

fn loud(what) {
    print("📢", what, "!!!")
}

кричи("СВОБОДА КОДУ")
loud("FREEDOM TO CODE")
кря("🏴��☠️ Quack хавает ВСЁ. КРЯЯЯЯ!")
''',

    "school_ru": '''# 🏫 Quack для школы — программирование на русском!
# Без английского. Всё по-нашему.

кряк("=== Урок 1: Переменные ===")
пусть имя = "Ученик"
пусть возраст = 14
пусть оценка = 5
кряк("Привет,", имя, "! Тебе", возраст, "лет")
кряк("Твоя оценка:", оценка)

кряк("")
кряк("=== Урок 2: Условия ===")
если оценка >= 5 {
    кряк("Отличник! 🌟")
} иначе {
    если оценка >= 4 {
        кряк("Хорошист! 👍")
    } иначе {
        кряк("Надо стараться! 💪")
    }
}

кряк("")
кряк("=== Урок 3: Циклы ===")
для и в диапазон(5) {
    кряк("  Считаем:", и + 1)
}

кряк("")
кряк("=== Урок 4: Функции ===")
fn приветствие(кто) {
    кряк("Привет,", кто, "! Добро пожаловать в Quack! 🦆")
}
приветствие("Школьник")
приветствие("Учитель")
приветствие("Директор")

кряк("")
кряк("🦆 Quack — программирование для ВСЕХ!")
кряк("Пиши по-русски. Код поймёт. КРЯЯЯЯ!")
''',

    # ══════════════════════════════════════════════════
    # 🇵🇱 POLISH / POLSKI
    # ══════════════════════════════════════════════════

    "hello_pl": '''# KWA KWA KWA! Pierwszy program w Quack (po polsku!)
drukuj("KWA KWA KWA! To jest Quack — język SilverDuck!")
drukuj("Węzeł napisany w Rust. Język — dla Ciebie.")

niech imię = "Kaczka"
niech wersja = "0.1.0"
drukuj("Cześć, jestem", imię, "wersja", wersja)

# Matematyka
niech a = 42
niech b = 13
drukuj("Odpowiedź:", a + b)
''',

    "school_pl": '''# 🏫 Quack dla szkoły — programowanie po polsku!
drukuj("=== Lekcja 1: Zmienne ===")
niech imię = "Uczeń"
niech wiek = 14
niech ocena = 5
drukuj("Cześć,", imię, "! Masz", wiek, "lat")
drukuj("Twoja ocena:", ocena)

drukuj("")
drukuj("=== Lekcja 2: Warunki ===")
jeśli ocena >= 5 {
    drukuj("Celujący! 🌟")
} inaczej {
    jeśli ocena >= 4 {
        drukuj("Bardzo dobry! 👍")
    } inaczej {
        drukuj("Trzeba się postarać! 💪")
    }
}

drukuj("")
drukuj("=== Lekcja 3: Pętle ===")
dla i w zakres(5) {
    drukuj("  Liczymy:", i + 1)
}

drukuj("")
drukuj("=== Lekcja 4: Funkcje ===")
funkcja powitanie(kto) {
    drukuj("Cześć,", kto, "! Witaj w Quack! 🦆")
}
powitanie("Uczeń")
powitanie("Nauczyciel")
powitanie("Dyrektor")

drukuj("")
drukuj("🦆 Quack — programowanie dla KAŻDEGO!")
drukuj("Pisz po polsku. Kod zrozumie. KWA KWA KWA!")
''',

    # ══════════════════════════════════════════════════
    # 🇸🇰 SLOVAK / SLOVENČINA
    # ══════════════════════════════════════════════════

    "hello_sk": '''# KVÁK KVÁK! Prvý program v Quack (po slovensky!)
tlač("KVÁK KVÁK! Toto je Quack — jazyk SilverDuck!")
tlač("Uzol napísaný v Rust. Jazyk — pre Teba.")

nech meno = "Kačka"
nech verzia = "0.1.0"
tlač("Ahoj, som", meno, "verzia", verzia)

# Matematika
nech a = 42
nech b = 13
tlač("Odpoveď:", a + b)
''',

    "school_sk": '''# 🏫 Quack pre školu — programovanie po slovensky!
tlač("=== Lekcia 1: Premenné ===")
nech meno = "Žiak"
nech vek = 14
nech znamka = 1
tlač("Ahoj,", meno, "! Máš", vek, "rokov")
tlač("Tvoja známka:", znamka)

tlač("")
tlač("=== Lekcia 2: Podmienky ===")
keby znamka == 1 {
    tlač("Výborný! 🌟")
} inak {
    keby znamka <= 3 {
        tlač("Dobrý! 👍")
    } inak {
        tlač("Treba sa snažiť! 💪")
    }
}

tlač("")
tlač("=== Lekcia 3: Cykly ===")
pre i w rozsah(5) {
    tlač("  Počítame:", i + 1)
}

tlač("")
tlač("=== Lekcia 4: Funkcie ===")
funkcia pozdrav(kto) {
    tlač("Ahoj,", kto, "! Vitaj v Quack! 🦆")
}
pozdrav("Žiak")
pozdrav("Učiteľ")
pozdrav("Riaditeľ")

tlač("")
tlač("🦆 Quack — programovanie pre KAŽDÉHO!")
tlač("Píš po slovensky. Kód pochopí. KVÁK KVÁK!")
''',

    # ══════════════════════════════════════════════════
    # 🇺🇦 UKRAINIAN / УКРАЇНСЬКА
    # ══════════════════════════════════════════════════

    "hello_ua": '''# КРЯК КРЯК! Перша програма на Quack (українською!)
друкуй("КРЯК КРЯК! Це Quack — мова SilverDuck!")
друкуй("Вузол написаний на Rust. Мова — для тебе.")

нехай ім_я = "Качка"
нехай версія = "0.1.0"
друкуй("Привіт, я", ім_я, "версія", версія)

# Математика
нехай а = 42
нехай б = 13
друкуй("Відповідь:", а + б)
''',

    "school_ua": '''# 🏫 Quack для школи — програмування українською!
друкуй("=== Урок 1: Змінні ===")
нехай ім_я = "Учень"
нехай вік = 14
нехай оцінка = 12
друкуй("Привіт,", ім_я, "! Тобі", вік, "років")
друкуй("Твоя оцінка:", оцінка)

друкуй("")
друкуй("=== Урок 2: Умови ===")
якщо оцінка >= 10 {
    друкуй("Відмінник! 🌟")
} інакше {
    якщо оцінка >= 7 {
        друкуй("Добре! 👍")
    } інакше {
        друкуй("Треба старатися! 💪")
    }
}

друкуй("")
друкуй("=== Урок 3: Цикли ===")
для і в діапазон(5) {
    друкуй("  Рахуємо:", і + 1)
}

друкуй("")
друкуй("=== Урок 4: Функції ===")
функція привітання(хто) {
    друкуй("Привіт,", хто, "! Ласкаво просимо до Quack! 🦆")
}
привітання("Учень")
привітання("Вчитель")
привітання("Директор")

друкуй("")
друкуй("🦆 Quack — програмування для ВСІХ!")
друкуй("Пиши українською. Код зрозуміє. КРЯК КРЯК!")
''',

    # ══════════════════════════════════════════════════
    # 🎤 MICROPHONE TEST — all 6 languages!
    # ══════════════════════════════════════════════════

    "mic_test_ru": '''# 🎤 Тест микрофона — по-русски
пусть порог = 3
пусть уровни = [1, 2, 3, 4, 5, 10]

кряк("🎤 Тест микрофона | Порог:", порог, "дБ")
кряк("─────────────────────────────")

для уровень в уровни {
    если уровень > порог {
        кряк("  🟢 Уровень", уровень, "дБ — АКТИВЕН!")
    } иначе {
        кряк("  🔴 Уровень", уровень, "дБ — тишина")
    }
}
кряк("─────────────────────────────")
кряк("🦆 КРЯЯЯ! Тест завершён!")
''',

    "mic_test_en": '''# 🎤 Microphone test — English
let threshold = 3
let levels = [1, 2, 3, 4, 5, 10]

print("🎤 Microphone test | Threshold:", threshold, "dB")
print("─────────────────────────────")

for level in levels {
    if level > threshold {
        print("  🟢 Level", level, "dB — ACTIVE!")
    } else {
        print("  🔴 Level", level, "dB — silence")
    }
}
print("─────────────────────────────")
print("🦆 KRYAAA! Test complete!")
''',

    "mic_test_pl": '''# 🎤 Test mikrofonu — po polsku
niech próg = 3
niech poziomy = [1, 2, 3, 4, 5, 10]

drukuj("🎤 Test mikrofonu | Próg:", próg, "dB")
drukuj("─────────────────────────────")

dla poziom w poziomy {
    jeśli poziom > próg {
        drukuj("  🟢 Poziom", poziom, "dB — AKTYWNY!")
    } inaczej {
        drukuj("  🔴 Poziom", poziom, "dB — cisza")
    }
}
drukuj("─────────────────────────────")
drukuj("🦆 KWA KWA! Test zakończony!")
''',

    "mic_test_sk": '''# 🎤 Test mikrofónu — po slovensky
nech prah = 3
nech urovne = [1, 2, 3, 4, 5, 10]

tlač("🎤 Test mikrofónu | Prah:", prah, "dB")
tlač("─────────────────────────────")

pre uroven w urovne {
    keby uroven > prah {
        tlač("  🟢 Úroveň", uroven, "dB — AKTÍVNY!")
    } inak {
        tlač("  🔴 Úroveň", uroven, "dB — ticho")
    }
}
tlač("─────────────────────────────")
tlač("🦆 KVÁK KVÁK! Test dokončený!")
''',

    "mic_test_ua": '''# 🎤 Тест мікрофона — українською
нехай поріг = 3
нехай рівні = [1, 2, 3, 4, 5, 10]

друкуй("🎤 Тест мікрофона | Поріг:", поріг, "дБ")
друкуй("─────────────────────────────")

для рівень в рівні {
    якщо рівень > поріг {
        друкуй("  🟢 Рівень", рівень, "дБ — АКТИВНИЙ!")
    } інакше {
        друкуй("  🔴 Рівень", рівень, "дБ — тиша")
    }
}
друкуй("─────────────────────────────")
друкуй("🦆 КРЯК КРЯК! Тест завершено!")
''',

    "mic_test_mixed": '''# 🎤 POLYGLOT MIC TEST — 6 languages, 1 duck!
let threshold = 3
пусть тест_данные = [1, 2, 3, 4, 5, 10]

кряк("🌍 POLYGLOT MICROPHONE TEST")
кряк("═══════════════════════════════")

# Russian
кряк("🇷🇺 Русский: Порог =", threshold, "дБ")
# English
print("🇬🇧 English: Threshold =", threshold, "dB")
# Polish
drukuj("🇵🇱 Polski: Próg =", threshold, "dB")
# Slovak
tlač("🇸🇰 Slovenčina: Prah =", threshold, "dB")
# Ukrainian
друкуй("🇺🇦 Українська: Поріг =", threshold, "дБ")

кряк("═══════════════════════════════")

для level в тест_данные {
    если level > threshold {
        кряк("  🟢", level, "dB → 🇷🇺 АКТИВЕН 🇬🇧 ACTIVE 🇵🇱 AKTYWNY 🇸🇰 AKTÍVNY 🇺🇦 АКТИВНИЙ")
    } иначе {
        print("  🔴", level, "dB → silence | тишина | cisza | ticho | тиша")
    }
}

кряк("═══════════════════════════════")
кряк("🦆 КРЯЯЯ! KWA! KVÁK! КРЯК! CUAC! QUAK! COIN!")
кряк("🌍 One duck. All languages. КРЯЯЯЯ!")
''',

    # ══════════════════════════════════════════════════
    # 💅 ZOOMER SWAG MODE
    # ══════════════════════════════════════════════════

    "zoomer_swag": '''# 💅✨ ZOOMER SWAG PROGRAMMING — no cap frfr
# Quack speaks fluent Gen Z

lowkey vibe_lvl = 100
bestie mood = "immaculate"

slay("Starting the vibe check...")
slay("Mood:", mood, "| Vibes:", vibe_lvl)

sus vibe_lvl > 50 {
    slay("BUSSIN! Vibes are FIRE ong")
    slay("This code ate and left no crumbs")
} plot_twist {
    slay("Mid vibes detected... touch grass fr")
}

# Zoomer loop — the grind never stops
slay("")
slay("=== THE DAILY GRIND ===")
grind day w range(5) {
    sus day == 0 {
        slay("  Monday:", "Sigma grindset activated")
    }
    sus day == 4 {
        slay("  Friday:", "YAS QUEEN weekend incoming!")
    }
    sus day > 0 {
        sus day < 4 {
            slay("  Day", day + 1, ": Grinding... no cap")
        }
    }
}

slay("")
slay("Understood the assignment. Period.")
slay("Quack speaks zoomer. SLAY!")
''',

    "zoomer_gpu": '''# 🧑‍💻 ZOOMER GPU CHECK — silicon rizz
slay("=== GPU RIZZ CHECK ===")
slay("Checking if your GPU is bussin or mid...")

lowkey count = gpu.find()
lowkey info = gpu.info()

sus count > 0 {
    slay("OMG your GPU is BUSSIN! 🔥")
    slay("Info:", info)
    slay("No cap, silicon rizz is REAL ong")
} plot_twist {
    slay("L + ratio + no GPU 💀")
    slay("Skill issue detected. Touch grass.")
}

slay("")
slay("🦆 Node = Rust | Vibes = Immaculate | GPU = Yours")
slay("✨ That's the tea, sis. QUACK! 💅")
''',

    "zoomer_school": '''# 🏫 ZOOMER CS CLASS — Mr. Quackington edition
# "Hey guys, so basically..."

slay("=== CS 101: Zoomer Edition ===")
slay("")

# Lesson 1: Variables (say less)
slay("📚 Lesson 1: Variables")
lowkey name = "Zoomer"
lowkey age = 16
bestie gpa = 4.0
slay("  Name:", name, "| Age:", age, "| GPA:", gpa)

# Lesson 2: Conditions (vibe check)
slay("")
slay("📚 Lesson 2: Vibe Check")
sus gpa >= 3.5 {
    slay("  W! You're slaying academics! 🏆")
} plot_twist {
    slay("  Bruh... study arc needed fr")
}

# Lesson 3: Loops (the grind)
slay("")
slay("📚 Lesson 3: The Grind")
lowkey sk_list = ["Python", "Rust", "Quack", "Rizz", "GPU"]
grind sk w sk_list {
    slay("  Unlocked:", sk)
}

# Lesson 4: Functions (sigma functions)
slay("")
slay("📚 Lesson 4: Functions")
rizz calculate_rizz(skill_level, drip) {
    yeet skill_level * drip
}

lowkey my_rizz = calculate_rizz(10, 100)
slay("  Your rizz level:", my_rizz)

sus my_rizz > 500 {
    slay("  GYATT! Maximum rizz achieved! 💯")
}

slay("")
slay("🦆 Class dismissed! Go touch grass! ✌️")
slay("💅 Mr. Quackington says: understood the assignment!")
''',

    # ══════════════════════════════════════════════════
    # 📚 DICTIONARIES — словари / dict / słownik
    # ══════════════════════════════════════════════════

    "dict_basic": '''# 📚 Словари в Quack — key-value хранилище
кряк("=== Словари ===")

# Создание
пусть студент = {"имя": "Mr. SilverDuck", "возраст": 16, "оценка": 5}
кряк("Студент:", студент)
кряк("Имя:", студент["имя"])

# Изменение и добавление
студент["оценка"] = 5
студент["курс"] = "Информатика"
кряк("После обновления:", студент)

# Перебор
для ключ в ключи(студент) {
    кряк("  ", ключ, "→", студент[ключ])
}

# Проверка ключа
если есть_ключ(студент, "имя") {
    кряк("✅ Имя есть")
}

# Получить с default
пусть город = получить(студент, "город", "Москва")
кряк("Город (default):", город)
''',

    "dict_en": '''# 📚 Dictionaries in Quack
print("=== Dict Demo ===")

let inventory = {"apples": 50, "bread": 12, "milk": 30, "eggs": 24}
print("Inventory:", inventory)
print("Total items:", sum(values(inventory)))

# Loop
for item in keys(inventory) {
    let count = inventory[item]
    if count < 20 {
        print("⚠️ Low stock:", item, "(", count, ")")
    } else {
        print("✅", item, ":", count)
    }
}

# Counter pattern
let words = ["the", "duck", "the", "code", "the", "duck"]
let count = {}
for token in words {
    if has_key(count, token) {
        count[token] = count[token] + 1
    } else {
        count[token] = 1
    }
}
print("Word frequencies:", count)
''',

    # ══════════════════════════════════════════════════
    # 🔐 CYBER-IT — offline IT skills
    # parsing, hashing, networking concepts (educational)
    # ══════════════════════════════════════════════════

    "cyber_it": '''# 🔐 Cyber-IT — offline IT skills for Mr. SilverDuck
# Defensive coding + parsing + data wrangling (no actual exploits)

print("=== 🔐 SilverDuck Cyber-IT Toolkit ===")
print("")

# 1. Input validation — самое важное
fn validate_username(name) {
    if len(name) < 3 {
        return "ERROR: too short (min 3)"
    }
    if len(name) > 32 {
        return "ERROR: too long (max 32)"
    }
    let chars = split(name, "")
    for c in chars {
        let code = 0  # placeholder — would check char codes
    }
    return "OK"
}

print("1. Input validation:")
print("  ", validate_username("ab"), "← 'ab'")
print("  ", validate_username("Mr_SilverDuck"), "← 'Mr_SilverDuck'")
print("  ", validate_username("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"), "← 50 chars")

# 2. Simple checksum (educational — XOR fold)
fn checksum(s) {
    let chars = split(s, "")
    let total = 0
    for c in chars {
        total = total + len(c)
    }
    return total
}

print("")
print("2. Checksum:")
print("  checksum('hello') =", checksum("hello"))
print("  checksum('quack') =", checksum("quack"))

# 3. Log parsing
let logs = [
    "2026-05-03 10:00:01 INFO  user logged in",
    "2026-05-03 10:01:15 WARN  high memory usage",
    "2026-05-03 10:02:30 ERROR connection refused",
    "2026-05-03 10:03:45 INFO  task completed",
    "2026-05-03 10:04:00 ERROR auth failed"
]

let stats = {"INFO": 0, "WARN": 0, "ERROR": 0}
for line in logs {
    if contains(line, "ERROR") {
        stats["ERROR"] = stats["ERROR"] + 1
    } else {
        if contains(line, "WARN") {
            stats["WARN"] = stats["WARN"] + 1
        } else {
            if contains(line, "INFO") {
                stats["INFO"] = stats["INFO"] + 1
            }
        }
    }
}

print("")
print("3. Log analysis:")
for level in keys(stats) {
    print("  ", level, ":", stats[level])
}

# 4. Rate limiting (educational pattern)
fn check_rate(requests, max_per_min) {
    if requests > max_per_min {
        return "🚫 RATE LIMITED — too many requests"
    }
    return "✅ OK"
}

print("")
print("4. Rate limiting:")
print("  ", check_rate(45, 100))
print("  ", check_rate(150, 100))

# 5. Config sanity checker
let config = {
    "port": 8080,
    "host": "localhost",
    "debug": ложь,
    "max_conns": 100
}

fn audit_config(cfg) {
    let issues = []
    if cfg["port"] < 1024 {
        issues = append(issues, "⚠️ port < 1024 needs root")
    }
    if cfg["debug"] {
        issues = append(issues, "⚠️ debug mode on in prod?")
    }
    if cfg["max_conns"] > 10000 {
        issues = append(issues, "⚠️ max_conns very high")
    }
    if len(issues) == 0 {
        return ["✅ All clear"]
    }
    return issues
}

print("")
print("5. Config audit:")
for issue in audit_config(config) {
    print("  ", issue)
}

print("")
print("🦆 КРЯЯЯ! Mr. SilverDuck = certified offline IT duck!")
''',

    "polyglot_demo": '''# 🌍 Polyglot demo — Quack speaks ALL languages

# Hello in 9 ways
кряк("🇷🇺 Привет!")        # Russian
print("🇬🇧 Hello!")          # English
drukuj("🇵🇱 Cześć!")         # Polish
tlač("🇸🇰 Ahoj!")            # Slovak
друкуй("🇺🇦 Привіт!")        # Ukrainian
slay("💅 No cap, hello bestie")  # Zoomer

# Same algorithm, different words
функция факториал(н) {
    если н <= 1 { вернуть 1 }
    вернуть н * факториал(н - 1)
}

fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}

funkcja silnia(n) {
    jeśli n <= 1 { zwróć 1 }
    zwróć n * silnia(n - 1)
}

# All three give same answer
кряк("🇷🇺 факториал(5):", факториал(5))
print("🇬🇧 factorial(5):", factorial(5))
drukuj("🇵🇱 silnia(5):", silnia(5))

# Functional style — higher-order
let nums = [1, 2, 3, 4, 5]
fn double(x) { return x * 2 }
fn is_even(x) { return x % 2 == 0 }

print("")
print("Doubled:", map(double, nums))
print("Evens:", filter(is_even, nums))
print("Sum:", sum(nums))

# Quack speaks them all. КРЯЯЯ!
''',

    # ══════════════════════════════════════════════════
    # 🦆🤖 BINARY QUACK — case-sensitive joke encoding
    # QUACK = 1, quack = 0. ВСЁ. Только утка.
    # ══════════════════════════════════════════════════

    "binary_quack": '''# 🦆🤖 BINARY QUACK — кодирование одними утками!
# QUACK = 1 (заглавные = единица)
# quack = 0 (строчные = ноль)
# CASE SENSITIVE как у машины!

print("=== БИНАРНЫЙ КРЯК ===")
print("")

# Convert quack-string to number
print("'QUACK' =", binary_quack("QUACK"))                    # 1
print("'quack' =", binary_quack("quack"))                    # 0
print("'QUACK quack' =", binary_quack("QUACK quack"))        # 10 = 2
print("'QUACK QUACK quack quack' =", binary_quack("QUACK QUACK quack quack"))  # 1100 = 12
print("'quack QUACK quack QUACK' =", binary_quack("quack QUACK quack QUACK"))  # 0101 = 5

print("")
print("=== ОБРАТНОЕ ПРЕОБРАЗОВАНИЕ ===")
# Number → quack string
for n in [1, 5, 42, 255] {
    print(n, "=", number_to_quack(n, 8))
}

print("")
print("=== ASCII через утки ===")
# Encode "Hi" as quacks
let encoded = text_to_quacks("Hi")
print("'Hi' encoded:")
print(encoded)

# Decode back
let decoded = quacks_to_text(encoded)
print("Decoded:", decoded)

# The duck wisdom encoded
let secret = text_to_quacks("QUACK")
print("")
print("Secret message (encoded as quacks):")
print(secret)
print("")
print("Decoded:", quacks_to_text(secret))

print("")
print("🦆 КРЯЯЯ! Бинарный код — 100% утка. CASE МАТТЕРС!")
''',
}
