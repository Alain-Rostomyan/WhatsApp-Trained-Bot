import pandas as pd
import json
import regex as re_emoji
from collections import defaultdict

# ======= FILE PATHS =======
input_csv = "data/processed/processed_chat.csv"
output_jsonl = "data/processed/training_data_multiturn.jsonl"

# ======= CONFIG =======
context_size = 3
min_message_len = 5
max_ratio_per_sender = 0.20  # Max 20% of responses from one sender

# ======= LOAD CHAT =======
df = pd.read_csv(input_csv)
df = df.sort_values("timestamp").reset_index(drop=True)

# ======= HELPERS =======
def is_only_emoji(text):
    pattern = re_emoji.compile(r"^\p{Emoji}+$", flags=re_emoji.UNICODE)
    return bool(pattern.fullmatch(text.strip()))

def is_valid_message(msg):
    msg = str(msg).strip()
    if len(msg) < min_message_len:
        return False
    if not any(c.isalpha() for c in msg):
        return False
    if is_only_emoji(msg):
        return False
    if re_emoji.match(r"^@\+?\d{5,}$", msg):  # Just a phone mention
        return False
    return True

# ======= BUILD EXAMPLES WITH STRATIFICATION =======
pairs = []
reply_counts = defaultdict(int)

# Count total possible responses per user
initial_counts = defaultdict(int)
for i in range(context_size, len(df) - 1):
    response_row = df.iloc[i + 1]
    responder = response_row["sender"]
    if is_valid_message(response_row["message"]):
        initial_counts[responder] += 1

total_possible = sum(initial_counts.values())
max_per_user = {user: int(max_ratio_per_sender * total_possible) for user in initial_counts}

# Second pass to build prompt-response pairs
for i in range(context_size, len(df) - 1):
    context_rows = df.iloc[i - context_size + 1 : i + 1]
    response_row = df.iloc[i + 1]
    responder = response_row["sender"]

    if not all(is_valid_message(row["message"]) for _, row in context_rows.iterrows()):
        continue
    if not is_valid_message(response_row["message"]):
        continue

    if context_rows.iloc[-1]["sender"] == responder:
        continue

    if reply_counts[responder] >= max_per_user[responder]:
        continue

    prompt_lines = [f'{row["sender"]}: {row["message"].strip()}' for _, row in context_rows.iterrows()]
    prompt = "\n".join(prompt_lines).strip()
    response = f'Gurt: {response_row["message"].strip()}'

    pairs.append({
        "prompt": prompt,
        "response": response,
        "source_user": responder
    })

    reply_counts[responder] += 1

# ======= SAVE =======
with open(output_jsonl, "w", encoding="utf-8") as f:
    for pair in pairs:
        json.dump(pair, f, ensure_ascii=False)
        f.write("\n")

print(f"✅ Saved {len(pairs)} stratified prompt-response pairs with `source_user` to {output_jsonl}")
