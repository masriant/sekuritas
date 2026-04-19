# services/technical.py
import yfinance as yf

def analyze(kode):
    try:
        hist = yf.Ticker(kode + ".JK").history(period="3mo")

        hist['MA20'] = hist['Close'].rolling(20).mean()

        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))

        last = hist.iloc[-1]

        score = 0
        signal = "HOLD"

        if last['RSI'] < 30:
            score += 10
            signal = "BUY"
        elif last['RSI'] > 70:
            score -= 10
            signal = "SELL"

        if last['Close'] > last['MA20']:
            score += 5
        else:
            score -= 5

        return score, signal

    except:
        return 0, "ERROR"