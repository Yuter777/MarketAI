const { TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const { NewMessage } = require('telegram/events');
const logger = require('./logger');

class TelegramUserClient {
  constructor(config) {
    this.config = config;
    this.client = null;
    this.reconnectAttempts = 0;
  }

  async connect() {
    const { apiId, apiHash, sessionString } = this.config.telegram;

    const session = new StringSession(sessionString);

    this.client = new TelegramClient(session, apiId, apiHash, {
      connectionRetries: this.config.reconnect.maxAttempts,
      retryDelay: this.config.reconnect.delayMs,
      autoReconnect: true,
      floodSleepThreshold: 60,
    });

    await this.client.connect();

    const me = await this.client.getMe();
    logger.info(`Logged in as: ${me.username || me.phone}`);

    return this.client;
  }

  /**
   * Register a handler that fires on every new message from the source chat.
   * @param {(message: import('telegram').Api.Message) => Promise<void>} handler
   */
  async listenTo(sourceChat, handler) {
    const entity = await this.client.getEntity(sourceChat).catch((err) => {
      throw new Error(`Cannot resolve source chat "${sourceChat}": ${err.message}`);
    });

    logger.info(`Listening to: ${sourceChat} (id=${entity.id})`);

    this.client.addEventHandler(async (event) => {
      const msg = event.message;
      if (!msg?.peerId) return;

      try {
        const chatId = msg.peerId.userId || msg.peerId.channelId || msg.peerId.chatId;
        if (chatId?.toString() !== entity.id?.toString()) return;

        const text = msg.message;
        if (!text) return;

        logger.debug(`New message from ${sourceChat}: ${text.slice(0, 80)}`);
        await handler(text);
      } catch (err) {
        logger.error('Handler error:', err.message);
      }
    }, new NewMessage({}));
  }

  async disconnect() {
    if (this.client) {
      await this.client.disconnect();
      logger.info('Disconnected from Telegram');
    }
  }

  isConnected() {
    return this.client?.connected ?? false;
  }
}

module.exports = TelegramUserClient;
