const { Client, LocalAuth } = require('whatsapp-web.js');
const axios = require('axios');
const qrcode = require('qrcode-terminal');
const fs = require('fs');

const client = new Client({
    authStrategy: new LocalAuth()
});

const chatMemory = {};
const MEMORY_LIMIT = 3;

client.on('qr', qr => qrcode.generate(qr, { small: true }));
client.on('ready', () => console.log('✅ WhatsApp bot is ready!'));

client.on('message', async msg => {
    if (msg.fromMe) return;

    const chat = await msg.getChat();
    const chatId = chat.id._serialized;

    // Only reply if "gurt" is mentioned
    if (!msg.body.toLowerCase().includes("gurt")) return;

    // Remove system annotation like "This message was edited"
    const cleanedMsg = msg.body.replace(/<This message was edited>/gi, "").trim();
    const name = msg._data.notifyName || "User";
    const entry = `${name}: ${cleanedMsg}`;

    // Memory setup
    if (!chatMemory[chatId]) {
        chatMemory[chatId] = [];
    }

    chatMemory[chatId].push(entry);
    if (chatMemory[chatId].length > MEMORY_LIMIT) {
        chatMemory[chatId] = chatMemory[chatId].slice(-MEMORY_LIMIT);
    }

    const prompt = chatMemory[chatId].join("\n") + `\nGurt:`;

    try {
        const response = await axios.post("https://your-ngrok-url.ngrok-free.app/generate", {
            prompt: prompt
        });

        // Clean up reply (remove garbage Unicode)
        const rawReply = response.data.response;
        const cleanReply = rawReply.replace(/[^\x00-\x7F]/g, "").trim();

        await msg.reply(cleanReply);

        chatMemory[chatId].push(`Gurt: ${cleanReply}`);
        if (chatMemory[chatId].length > MEMORY_LIMIT) {
            chatMemory[chatId] = chatMemory[chatId].slice(-MEMORY_LIMIT);
        }

        // Log the interaction
        const logEntry = {
            from: msg.author || msg.from,
            message: msg.body,
            response: cleanReply,
            timestamp: new Date().toISOString(),
            memory: [...chatMemory[chatId]]
        };

        fs.appendFile("logs.jsonl", JSON.stringify(logEntry) + "\n", err => {
            if (err) console.error("❌ Error logging message:", err.message);
        });

    } catch (error) {
        console.error("❌ Error generating reply:", error.message);
    }
});

client.initialize();
