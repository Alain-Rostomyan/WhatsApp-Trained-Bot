import re
import pandas as pd
import unicodedata
from datetime import datetime
import regex as re_emoji
import json
from collections import defaultdict

# ======= FILE PATHS =======
input_file = "data/raw/chat_data.txt"
output_file = "data/processed/processed_chat.csv"
number_map_path = "data/raw/number_map.json"

# ======= LOAD PHONE → NAME MAP =======
try:
    with open(number_map_path, "r", encoding="utf-8") as f:
        sender_map = json.load(f)
        print(f"✅ Loaded {len(sender_map)} mapped numbers from {number_map_path}")
except FileNotFoundError:
    print("number_map.json not found. Phone numbers will not be mapped.")
    sender_map = {}

# ======= MESSAGE PATTERNS =======
msg_pattern = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2})[\u202f ]?(AM|PM)? - ([^:]+): (.+)$"
)
system_msg_pattern = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}[\u202f ]?(AM|PM)? - .+$"
)

# ======= CLEANING HELPERS =======
def parse_timestamp(date_str, time_str, am_pm):
    try:
        if am_pm:
            fmt = "%m/%d/%y, %I:%M %p"
            return datetime.strptime(f"{date_str}, {time_str} {am_pm}", fmt)
        else:
            fmt = "%m/%d/%y, %H:%M"
            return datetime.strptime(f"{date_str}, {time_str}", fmt)
    except:
        return None

def clean_text(text):
    text = unicodedata.normalize("NFKC", text).strip()
    text = re.sub(r'@\+?\d{5,}', '', text)  # Remove @numbers
    text = re.sub(r'https?://\S+', '', text)  # Remove URLs
    text = re.sub(r'<This message was edited>', '', text, flags=re.IGNORECASE)  # Remove edit tags
    return text.strip()

def is_only_emoji(text):
    emoji_pattern = re_emoji.compile(r"^\p{Emoji}+$", flags=re_emoji.UNICODE)
    return bool(emoji_pattern.fullmatch(text.strip()))

def is_meaningful_message(message):
    if not message or len(message.strip()) < 3:
        return False
    if "<Media omitted>" in message:
        return False
    if "This message was deleted" in message:
        return False
    if is_only_emoji(message):
        return False
    return True

# ======= TRACK UNMAPPED SENDERS =======
unmapped_senders = defaultdict(int)

# ======= MAIN PARSING =======
messages = []
current_msg = None

with open(input_file, "r", encoding="utf-8") as file:
    for line in file:
        line = line.strip()

        user_msg = msg_pattern.match(line)
        system_msg = system_msg_pattern.match(line)

        if user_msg:
            if current_msg and is_meaningful_message(current_msg["message"]):
                messages.append(current_msg)

            date_str, time_str, am_pm, sender, message = user_msg.groups()
            timestamp = parse_timestamp(date_str, time_str, am_pm)

            sender = clean_text(sender)

            # Track unmapped phone numbers
            if sender.startswith("+") and sender not in sender_map:
                unmapped_senders[sender] += 1

            # Apply name mapping
            sender = sender_map.get(sender, sender)

            current_msg = {
                "timestamp": timestamp,
                "sender": sender,
                "message": clean_text(message)
            }

        elif system_msg:
            if current_msg and is_meaningful_message(current_msg["message"]):
                messages.append(current_msg)
                current_msg = None

        else:
            if current_msg:
                current_msg["message"] += " " + clean_text(line)

# Add final message
if current_msg and is_meaningful_message(current_msg["message"]):
    messages.append(current_msg)

# ======= SAVE OUTPUT =======
df = pd.DataFrame(messages)
df = df.dropna(subset=["timestamp", "sender", "message"])
df.to_csv(output_file, index=False)

print(f"\n✅ Saved {len(df)} cleaned messages to {output_file}")

# ======= UNMAPPED SUMMARY =======
if unmapped_senders:
    print("\nUnmapped phone-number senders detected:")
    for number, count in sorted(unmapped_senders.items(), key=lambda x: -x[1]):
        print(f"  {number}: {count} messages")
else:
    print("\nNo unmapped phone numbers found.")
