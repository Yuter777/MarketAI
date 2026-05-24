require('dotenv').config();

function required(name) {
  const val = process.env[name];
  if (!val) throw new Error(`Missing required env variable: ${name}`);
  return val;
}

function optionalInt(name, def) {
  const val = process.env[name];
  return val ? parseInt(val, 10) : def;
}

const config = {
  telegram: {
    apiId: parseInt(required('API_ID'), 10),
    apiHash: required('API_HASH'),
    sessionString: process.env.SESSION_STRING || '',
  },

  source: {
    chat: process.env.SOURCE_CHAT || 'HUMOcardbot',
  },

  target: {
    botToken: required('TARGET_BOT_TOKEN'),
    chatIds: (required('TARGET_CHAT_IDS'))
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean),
  },

  reconnect: {
    delayMs: optionalInt('RECONNECT_DELAY_MS', 5000),
    maxAttempts: optionalInt('MAX_RECONNECT_ATTEMPTS', 10),
  },

  logLevel: process.env.LOG_LEVEL || 'info',
};

module.exports = config;
