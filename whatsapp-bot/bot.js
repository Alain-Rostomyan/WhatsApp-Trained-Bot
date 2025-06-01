const { Client, LocalAuth } = require('whatsapp-web.js');
const axios = require('axios');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
require('dotenv').config();

const MEMORY_FILE = 'memory.json';
const LOG_FILE = 'logs.jsonl';
const MEMORY_LIMIT = 5;
const API_URL = process.env.NGROK_URL;
const ADMIN_NUMBERS = process.env.ADMIN_NUMBERS ? process.env.ADMIN_NUMBERS.split(',') : [];

let chatMemory = {};

// Load memory from disk
if (fs.existsSync(MEMORY_FILE)) {
    try {
        chatMemory = JSON.parse(fs.readFileSync(MEMORY_FILE));
        console.log('✅ Memory loaded from disk.');
    } catch (err) {
        console.error('❌ Failed to load memory:', err);
    }
}

function saveMemory() {
    fs.writeFileSync(MEMORY_FILE, JSON.stringify(chatMemory, null, 2));
}

function updateMemory(chatId, userId, line) {
    if (!chatMemory[chatId]) chatMemory[chatId] = {};
    if (!chatMemory[chatId][userId]) chatMemory[chatId][userId] = [];

    // Skip Gurt's lines from being added again
    if (line.startsWith('Gurt:')) return;

    chatMemory[chatId][userId].push(line);
    if (chatMemory[chatId][userId].length > MEMORY_LIMIT) {
        chatMemory[chatId][userId] = chatMemory[chatId][userId].slice(-MEMORY_LIMIT);
    }
    saveMemory();
}

function getPrompt(chatId, userId, chatTitle) {
    const memory = chatMemory[chatId]?.[userId] || [];
    const tone = getToneFromTitle(chatTitle);
    const hour = new Date().getHours() + 2;
    const timeHint = `Current time: ${hour}:00.`;
    return `[Tone: ${tone}]\n${timeHint}\n${memory.join('\n')}\nGurt:`;
}

function getToneFromTitle(title) {
    if (!title) return 'neutral';
    const lower = title.toLowerCase();
    if (lower.includes('memes')) return 'funny';
    if (lower.includes('work')) return 'formal';
    if (lower.includes('family')) return 'casual';
    return 'neutral';
}

function isAdmin(userId) {
    return ADMIN_NUMBERS.includes(userId);
}


const client = new Client({
    authStrategy: new LocalAuth()
});

client.on('qr', qr => qrcode.generate(qr, { small: true }));
client.on('ready', () => console.log('✅ WhatsApp bot is ready!'));

client.on('message', async msg => {
    if (msg.fromMe) return;

    const chat = await msg.getChat();
    const chatId = chat.id._serialized;
    const rawUserId = msg.author || msg.from;
    const userId = rawUserId.replace(/@.*$/, ''); // Strip @c.us or @g.us
    const name = msg._data.notifyName || 'User';
    const cleanedMsg = msg.body.replace(/<This message was edited>/gi, '').trim();
    const entry = `${name}: ${cleanedMsg}`;

    // Admin command handling
    if (cleanedMsg.toLowerCase() === 'gurt reset memory' && isAdmin(userId)) {
        if (chatMemory[chatId]) delete chatMemory[chatId];
        saveMemory();
        await msg.reply('Memory reset.');
        return;
    }

    if (cleanedMsg.toLowerCase() === 'gurt leave group' && isAdmin(userId) && chat.isGroup) {
        await msg.reply('Ts pmo fr ima dip');
        await chat.leave();
        return;
    }

    // Only respond if "gurt" is mentioned
    if (!cleanedMsg.toLowerCase().includes('gurt')) return;

    updateMemory(chatId, userId, entry);

    const prompt = getPrompt(chatId, userId, chat.name);
    const start = Date.now();

    try {
        const response = await axios.post(`${API_URL}/generate`, { prompt });
        const rawReply = response.data.response;
        const cleanReply = rawReply.replace(/\uFFFD/g, '').trim();

        if (!cleanReply || cleanReply.length < 2) {
            console.log('⚠️ Empty or invalid response, not replying.');
            return;
        }

        await msg.reply(cleanReply);
        updateMemory(chatId, userId, `Gurt: ${cleanReply}`);

        const duration = Date.now() - start;
        const logEntry = {
            from: userId,
            message: cleanedMsg,
            response: cleanReply,
            chat: chat.name || chatId,
            timestamp: new Date().toISOString(),
            memorySize: chatMemory[chatId]?.[userId]?.length || 0,
            durationMs: duration
        };
        fs.appendFile(LOG_FILE, JSON.stringify(logEntry) + '\n', err => {
            if (err) console.error('❌ Error logging message:', err.message);
        });

    } catch (err) {
        console.error('❌ Error generating reply:', err);
        fs.appendFile(LOG_FILE, JSON.stringify({
            from: userId,
            error: err.message,
            timestamp: new Date().toISOString()
        }) + '\n', () => {});
    }
});

client.initialize();
