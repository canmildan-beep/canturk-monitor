def normalize(text):
    if not text:
        return ""
    # Turkce noktali/noktasiz I sorununu basitce coz, sonra kucult.
    t = text.replace("İ", "i").replace("I", "i")
    return t.casefold()


def find_match(text, keywords):
    """Mesajda gecen ilk aktif anahtar kelimeyi dondurur, yoksa None."""
    norm = normalize(text)
    for kw in keywords:
        nkw = normalize(kw)
        if nkw and nkw in norm:
            return kw
    return None
