export default function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method Not Allowed' });
  }

  // Return a simple 200 OK response
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
} 