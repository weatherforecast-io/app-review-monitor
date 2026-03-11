"""Complete list of App Store and Google Play supported country codes."""

# All App Store / Google Play supported country/region codes (ISO 3166-1 alpha-2)
ALL_COUNTRIES = [
    "ae", "ag", "ai", "al", "am", "ao", "ar", "at", "au", "az",
    "ba", "bb", "bd", "be", "bf", "bg", "bh", "bj", "bm", "bn",
    "bo", "br", "bs", "bt", "bw", "by", "bz",
    "ca", "cd", "cg", "ch", "ci", "cl", "cm", "cn", "co", "cr",
    "cv", "cy", "cz",
    "de", "dk", "dm", "do", "dz",
    "ec", "ee", "eg", "es",
    "fi", "fj", "fm", "fr",
    "ga", "gb", "gd", "ge", "gh", "gm", "gr", "gt", "gw", "gy",
    "hk", "hn", "hr", "hu",
    "id", "ie", "il", "in", "iq", "is", "it",
    "jm", "jo", "jp",
    "ke", "kg", "kh", "kn", "kr", "kw", "ky", "kz",
    "la", "lb", "lc", "lk", "lr", "lt", "lu", "lv",
    "md", "me", "mg", "mk", "ml", "mm", "mn", "mo", "mr", "ms",
    "mt", "mu", "mv", "mw", "mx", "my", "mz",
    "na", "ne", "ng", "ni", "nl", "no", "np", "nz",
    "om",
    "pa", "pe", "pg", "ph", "pk", "pl", "pt", "pw", "py",
    "qa",
    "ro", "rs", "ru", "rw",
    "sa", "sb", "sc", "se", "sg", "si", "sk", "sl", "sn", "sr",
    "st", "sv", "sz",
    "tc", "td", "th", "tj", "tm", "tn", "tr", "tt", "tw", "tz",
    "ua", "ug", "us", "uy", "uz",
    "vc", "ve", "vg", "vn",
    "ye",
    "za", "zm", "zw",
]

# Google Play language code mapping for all countries
COUNTRY_LANG_MAP = {
    "ae": "ar", "ag": "en", "ai": "en", "al": "sq", "am": "hy",
    "ao": "pt", "ar": "es", "at": "de", "au": "en", "az": "az",
    "ba": "bs", "bb": "en", "bd": "bn", "be": "nl", "bf": "fr",
    "bg": "bg", "bh": "ar", "bj": "fr", "bm": "en", "bn": "ms",
    "bo": "es", "br": "pt", "bs": "en", "bt": "en", "bw": "en",
    "by": "be", "bz": "en",
    "ca": "en", "cd": "fr", "cg": "fr", "ch": "de", "ci": "fr",
    "cl": "es", "cm": "fr", "cn": "zh", "co": "es", "cr": "es",
    "cv": "pt", "cy": "el", "cz": "cs",
    "de": "de", "dk": "da", "dm": "en", "do": "es", "dz": "ar",
    "ec": "es", "ee": "et", "eg": "ar", "es": "es",
    "fi": "fi", "fj": "en", "fm": "en", "fr": "fr",
    "ga": "fr", "gb": "en", "gd": "en", "ge": "ka", "gh": "en",
    "gm": "en", "gr": "el", "gt": "es", "gw": "pt", "gy": "en",
    "hk": "zh", "hn": "es", "hr": "hr", "hu": "hu",
    "id": "id", "ie": "en", "il": "he", "in": "en", "iq": "ar",
    "is": "is", "it": "it",
    "jm": "en", "jo": "ar", "jp": "ja",
    "ke": "en", "kg": "ky", "kh": "km", "kn": "en", "kr": "ko",
    "kw": "ar", "ky": "en", "kz": "kk",
    "la": "lo", "lb": "ar", "lc": "en", "lk": "si", "lr": "en",
    "lt": "lt", "lu": "fr", "lv": "lv",
    "md": "ro", "me": "sr", "mg": "fr", "mk": "mk", "ml": "fr",
    "mm": "my", "mn": "mn", "mo": "zh", "mr": "ar", "ms": "en",
    "mt": "mt", "mu": "en", "mv": "en", "mw": "en", "mx": "es",
    "my": "ms", "mz": "pt",
    "na": "en", "ne": "fr", "ng": "en", "ni": "es", "nl": "nl",
    "no": "no", "np": "ne", "nz": "en",
    "om": "ar",
    "pa": "es", "pe": "es", "pg": "en", "ph": "en", "pk": "ur",
    "pl": "pl", "pt": "pt", "pw": "en", "py": "es",
    "qa": "ar",
    "ro": "ro", "rs": "sr", "ru": "ru", "rw": "en",
    "sa": "ar", "sb": "en", "sc": "en", "se": "sv", "sg": "en",
    "si": "sl", "sk": "sk", "sl": "en", "sn": "fr", "sr": "nl",
    "st": "pt", "sv": "es", "sz": "en",
    "tc": "en", "td": "fr", "th": "th", "tj": "tg", "tm": "tk",
    "tn": "ar", "tr": "tr", "tt": "en", "tw": "zh", "tz": "en",
    "ua": "uk", "ug": "en", "us": "en", "uy": "es", "uz": "uz",
    "vc": "en", "ve": "es", "vg": "en", "vn": "vi",
    "ye": "ar",
    "za": "en", "zm": "en", "zw": "en",
}


def resolve_countries(countries_env: str) -> list[str]:
    """Resolve country codes from environment variable.

    Supports 'all' to use all available countries, or comma-separated codes.
    """
    value = countries_env.strip().lower()
    if value == "all":
        return list(ALL_COUNTRIES)
    return [x.strip() for x in value.split(",") if x.strip()]
