// Chat Service
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class ChatService {
  async getChatHistory() {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/history/list`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch chat history');
      }

      return await response.json();
    } catch (error) {
      throw new Error('Failed to fetch chat history');
    }
  }

  async getChatSession(sessionId) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/history/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch chat session');
      }

      return await response.json();
    } catch (error) {
      throw new Error('Failed to fetch chat session');
    }
  }

  async saveChatSession(sessionData) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/history/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(sessionData),
      });

      if (!response.ok) {
        throw new Error('Failed to save chat session');
      }

      return await response.json();
    } catch (error) {
      throw new Error('Failed to save chat session');
    }
  }

  async renameChatSession(sessionId, title) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/history/${sessionId}/rename`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ title }),
      });
      if (!response.ok) throw new Error('Failed to rename chat session');
      return await response.json();
    } catch (error) {
      throw new Error('Failed to rename chat session');
    }
  }

  async deleteChatSession(sessionId) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/history/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete chat session');
      }

      return await response.json();
    } catch (error) {
      throw new Error('Failed to delete chat session');
    }
  }
}

export const chatService = new ChatService();
