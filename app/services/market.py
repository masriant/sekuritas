# services/market.py
import time
import yfinance as yf

cache = {}
CACHE_TTL = 60  # detik

def get_price(kode):
    now = time.time()

    if kode in cache:
        data, ts = cache[kode]
        if now - ts < CACHE_TTL:
            return data

    try:
        ticker = yf.Ticker(kode + ".JK")
        harga = int(ticker.history(period="1d")['Close'].iloc[-1])
        cache[kode] = (harga, now)
        return harga
    except:
        return 0