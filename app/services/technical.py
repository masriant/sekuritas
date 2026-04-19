import yfinance as yf
import time

def analyze(kode):
    for i in range(2):  # retry 2x
        try:
            hist = yf.Ticker(kode + ".JK").history(period="3mo")

            # ❗ VALIDASI DATA
            if hist.empty or len(hist) < 20:
                return 0, "NO DATA"

            # MA20
            hist['MA20'] = hist['Close'].rolling(20).mean()

            # RSI
            delta = hist['Close'].diff()

            gain = delta.clip(lower=0).rolling(14).mean()
            loss = -delta.clip(upper=0).rolling(14).mean()

            # hindari division by zero
            rs = gain / loss.replace(0, 1e-10)

            hist['RSI'] = 100 - (100 / (1 + rs))

            last = hist.iloc[-1]

            score = 0
            signal = "HOLD"

            # RSI logic
            if last['RSI'] < 30:
                score += 10
                signal = "BUY"
            elif last['RSI'] > 70:
                score -= 10
                signal = "SELL"

            # MA20 logic
            if last['Close'] > last['MA20']:
                score += 5
            else:
                score -= 5

            return score, signal

        except Exception as e:
            print(f"Error analyze {kode}: {e}")
            time.sleep(1)

    return 0, "ERROR"