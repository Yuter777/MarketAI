const DIVIDER = '━━━━━━━━━━';

/**
 * Formats a raw HUMO bot message into a styled notification.
 * @param {string} rawText
 * @returns {string}
 */
function formatMessage(rawText) {
  const time = new Date().toLocaleString('uz-UZ', {
    timeZone: 'Asia/Tashkent',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return [
    `💳 <b>HUMO Xabarnoma</b>`,
    DIVIDER,
    rawText,
    DIVIDER,
    `⏰ ${time}`,
  ].join('\n');
}

module.exports = { formatMessage };
