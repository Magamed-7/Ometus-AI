import re

SPECIALIZATION_KEYWORDS = {
    "кардиолог": ["сердц", "сердечн", "давлени", "пульс", "аритми", "стенокард", "тахикард"],
    "невролог": ["мигрен", "невр", "поясниц", "онемен", "защемил", "бессонниц", "головокруж"],
    "терапевт": ["температур", "простуд", "кашел", "горло", "насморк", "грипп", "слабост"],
    "офтальмолог": ["глаз", "зрени", "линз", "очк", "близорук"],
    "отоларинголог": ["лор", "ухо", "уш", "гайморит", "слух", "ангин", "нос"],
    "дерматолог": ["кожа", "кожн", "сыпь", "зуд", "родинк", "прыщ", "экзем"],
    "гастроэнтеролог": ["живот", "желуд", "тошнот", "изжог", "кишеч", "печен", "стул"],
    "эндокринолог": ["щитовид", "сахар", "диабет", "гормон", "лишний вес"],
    "уролог": ["почк", "мочев", "мочеиспуск", "простат"],
    "гинеколог": ["беремен", "менструа", "гинеколог"],
    "травматолог": ["перелом", "вывих", "ушиб", "сустав", "колен", "растяжен"],
    "стоматолог": ["зуб", "десн"],
    "педиатр": ["ребенок", "ребенка", "детск", "младенц", "грудничок"],
    "психотерапевт": ["тревог", "депресс", "паническ", "стресс"],
}

SPECIALIZATION_KEYWORDS_TG = {
    "кардиолог": ["дил", "қалб", "фишор", "фишори хун", "набз"],
    "невролог": ["асаб", "мигрен", "хоб намеравад", "сарчархзанӣ"],
    "терапевт": ["таб", "шамол", "сулфа", "гулӯ", "зуком", "бемадорӣ"],
    "офтальмолог": ["чашм", "биноӣ", "айнак"],
    "отоларинголог": ["гӯш", "бинӣ", "шунавоӣ", "гулӯдард"],
    "дерматолог": ["пӯст", "доғ", "хориш", "ҷӯшиш"],
    "гастроэнтеролог": ["шикам", "меъда", "дилбеҳузурӣ", "рӯда", "ҷигар"],
    "эндокринолог": ["сипаршакл", "қанд", "диабет", "гормон"],
    "уролог": ["гурда", "пешоб", "простата"],
    "гинеколог": ["ҳомила", "ҳайз", "занона"],
    "травматолог": ["шикастан", "буғум", "зону", "лат хӯрд"],
    "стоматолог": ["дандон", "милк"],
    "педиатр": ["кӯдак", "бача", "тифл"],
    "психотерапевт": ["ташвиш", "депрессия", "стресс", "воҳима"],
}

SPECIALIZATION_KEYWORDS_EN = {
    "кардиолог": ["heart", "chest pain", "blood pressure", "pulse", "cardio"],
    "невролог": ["migraine", "neuro", "numb", "insomnia", "dizzy"],
    "терапевт": ["fever", "cold", "cough", "throat", "flu", "weakness", "therapist"],
    "офтальмолог": ["eye", "vision", "glasses", "sight"],
    "отоларинголог": ["ear", "nose", "hearing", "sinus", "tonsil"],
    "дерматолог": ["skin", "rash", "itch", "mole", "acne"],
    "гастроэнтеролог": ["stomach", "nausea", "heartburn", "intestin", "liver"],
    "эндокринолог": ["thyroid", "sugar", "diabet", "hormone"],
    "уролог": ["kidney", "urin", "prostate"],
    "гинеколог": ["pregnan", "menstrua", "gynecolog"],
    "травматолог": ["fracture", "sprain", "joint", "knee", "bruise"],
    "стоматолог": ["tooth", "teeth", "dental", "gum"],
    "педиатр": ["child", "kid", "baby", "infant"],
    "психотерапевт": ["anxiety", "depress", "panic", "stress"],
}

KEYWORDS_BY_LANGUAGE = {
    "ru": SPECIALIZATION_KEYWORDS,
    "tg": SPECIALIZATION_KEYWORDS_TG,
    "en": SPECIALIZATION_KEYWORDS_EN,
}

SPECIALIST_HIERARCHY = {
    "кардиолог": ["терапевт", "кардиохирург"],
    "невролог": ["терапевт"],
    "терапевт": ["кардиолог", "невролог"],
    "отоларинголог": ["терапевт"],
    "офтальмолог": ["терапевт"],
    "дерматолог": ["терапевт"],
    "гастроэнтеролог": ["терапевт"],
    "эндокринолог": ["терапевт"],
    "уролог": ["терапевт"],
    "гинеколог": ["акушер", "терапевт"],
    "акушер": ["гинеколог", "терапевт"],
    "травматолог": ["терапевт"],
    "стоматолог": ["терапевт"],
    "педиатр": ["терапевт"],
    "психотерапевт": ["терапевт"],
}


def normalize(text: str):
    return text.lower().replace("ё", "е")


def contains_keyword(normalized: str, keyword: str, language: str):
    if language != "en":
        return keyword in normalized

    return re.search(rf"\b{re.escape(keyword)}", normalized) is not None


def match_specializations(text: str, language: str = "ru"):
    normalized = normalize(text)
    keywords_map = KEYWORDS_BY_LANGUAGE.get(language, SPECIALIZATION_KEYWORDS)
    matched = []

    for specialization, keywords in keywords_map.items():
        if specialization in normalized or any(
            contains_keyword(normalized, keyword, language) for keyword in keywords
        ):
            matched.append(specialization)

    return matched


def detect_specialization(text: str):
    matched = match_specializations(text)

    if len(matched) == 1:
        return matched[0]

    return None


def find_fallback_specialists(requested: str):
    return SPECIALIST_HIERARCHY.get(normalize(requested), [])
