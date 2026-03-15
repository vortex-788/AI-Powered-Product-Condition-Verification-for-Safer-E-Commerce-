import axios from 'axios';

// Use VITE_API_BASE_URL if available (for Vercel deployment), else use the Vite proxy (/api)
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// Product APIs
export const createProduct = async (formData) => {
  const { data } = await api.post('/products', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const getProducts = async (params = {}) => {
  const { data } = await api.get('/products', { params });
  return data;
};

export const getProduct = async (id) => {
  const { data } = await api.get(`/products/${id}`);
  return data;
};

export const getProductPassport = async (id) => {
  const { data } = await api.get(`/products/${id}/passport`);
  return data;
};

// Verification APIs
export const verifyImage = async (formData) => {
  const { data } = await api.post('/verify/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const verifyVideo = async (formData) => {
  const { data } = await api.post('/verify/video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const getVerificationHistory = async (productId) => {
  const { data } = await api.get(`/verify/${productId}/history`);
  return data;
};

// Fraud APIs
export const checkFraud = async (formData) => {
  const { data } = await api.post('/fraud/check', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const getFraudHistory = async (productId) => {
  const { data } = await api.get(`/fraud/${productId}`);
  return data;
};

export default api;
