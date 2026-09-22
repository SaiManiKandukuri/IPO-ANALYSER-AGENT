import json
import os
import requests
from datetime import datetime, timedelta, timezone

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

def generate_tenglish_reasoning(status, top_pick, is_clash, num_open_ipos):
    if status == "INVALID":
        if is_clash:
            return "• Ee roju open unna IPOs ki apply cheyakudadhu. Endukante, multiple IPOs okesari open unnai. Okavela vatiki apply chesthe, mee dabbulu (funds) ekkuva rojulapatu block aypothayi. Ippudu risk theeskuni funds block cheskovadam kante, next week oche manchi IPOs kosam money save cheskovadam chala better. So, ivanni skip cheseyandi."
        else:
            if num_open_ipos == 1:
                return "• Present ga open unna ee okka IPO lo kooda manchi GMP (Grey Market Premium) ledu. GMP thakkuva undi ante, listing roju profit oche chances chala thakkuva, sometimes loss kuda ravochu. Dabbulu waste cheskokunda, safe ga undandi. Ee IPO ni skip cheseyandi."
            else:
                return "• Present ga open unna ye IPO lo kooda manchi GMP (Grey Market Premium) ledu. GMP thakkuva undi ante, listing roju profit oche chances chala thakkuva, sometimes loss kuda ravochu. Dabbulu waste cheskokunda, safe ga undandi. Ee IPOs anni skip cheseyandi."
    else:
        # VALID Top Pick
        comp = top_pick.get('Company', 'Ee')
        gmp = top_pick.get('Expected_Gain_Pct', 0.0)
        
        # Safely parse size and retail sub, defaulting to 0 if '-'
        try:
            size_str = str(top_pick.get('Issue_Size_Cr', '0')).replace(',', '')
            size = float(size_str) if size_str != '-' else 0.0
        except ValueError:
            size = 0.0
            
        try:
            ret_str = str(top_pick.get('Retail_Sub', '0')).replace(',', '')
            ret_sub = float(ret_str) if ret_str != '-' else 0.0
        except ValueError:
            ret_sub = 0.0
            
        c_date = top_pick.get('Close_Date', '')

        p1 = f"• *{comp}* IPO lo apply cheyadaniki main reason enti ante, deeni GMP chala strong ga {gmp}% undi. Ante listing roju manchi profit expect cheyochu."
        
        if size >= 100.0 and ret_sub < 30.0:
            p2 = f"• Inko plus point enti ante, ee IPO issue size peddadi (₹{size}Cr), mariyu retail quota inka {ret_sub}x mathrame subscribe ayindi. Kabatti manaku allotment oche chances chala ekkuva untayi!"
        elif size >= 100.0 and ret_sub >= 30.0:
            p2 = f"• Ee IPO issue size peddadi (₹{size}Cr) aina kooda, retail quota already {ret_sub}x heavy ga subscribe aypoyindi. Allotment chance thakkuva unna, demand heavy ga undi kabatti kachithanga try cheyali!"
        elif size < 100.0 and ret_sub < 30.0:
            p2 = f"• Idi oka chinna IPO (Size: ₹{size}Cr), kani retail quota inka {ret_sub}x mathrame subscribe ayindi. Competition inka peragakamunde apply chesthe allotment chance manchiga untundi!"
        else: # size < 100.0 and ret_sub >= 30.0
            p2 = f"• Ee IPO issue size chala chinnadi (₹{size}Cr), mariyu retail quota already {ret_sub}x chala heavy ga subscribe ayindi. Allotment oche chance chala thakkuva unna kooda, list ayithe mathram super profits isthundi kabatti try cheyali."
        
        p3 = f"• Ee IPO close date {c_date}. Meeru ippudu apply chesthe, allotment tarvata just 2-3 working days lo mee capital unblock aypothundi. So, mee money ekkuva rojulapatu stuck aypodu."
        
        return f"{p1}\n{p2}\n{p3}"

def main():
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ipo_data.json')
    if not os.path.exists(json_path):
        print("No ipo_data.json found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Calculate current date in IST (+5:30) because the server runs in UTC
    utc_now = datetime.now(timezone.utc)
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

    # Generate deterministic Tenglish reasoning
    reasoning_tenglish = generate_tenglish_reasoning(status, top_pick, is_clash, len(open_ipos))
            
    # Format Telegram Alert (Convert UTC to IST: +5:30)
    utc_now = datetime.now(timezone.utc)
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
        if len(open_ipos) == 1:
            msg += f"📋 *Currently Open IPO Status:*\n"
        else:
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
                print("Failed to send Telegram message with Markdown:", r.text)
                # Fallback: The failure is almost certainly due to Telegram's strict Markdown parser choking on 
                # a stray '_' or '*' in the AI text or API error string. Retry without Markdown.
                print("Retrying Telegram send without Markdown formatting...")
                payload.pop("parse_mode", None)
                r2 = requests.post(url, json=payload)
                if r2.status_code != 200:
                    print("Failed to send Telegram message completely:", r2.text)
                else:
                    print("Successfully sent Telegram message using plaintext fallback.")
            else:
                print("Successfully sent Telegram message.")
        except Exception as e:
            print(f"Error connecting to Telegram: {e}")

if __name__ == '__main__':
    main()
