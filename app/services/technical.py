import yfinance as yf

def analyze(kode):
    try:
        hist = yf.Ticker(kode + ".JK").history(period="3mo")

        # ✅ CEGAH DATA KOSONG
        if hist.empty or len(hist) < 20:
            return 0, "NO DATA"

        # MA20
        hist['MA20'] = hist['Close'].rolling(20).mean()

        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

        # ✅ HINDARI BAGI NOL
        loss = loss.replace(0, 1e-10)

        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))

        last = hist.iloc[-1]

        score = 0
        signal = "HOLD"

        # RSI
        if last['RSI'] < 30:
            score += 10
            signal = "BUY"
        elif last['RSI'] > 70:
            score -= 10
            signal = "SELL"

        # MA20
        if last['Close'] > last['MA20']:
            score += 5
        else:
            score -= 5

        return score, signal

    except Exception as e:
        print(f"Error analyze {kode}: {e}")
        return 0, "ERROR"