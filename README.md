# WhatsApp Trained Bot

**Gurt**, a custom-trained AI bot, writes in WhatsApp DMs/group chats to talk like the members.

This project fine-tunes a Mistral language model on real chat history, hosts it via Flask in Google Colab, and integrates with WhatsApp using `whatsapp-web.js`.

---

## 🧠 Features

- 🔁 Fine-tuned on real WhatsApp chat history
- 💬 Responds in DMs or chats via WhatsApp Web
- 🧠 Remembers recent messages for better context (sliding window memory)
- 📝 Logs all interactions to a local file (`logs.jsonl`)
- ☁️ Hosted in Colab via Flask + ngrok
- 🔧 Fully customizable behavior (name-calling requirement, filters, personality)
- 📚 Retrieval-Augmented Generation (RAG) for knowledge-grounded replies

---

## 🗂 Project Structure
```
WhatsApp Trained Bot/
├── data/                             # (gitignored) all data excluded
│   ├── processed/
│   │   ├── processed_chat.csv        # (gitignored) structured message data
│   │   └── training_data_multiturn.jsonl  # (gitignored) prompt/response pairs
│   └── raw/
│       ├── groupchat.txt             # (gitignored) WhatsApp export
│       └── number_map.json           # (gitignored) phone-to-name mapping
│
├── data_preparation/                 # Scripts for data cleaning and formatting
│   ├── preprocess_chat.py            # Cleans and maps chat exports
│   └── generate_prompt_responses_multiturn.py  # Builds multi-turn training sets
│
├── knowledge/                        # Small text files for RAG context
│   └── knowledge.txt
├── model_hosting/                    # Hosts fine-tuned model using Flask
│   ├── host_model.ipynb
│   ├── rag_retriever.py              # Simple TF-IDF retriever
│   └── rag_server.py                 # Example Flask server with RAG
│
├── model_training/                   # Fine-tuning setup for LoRA training
│   └── train_model.ipynb
│
├── whatsapp-bot/                     # WhatsApp bot using Node.js and whatsapp-web.js
│   ├── bot.js                        # Handles message parsing and API reply
│   ├── package.json
│   ├── package-lock.json             # (gitignored) optionally excluded for consistency
│   ├── logs.jsonl                    # (gitignored) logs of messages handled by Gurt
│   ├── .env                          # (gitignored) contains secrets and API keys
│   ├── .wwebjs_auth/                 # (gitignored) WhatsApp session data
│   ├── .wwebjs_cache/                # (gitignored) WhatsApp cache files
│   └── node_modules/                 # (gitignored) installed dependencies
│
├── .env.example                      # Public-safe .env template for setup
├── .gitignore                        # Specifies all ignored files and folders
└── README.md                         # Documentation and usage instructions
```

---

## 🚀 How It Works

1. **Train** a LoRA-adapted Mistral model on chat data (done in Colab)
2. **Serve** the model via Flask + ngrok in `host_model.ipynb`
3. **Run** the WhatsApp bot via `bot.js` on your local machine
4. **Interact** with Gurt in DMs or groups

---

## 🔧 Configuration

- **Memory size**: Set in `bot.js` via `MEMORY_LIMIT`
- **Trigger behavior**: Adjust whether Gurt replies to all messages or only when mentioned
- **Logging**: Messages and replies are logged to `logs.jsonl`

### 📁 Data Setup (Bring Your Own WhatsApp Chat)

This repo does **not include any message data** for privacy reasons. To use this project with your own chat history:

1. **Export your WhatsApp chat** (without media)  
   - On your phone:  
     `Chat > More Options > Export Chat > Without Media`

2. **Save the export as:**
   data/raw/chat_data.txt

   If you use a different name, update the path in `preprocess_chat.py`.

3. *(Optional but recommended)* If your export contains raw phone numbers (e.g. `+44789...`), create a mapping file:
   data/raw/number_map.json

   Example format:
   ```json
   {
   "+447891234567": "Alice",
   "+12125550123": "Bob"
   }

4. **Run the preprocessing script**:
   python data_preparation/preprocess_chat.py

   - This will generate:
   data/processed/processed_chat.csv

The data and mapping files are excluded from version control and will not be uploaded.

### .gitignore

This project includes a `.gitignore` that excludes:

- Node.js dependencies (`node_modules/`)
- WhatsApp auth sessions (`.wwebjs_auth/`, `.wwebjs_cache/`)
- Logs (`logs.jsonl`)
- Environment variables (`.env`)

Make sure to **create your own `.env` file** using `.env.example` as a reference, and **never commit it**.

---

## 🛠 Requirements

### WhatsApp Bot (Node.js)
- Node.js 18+
- `npm install` in `whatsapp-bot/`

### Colab (Model Hosting)
- Google Colab + GPU
- Hugging Face account (for loading Mistral base model)
- Ngrok account (for public URL)
- `pip install transformers flask flask-cors scikit-learn torch`

---

## 📦 To Run the Bot

1. Open `host_model.ipynb` in Colab and run all cells
2. *(Optional)* run `model_hosting/rag_server.py` for RAG-enabled replies
3. Copy the ngrok URL
4. Update `bot.js` with that URL
5. In `whatsapp-bot/`:
   ```bash
   npm start
6. Scan the QR code with Gurt's WhatsApp account

---

## 💡 Future Improvements
- Respond only when called ("Gurt")
- Better multi-turn context handling
- Persistent memory across restarts
- Deploy to a VPS (no need for local machine)

---

## Credit
Made by Alen Rostomyan.
