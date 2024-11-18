const API_BASE_URL = 'http://127.0.0.1:5000/api';

export const startRecording = async (motion: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/record`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ motion }),
    });
    return response.json();
  } catch (error) {
    console.error('Recording error:', error);
    return { status: 'error', message: 'Failed to connect to server' };
  }
};

export const stopRecording = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/stop-recording`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
    });
    return response.json();
  } catch (error) {
    console.error('Stop recording error:', error);
    return { status: 'error', message: 'Failed to connect to server' };
  }
};

export const trainModel = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/train`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
    });
    return response.json();
  } catch (error) {
    console.error('Training error:', error);
    return { status: 'error', message: 'Failed to connect to server' };
  }
};

export const startInference = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/start-inference`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
    });
    return response.json();
  } catch (error) {
    console.error('Inference error:', error);
    return { status: 'error', message: 'Failed to connect to server' };
  }
};

export const stopInference = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/stop-inference`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
    });
    return response.json();
  } catch (error) {
    console.error('Stop inference error:', error);
    return { status: 'error', message: 'Failed to connect to server' };
  }
};

export const getStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/status`, {
      headers: {
        'Accept': 'application/json',
      },
    });
    return response.json();
  } catch (error) {
    console.error('Status error:', error);
    return { status: 'waiting' };
  }
};