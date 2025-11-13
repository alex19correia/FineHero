import { http, HttpResponse } from 'msw';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const handlers = [
  http.post(`${API_BASE_URL}/auth/register`, () => {
    return HttpResponse.json({
      token: 'mock_token',
      user: {
        id: '1',
        email: 'test@example.com',
        full_name: 'Test User',
        subscription_type: 'basic',
        credits_remaining: 1,
        created_at: new Date().toISOString(),
      },
    });
  }),

  http.post(`${API_BASE_URL}/auth/login`, () => {
    return HttpResponse.json({
      token: 'mock_token',
      user: {
        id: '1',
        email: 'test@example.com',
        full_name: 'Test User',
        subscription_type: 'basic',
        credits_remaining: 1,
        created_at: new Date().toISOString(),
      },
    });
  }),

  http.get(`${API_BASE_URL}/users/profile`, () => {
    return HttpResponse.json({
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      subscription_type: 'basic',
      credits_remaining: 1,
      created_at: new Date().toISOString(),
    });
  }),

  http.post(`${API_BASE_URL}/auth/logout`, () => {
    return new HttpResponse(null, { status: 200 });
  }),

  http.post(`${API_BASE_URL}/uploads/fine-document`, () => {
    return HttpResponse.json({
      fine_id: '123',
    });
  }),

  http.get(`${API_BASE_URL}/fines/123`, () => {
    return HttpResponse.json({
      id: '123',
      user_id: '1',
      document_url: 'http://example.com/document.pdf',
      incident_date: '2025-11-13',
      incident_description: 'Estacionei em local proibido.',
      fine_type: 'parking',
      fine_amount: 50,
      status: 'uploaded',
      created_at: new Date().toISOString(),
    });
  }),

  http.put(`${API_BASE_URL}/fines/123`, () => {
    return new HttpResponse(null, { status: 200 });
  }),

  http.get(`${API_BASE_URL}/fines`, () => {
    return HttpResponse.json([
      {
        id: '123',
        user_id: '1',
        document_url: 'http://example.com/document.pdf',
        incident_date: '2025-11-13',
        incident_description: 'Estacionei em local proibido.',
        fine_type: 'parking',
        fine_amount: 50,
        status: 'uploaded',
        created_at: new Date().toISOString(),
      },
    ]);
  }),

  http.post(`${API_BASE_URL}/payments/subscribe`, () => {
    return HttpResponse.json({
      clientSecret: 'mock_client_secret',
    });
  }),

  http.post(`${API_BASE_URL}/payments/one-time`, () => {
    return HttpResponse.json({
      clientSecret: 'mock_client_secret',
    });
  }),
];
