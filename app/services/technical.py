# services/technical.py
import yfinance as yf
import numpy as np

def analyze(kode):
    try:
        hist = yf.Ticker(kode + ".JK").history(period="3mo")

        if hist.empty or len(hist) < 30:
            return 0, "NO DATA"

        # MA20 & MA50
        hist['MA20'] = hist['Close'].rolling(20).mean()
        hist['MA50'] = hist['Close'].rolling(50).mean()

        # RSI
        delta = hist['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        hist['RSI'] = 100 - (100 / (1 + rs))

        last = hist.iloc[-1]

        if np.isnan(last['RSI']) or np.isnan(last['MA20']):
            return 0, "INVALID DATA"

        score = 0
        signal = "HOLD"

        # ========================
        # 🔥 RSI + TREND COMBINATION
        # ========================

        # BUY kuat
        if last['RSI'] < 30 and last['Close'] > last['MA20']:
            score += 15
            signal = "STRONG BUY"

        # BUY biasa
        elif last['RSI'] < 30:
            score += 8
            signal = "BUY"

        # SELL kuat
        elif last['RSI'] > 70 and last['Close'] < last['MA20']:
            score -= 15
            signal = "STRONG SELL"

        # SELL biasa
        elif last['RSI'] > 70:
            score -= 8
            signal = "SELL"

        # ========================
        # 📈 TREND FILTER
        # ========================

        if last['Close'] > last['MA20']:
            score += 5
        else:
            score -= 5

        # trend besar
        if not np.isnan(last['MA50']):
            if last['MA20'] > last['MA50']:
                score += 5
            else:
                score -= 5

        return int(score), signal

    except Exception as e:
        print(f"Error analyze {kode}: {e}")
        return 0, "ERROR"