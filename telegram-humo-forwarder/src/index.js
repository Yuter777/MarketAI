require('dotenv').config();

const config = require('./config');
const TelegramUserClient = require('./telegramClient');
const Forwarder = require('./forwarder');
const logger = require('./logger');

const userClient = new TelegramUserClient(config);
const forwarder = new Forwarder(config);

async function main() {
  logger.info('Starting HUMO Forwarder...');

  await userClient.connect();

  await userClient.listenTo(config.source.chat, async (rawText) => {
    try {
      await forwarder.send(rawText);
    } catch (err) {
      logger.error('Forwarding error:', err.message);
    }
  });

  logger.info('Forwarder is running. Waiting for messages...');

  // Keep process alive
  await new Promise(() => {});
}

async function shutdown(signal) {
  logger.info(`Received ${signal}. Shutting down...`);
  await userClient.disconnect();
  process.exit(0);
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

process.on('unhandledRejection', (err) => {
  logger.error('Unhandled rejection:', err?.message || err);
});

process.on('uncaughtException', (err) => {
  logger.error('Uncaught exception:', err.message);
  process.exit(1);
});

main().catch((err) => {
  logger.error('Startup error:', err.message);
  process.exit(1);
});
