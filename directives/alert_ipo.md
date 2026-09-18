# Directive: Evaluate & Alert IPOs via Telegram

**Goal:** Evaluate currently open IPOs using SEBI T+3 rules and generate a Telegram alert with reasoning provided by Groq in simple Tenglish.

**Inputs:**
- `ipo_data.json`
- `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

**Tools / Scripts to Use:**
- `execution/telegram_alerter.py`

**Rules & Edge Cases:**
1. **Date Filter:** Only consider IPOs where `Open_Date <= Today <= Close_Date`.
2. **Business Day Logic (T+3):** 
   - Day T: Close Date
   - Day T+1: Basis of Allotment
   - Day T+2: Refund / Unblock
   - Must skip weekends and 2026 NSE Holidays.
3. **Capital Overlap Clash:** If IPO B closes on or before Day T+1 of IPO A, their capital is mutually exclusive. Pick only the single best candidate from the clashing set.
4. **Evaluation Logic:**
   - Standalone IPO (no clash): Requires Expected Gain % >= 25% to qualify.
   - Clashing IPOs: Requires Expected Gain % >= 20%. Rank by larger Issue Size (₹ Cr) first, then lower Retail Sub.
5. **Groq Reasoning (Tenglish):** The reasoning section must be written in simple, casual Tenglish (Telugu spelled in English). It must explain the GMP margin, allotment chances, and capital block timing.
6. **Output Format:** The output must precisely follow the defined Telegram Markdown format (either "Valid Best IPO Exists" or "No Good IPO to Apply").
