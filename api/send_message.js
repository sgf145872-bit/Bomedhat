import { VercelRequest, VercelResponse } from '@vercel/node';
import fetch from 'node-fetch';

export default async (request, response) => {
  const { text } = request.body;

  if (!text) {
    return response.status(400).json({ error: 'Message text is required.' });
  }

  // احصل على هذه القيم من متغيرات البيئة (Environment Variables) في Vercel
  const BOT_TOKEN = process.env.BOT_TOKEN;
  const CHAT_ID = process.env.CHAT_ID;

  if (!BOT_TOKEN || !CHAT_ID) {
    return response.status(500).json({ error: 'Server configuration error: BOT_TOKEN or CHAT_ID not set.' });
  }

  const telegramApiUrl = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`;

  const telegramPayload = {
    chat_id: CHAT_ID,
    text: `رسالة جديدة من موقعك: \n\n${text}`,
    parse_mode: 'HTML'
  };

  try {
    const telegramResponse = await fetch(telegramApiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(telegramPayload)
    });

    const telegramResult = await telegramResponse.json();

    if (telegramResult.ok) {
      return response.status(200).json({ message: 'تم إرسال رسالتك بنجاح!' });
    } else {
      console.error('Telegram API Error:', telegramResult);
      return response.status(500).json({ error: 'Failed to send message via Telegram.', details: telegramResult.description });
    }
  } catch (error) {
    console.error('Network or Fetch Error:', error);
    return response.status(500).json({ error: 'Network error occurred while trying to send message.' });
  }
};
