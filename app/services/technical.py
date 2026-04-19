import yfinance as yf
import numpy as np

def analyze(kode):
    try:
        hist = yf.Ticker(kode + ".JK").history(period="3mo")

        if hist.empty or len(hist) < 20:
            return 0, "NO DATA"

        # MA20
        hist['MA20'] = hist['Close'].rolling(20).mean()

        # RSI (lebih stabil)
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

        # RSI signal
        if last['RSI'] < 30:
            score += 10
            signal = "BUY"
        elif last['RSI'] > 70:
            score -= 10
            signal = "SELL"

        # Trend MA20
        if last['Close'] > last['MA20']:
            score += 5
        else:
            score -= 5

        return int(score), signal

    except Exception as e:
        print(f"Error analyze {kode}: {e}")
        return 0, "ERROR"