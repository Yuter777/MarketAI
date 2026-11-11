const axios = require('axios');
const { formatMessage } = require('./parser');
const logger = require('./logger');

const FLOOD_WAIT_RE = /FLOOD_WAIT_(\d+)/;
const TELEGRAM_API = 'https://api.telegram.org';

class Forwarder {
  constructor(config) {
    this.botToken = config.target.botToken;
    this.chatIds = config.target.chatIds;
    this.baseUrl = `${TELEGRAM_API}/bot${this.botToken}`;
  }

  async send(rawText) {
    const text = formatMessage(rawText);

    const results = await Promise.allSettled(
      this.chatIds.map((chatId) => this._sendToChat(chatId, text))
    );

    results.forEach((result, i) => {
      if (result.status === 'rejected') {
        logger.error(`Failed to send to ${this.chatIds[i]}: ${result.reason?.message}`);
      } else {
        logger.info(`Forwarded to ${this.chatIds[i]}`);
      }
    });
  }

  async _sendToChat(chatId, text, retries = 3) {
    try {
      await axios.post(`${this.baseUrl}/sendMessage`, {
        chat_id: chatId,
        text,
        parse_mode: 'HTML',
        disable_web_page_preview: true,
      });
    } catch (err) {
      const telegramErr = err.response?.data?.description || '';
      const floodMatch = telegramErr.match(FLOOD_WAIT_RE);

      if (floodMatch && retries > 0) {
        const waitSec = parseInt(floodMatch[1], 10) + 1;
        logger.warn(`FloodWait for ${chatId}: waiting ${waitSec}s`);
        await sleep(waitSec * 1000);
        return this._sendToChat(chatId, text, retries - 1);
      }

      if (err.response?.status === 429 && retries > 0) {
        const retryAfter = err.response.headers['retry-after'] || 5;
        logger.warn(`Rate limited for ${chatId}: waiting ${retryAfter}s`);
        await sleep(retryAfter * 1000);
        return this._sendToChat(chatId, text, retries - 1);
      }

      throw err;
    }
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

module.exports = Forwarder;
