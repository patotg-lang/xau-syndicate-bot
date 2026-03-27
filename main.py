from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID")
WH_SECRET  = os.environ.get("WEBHOOK_SECRET", "")


def format_signal(data: dict) -> str:
    action  = data.get("action", "BUY")
    setup   = data.get("setup", "—")
    symbol  = data.get("symbol", "XAUUSD")
    entry   = float(data.get("entry", 0))
    sl      = float(data.get("sl", 0))
    tp1     = float(data.get("tp1", 0))
    adx     = data.get("adx", "—")
    rsi     = data.get("rsi", "—")
    macro   = data.get("macro", "—")
    vol     = data.get("vol", "—")
    trail   = data.get("trail_atr", "—")

    is_long   = action == "BUY"
    direction = "LONG 🟢" if is_long else "SHORT 🔴"
    risk_pts  = abs(entry - sl)
    tp1_pts   = abs(tp1 - entry)
    rr        = round(tp1_pts / risk_pts, 2) if risk_pts > 0 else "—"

    now = datetime.utcnow().strftime("%d %b %Y  %H:%M UTC")

    return (
        f"⚡ *XAU SYNDICATE v9 — {direction}*\n"
        f"Setup: `{setup}`\n"
        f"\n"
        f"*Entrada:*  `${entry:,.2f}`\n"
        f"*Stop Loss:* `${sl:,.2f}`  (−${risk_pts:.2f})\n"
        f"*TP1 (30%):* `${tp1:,.2f}`  (+${tp1_pts:.2f} · {rr}R)\n"
        f"*Runner:* trailing `{trail}×` ATR adaptativo\n"
        f"\n"
        f"ADX: `{adx}` · RSI: `{rsi}` · Vol: `{vol}`\n"
        f"Macro D1: `{macro}`\n"
        f"\n"
        f"_{now}_"
    )


def send_telegram(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if not r.ok:
            print(f"Telegram error: {r.status_code} — {r.text}")
        return r.ok
    except Exception as e:
        print(f"Telegram exception: {e}")
        return False


@app.route("/webhook", methods=["POST"])
def webhook():
    # Verificación opcional de secreto
    if WH_SECRET:
        secret = request.headers.get("X-Webhook-Secret", "")
        if secret != WH_SECRET:
            return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    print(f"[{datetime.utcnow()}] Señal recibida: {data}")

    msg = format_signal(data)
    ok  = send_telegram(msg)

    return jsonify({"ok": ok, "action": data.get("action"), "setup": data.get("setup")}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bot": "XAU Syndicate v9", "time": datetime.utcnow().isoformat()}), 200


@app.route("/test", methods=["GET"])
def test():
    """Endpoint para probar que el bot manda mensajes a Telegram correctamente."""
    test_data = {
        "symbol": "XAUUSD", "action": "BUY",  "setup": "A+ Long",
        "entry": 3142.50,   "sl": 3128.00,     "tp1": 3171.50,
        "adx": 24,          "rsi": 48,         "macro": "ALCISTA",
        "vol": "normal",    "trail_atr": 2.0
    }
    msg = format_signal(test_data)
    ok  = send_telegram(msg)
    return jsonify({"ok": ok, "message": "Señal de prueba enviada"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
