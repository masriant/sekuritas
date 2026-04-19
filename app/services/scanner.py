# services/scanner.py
SAHAM_LIST = [
    "BBRI", "BBCA", "TLKM", "ASII", "BMRI",
    "UNVR", "ICBP", "ADRO", "PGAS"
]


# services/scanner.py
from services.market import get_price
from services.technical import analyze

def scan_market():
    results = []

    for kode in SAHAM_LIST:
        harga = get_price(kode)
        score, signal = analyze(kode)

        results.append({
            "kode": kode,
            "harga": harga,
            "score": score,
            "signal": signal
        })

    return sorted(results, key=lambda x: x['score'], reverse=True)