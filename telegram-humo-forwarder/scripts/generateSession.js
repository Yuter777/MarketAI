/**
 * Run once to generate a SESSION_STRING for your .env file.
 * Usage: node scripts/generateSession.js
 */
require('dotenv').config();

const { TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const input = require('input');

const API_ID = parseInt(process.env.API_ID, 10);
const API_HASH = process.env.API_HASH;

if (!API_ID || !API_HASH) {
  console.error('ERROR: Set API_ID and API_HASH in your .env file first.');
  process.exit(1);
}

(async () => {
  const session = new StringSession('');

  const client = new TelegramClient(session, API_ID, API_HASH, {
    connectionRetries: 3,
  });

  await client.start({
    phoneNumber: async () => input.text('Enter your phone number (with country code, e.g. +998901234567): '),
    password: async () => input.text('Enter your 2FA password (leave blank if none): '),
    phoneCode: async () => input.text('Enter the OTP code you received: '),
    onError: (err) => console.error('Login error:', err.message),
  });

  const sessionString = client.session.save();

  console.log('\n=== SESSION_STRING (copy this into your .env) ===');
  console.log(sessionString);
  console.log('================================================\n');

  await client.disconnect();
  process.exit(0);
})();
