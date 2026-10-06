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
    
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    open_ipos = []
    for ipo in data:
        # Strict Date Filter: Open Date <= Today <= Close Date
        if ipo.get('Open_Date') not in ['-', ''] and ipo.get('Close_Date') not in ['-', '']:
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
        ipo_type = ipo.get('IPO_Type', 'Mainboard')
        
        # Thresholds
        if ipo_type == 'SME':
            if gain >= 50.0:
                qualified_ipos.append(ipo)
        else:
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
        msg += f"🏆 *TOP PICK*\n"
        for idx, q_ipo in enumerate(qualified_ipos):
            est_profit = q_ipo.get('Est_Profit_Rs', 0)
            if q_ipo.get('Close_Date') == today_str:
                closing_tag = " [🔥 CLOSING TODAY]"
            elif q_ipo.get('Close_Date') == tomorrow_str:
                closing_tag = " [⏳ CLOSES TOMORROW]"
            else:
                closing_tag = ""
            
            gmp_pct = q_ipo['Expected_Gain_Pct']
            gmp_rs = q_ipo.get('GMP', 0)
            size = q_ipo['Issue_Size_Cr']
            qib = q_ipo.get('QIB_Sub', 0)
            ret = q_ipo['Retail_Sub']
            
            ipo_tag = f" [{q_ipo.get('IPO_Type', 'Mainboard')}]"
            msg += f"🏢 *{q_ipo['Company']}*{ipo_tag}{closing_tag}\n"
            msg += f"  📈 GMP: {gmp_pct}% (₹{gmp_rs})\n"
            msg += f"  💰 Profit: ~₹{est_profit}\n"
            msg += f"  📦 Size: ₹{size}Cr\n"
            msg += f"  🏦 QIB Sub: {qib}x\n"
            msg += f"  👥 Retail Sub: {ret}x\n"
            msg += f"✅ Verdict: APPLY\n\n"
        
        msg += f"💡 *Enduku ee IPO select chesam (Reason):*\n"
        msg += reasoning_tenglish
    else:
        msg = f"🎯 *Hourly IPO Strategy Alert* ({current_time})\n\n"
        if len(open_ipos) == 1:
            msg += f"📋 *CURRENTLY OPEN IPO*\n\n"
        else:
            msg += f"📋 *CURRENTLY OPEN IPOs*\n\n"
            
        for ipo in open_ipos:
            est_profit = ipo.get('Est_Profit_Rs', 0)
            if ipo.get('Close_Date') == today_str:
                closing_tag = " [🔥 CLOSING TODAY]"
            elif ipo.get('Close_Date') == tomorrow_str:
                closing_tag = " [⏳ CLOSES TOMORROW]"
            else:
                closing_tag = ""
                
            gmp_pct = ipo['Expected_Gain_Pct']
            gmp_rs = ipo.get('GMP', 0)
            size = ipo['Issue_Size_Cr']
            qib = ipo.get('QIB_Sub', 0)
            ret = ipo['Retail_Sub']
            ipo_type = ipo.get('IPO_Type', 'Mainboard')
            ipo_tag = f" [{ipo_type}]"
            
            msg += f"🏢 *{ipo['Company']}*{ipo_tag}{closing_tag}\n"
            msg += f"  📈 GMP: {gmp_pct}% (₹{gmp_rs})\n"
            msg += f"  💰 Profit: ~₹{est_profit}\n"
            msg += f"  📦 Size: ₹{size}Cr\n"
            msg += f"  🏦 QIB Sub: {qib}x\n"
            msg += f"  👥 Retail Sub: {ret}x\n"
            
            if ipo_type == 'SME':
                msg += f"❌ Verdict: FAILED (SME GMP < 50%)\n\n"
            else:
                msg += f"❌ Verdict: FAILED (Mainboard GMP too low)\n\n"
        
        msg += f"⚠️ *Conclusion & Reason:*\n"
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

def check_allotments_for_subscribers():
    try:
        from allotment_scraper import KFintechScraper, get_todays_ipos
        from users_db import get_all_users_by_status
        import requests
        
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return
            
        def send_dm(chat_id, text):
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
            
        def send_photo(chat_id, text, photo_path):
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            try:
                with open(photo_path, 'rb') as photo:
                    payload = {"chat_id": chat_id, "caption": text, "parse_mode": "Markdown"}
                    requests.post(url, data=payload, files={"photo": photo})
            except Exception as e:
                print(f"Error sending photo: {e}")
                send_dm(chat_id, text) # Fallback to text

        todays_ipos = get_todays_ipos()
        if not todays_ipos:
            print("No IPOs declaring allotment today.")
            return
            
        print(f"IPOs declaring allotment today: {todays_ipos}")
            
        active_users = get_all_users_by_status('ACTIVE')
        if not active_users:
            print("No active subscribers to check allotments for.")
            return
            
        scraper = KFintechScraper()
        import asyncio
        
        # PRE-CHECK: Fast validation to see if KFintech has actually released the IPO in the dropdown
        # This prevents 500 browsers from spinning up every 5 minutes if the IPO hasn't dropped yet!
        active_kfin = asyncio.run(scraper.get_active_dropdown_ipos())
        
        live_ipos = []
        for target in todays_ipos:
            t_simple = target.lower().replace('limited', '').replace('ltd', '').strip()
            for active in active_kfin:
                a_simple = active.lower().replace('limited', '').replace('ltd', '').strip()
                if t_simple in a_simple or a_simple in t_simple:
                    live_ipos.append(target)
                    break
                    
        if not live_ipos:
            print(f"IPOs {todays_ipos} are declaring today, but are NOT YET live on KFintech. Exiting gracefully.")
            return
            
        print(f"🚨 MATCH FOUND! {live_ipos} are officially LIVE on KFintech! Starting 500-PAN Bulk Scan...")
        
        # We extract all pans to check in bulk asynchronously
        pan_to_chat_id = {user['pan_number']: user['chat_id'] for user in active_users}
        pans_to_check = list(pan_to_chat_id.keys())
        
        print(f"Checking allotments for {len(pans_to_check)} PANs concurrently...")
        bulk_results = asyncio.run(scraper.check_allotments_bulk(pans_to_check, live_ipos))
        
        for pan, allotments in bulk_results.items():
            if allotments:
                chat_id = pan_to_chat_id[pan]
                msg = f"🎉 *ALLOTMENT ALERT* 🎉\n\nYour PAN `{pan}` has been checked!\n\n"
                for allot in allotments:
                    msg += f"🏢 *Company:* {allot['company']}\n"
                    msg += f"✅ *Status:* {allot['allotted']}\n\n"
                msg += "Thank you for being a premium subscriber!"
                
                # Send screenshot if available, otherwise just text
                if 'screenshot' in allotments[0] and allotments[0]['screenshot']:
                    send_photo(chat_id, msg, allotments[0]['screenshot'])
                else:
                    send_dm(chat_id, msg)
                
    except Exception as e:
        print(f"Error checking allotments: {e}")

if __name__ == '__main__':
    main()
    check_allotments_for_subscribers()
