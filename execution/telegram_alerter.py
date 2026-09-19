import json
import os
import requests
from datetime import datetime, timedelta
from groq import Groq

# 2026 NSE Holidays (Format: YYYY-MM-DD)
HOLIDAYS_2026 = {
    '2026-01-26', '2026-03-03', '2026-03-26', '2026-03-31',
    '2026-04-03', '2026-04-14', '2026-05-01', '2026-05-28',
    '2026-06-26', '2026-09-14', '2026-10-02', '2026-10-20',
    '2026-11-10', '2026-11-24', '2026-12-25'
}

def is_business_day(date_obj):
    if date_obj.weekday() >= 5: # 5=Sat, 6=Sun
        return False
    if date_obj.strftime('%Y-%m-%d') in HOLIDAYS_2026:
        return False
    return True

def get_next_business_day(date_obj, add_days=1):
    current = date_obj
    added = 0
    while added < add_days:
        current += timedelta(days=1)
        if is_business_day(current):
            added += 1
    return current

def main():
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ipo_data.json')
    if not os.path.exists(json_path):
        print("No ipo_data.json found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Calculate current date in IST (+5:30) because the server runs in UTC
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    today = ist_now.date()
    today_str = today.strftime('%Y-%m-%d')

    open_ipos = []
    for ipo in data:
        # Strict Date Filter: Open Date <= Today <= Close Date
        if ipo.get('Open_Date') != '-' and ipo.get('Close_Date') != '-':
            o_date = datetime.strptime(ipo['Open_Date'], '%Y-%m-%d').date()
            c_date = datetime.strptime(ipo['Close_Date'], '%Y-%m-%d').date()
            if o_date <= today <= c_date:
                # Add computed business days
                ipo['c_date_obj'] = c_date
                ipo['t1_date'] = get_next_business_day(c_date, 1)
                ipo['t2_date'] = get_next_business_day(c_date, 2)
                open_ipos.append(ipo)

    # If no open IPOs, we can stop here or alert that nothing is open
    if not open_ipos:
        print("No active IPOs open today.")
        return

    # Check for Capital Blocking Overlap
    # Two IPOs clash if IPO B closes on or before Day T+1 of IPO A
    # Since any overlapping capital means we must pick one, let's treat all open IPOs that overlap as a single "clash group"
    is_clash = False
    if len(open_ipos) > 1:
        # A simple overlap check: sort by close date, see if next IPO closes <= T+1 of current
        open_ipos.sort(key=lambda x: x['c_date_obj'])
        for i in range(len(open_ipos) - 1):
            if open_ipos[i+1]['c_date_obj'] <= open_ipos[i]['t1_date']:
                is_clash = True
                break

    qualified_ipos = []
    for ipo in open_ipos:
        gain = ipo.get('Expected_Gain_Pct', 0.0)
        # Thresholds
        if is_clash and gain >= 20.0:
            qualified_ipos.append(ipo)
        elif not is_clash and gain >= 25.0:
            qualified_ipos.append(ipo)

    # Rank qualified IPOs
    if qualified_ipos:
        # Primary: Issue Size (Desc), Secondary: Retail Sub (Asc)
        qualified_ipos.sort(key=lambda x: (x.get('Issue_Size_Cr', 0), -x.get('Retail_Sub', 0)), reverse=True)
        top_pick = qualified_ipos[0]
        status = "VALID"
    else:
        top_pick = None
        status = "INVALID"

    # Construct Groq Prompt
    system_prompt = f"""You are an institutional Indian Stock Market IPO evaluation agent.
Your job is to write a short Telegram reasoning section in "Tenglish" (Telugu spelled in English, e.g. "Ee IPO lo GMP bagundi...").
Do not write in English, and do not write in Telugu script. ONLY Tenglish.

Status: {status}
Clash Existed: {is_clash}
Open IPOs today: {json.dumps([{k: v for k,v in ipo.items() if k not in ['c_date_obj', 't1_date', 't2_date']} for ipo in open_ipos], indent=2)}
Qualified Top Pick: {json.dumps({k: v for k,v in top_pick.items() if k not in ['c_date_obj', 't1_date', 't2_date']} if top_pick else None, indent=2)}

If Status is VALID, explain why we selected the Top Pick (mentioning GMP, Allotment chances/Issue size, and capital unblock timing). 
If Status is INVALID, directly explain that none of the open IPOs are worth applying for (mentioning weak GMP/loss risk, capital block overlap, and saving capital for next week). Do NOT literally use the word "INVALID" in your response.

IMPORTANT RULES: 
- DO NOT use complex financial jargon like "composite score" or "conviction" or "capital block overlap".
- Write in extremely casual, conversational, everyday Telugu (Tenglish) like you are texting a friend. Use very simple words like "money", "dabbulu", "profit", and "chances".
- Keep sentences short, punchy, and easy to read. Do not write long, complicated paragraphs.
- Logic Rule: If an IPO has a LARGE Issue Size and a LOW Retail Subscription multiplier, this means the chances of getting an allotment are HIGH (not low). Ensure your reasoning reflects this correctly!
- Format your response EXACTLY as bullet points starting with '•'. No extra intro/outro text.
"""
    
    groq_api_key = os.environ.get("GROQ_API_KEY")
    reasoning_tenglish = "• API Key missing, automated reasoning failed."
    
    if groq_api_key:
        try:
            import time
            client = Groq(api_key=groq_api_key)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    completion = client.chat.completions.create(
                        model="groq/compound",
                        messages=[{"role": "user", "content": system_prompt}],
                        temperature=0.7,
                        max_completion_tokens=300
                    )
                    reasoning_tenglish = completion.choices[0].message.content.strip()
                    break # Success, exit retry loop
                except Exception as inner_e:
                    if attempt == max_retries - 1:
                        raise inner_e # Re-raise if all retries failed
                    time.sleep(2) # Wait 2 seconds before retrying
        except Exception as e:
            reasoning_tenglish = f"• Groq API Error: {str(e)}"
            
    # Format Telegram Alert (Convert UTC to IST: +5:30)
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    current_time = ist_now.strftime('%d-%m-%Y %I:%M %p')
    
    if status == "VALID":
        msg = f"🎯 *Hourly IPO Strategy Alert* ({current_time})\n\n"
        msg += f"🏆 *Top Pick:* *{top_pick['Company']}*\n\n"
        msg += f"📊 *Current Qualified Rankings:*\n"
        for idx, q_ipo in enumerate(qualified_ipos):
            msg += f"{idx+1}. *{q_ipo['Company']}* | GMP: {q_ipo['Expected_Gain_Pct']}% | Size: ₹{q_ipo['Issue_Size_Cr']}Cr | Retail: {q_ipo['Retail_Sub']}x\n"
        
        msg += f"\n💡 *Enduku ee IPO select chesam (Reason):*\n"
        msg += reasoning_tenglish
    else:
        msg = f"🎯 *Hourly IPO Strategy Alert* ({current_time})\n\n"
        msg += f"📋 *Currently Open IPOs Status:*\n"
        for ipo in open_ipos:
            msg += f"• *{ipo['Company']}* | GMP: ₹{ipo.get('GMP', 0)} ({ipo['Expected_Gain_Pct']}%) | Size: ₹{ipo['Issue_Size_Cr']}Cr | Total Sub: {ipo['Total_Sub']}x | Retail: {ipo['Retail_Sub']}x -> ❌ Failed (GMP < 20%)\n"
        
        msg += f"\n⚠️ *Conclusion & Reason:*\n"
        msg += f"Present ga apply cheyadaniki ye okka manchi IPO kuda ledu brother. Money safe ga unchandi, apply cheyoddu.\n\n"
        msg += f"💡 *Enduku apply cheyoddu (Reason):*\n"
        msg += reasoning_tenglish

    print(msg)

    # Send to Telegram
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }
        try:
            r = requests.post(url, json=payload)
            if r.status_code != 200:
                print("Failed to send Telegram message:", r.text)
        except Exception as e:
            print(f"Error connecting to Telegram: {e}")

if __name__ == '__main__':
    main()
