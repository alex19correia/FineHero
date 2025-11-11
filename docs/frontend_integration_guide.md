# FineHero Frontend Integration Guide
*Connecting React/Next.js Frontend to Backend APIs*

## Overview
This guide covers connecting your existing FastAPI backend to a React/Next.js frontend for the FineHero SaaS legal service.

---

## Current Backend API Structure

### Existing Endpoints (From Review)
```python
# backend/app/api/v1/endpoints/
- defenses.py: POST /defenses/generate
- fines.py: GET/POST /fines
```

### Missing Endpoints Needed for SaaS
```python
# backend/app/api/v1/endpoints/
- auth.py: POST /auth/register, POST /auth/login
- payments.py: POST /payments/subscribe, POST /payments/one-time
- users.py: GET /users/profile, GET /users/dashboard
- uploads.py: POST /uploads/fine-document
```

---

## Frontend Project Structure

### Recommended Next.js Setup
```
frontend/
├── components/
│   ├── ui/              # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   └── Modal.tsx
│   ├── auth/            # Authentication components
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── ForgotPassword.tsx
│   ├── upload/          # Document upload
│   │   ├── UploadZone.tsx
│   │   ├── UploadProgress.tsx
│   │   └── FilePreview.tsx
│   ├── fine/            # Fine management
│   │   ├── FineForm.tsx
│   │   ├── FineCard.tsx
│   │   └── FineStatus.tsx
│   ├── letter/          # Letter generation
│   │   ├── LetterPreview.tsx
│   │   ├── LetterEditor.tsx
│   │   └── LetterDownload.tsx
│   └── payment/         # Payment processing
│       ├── PaymentForm.tsx
│       ├── SubscriptionPlans.tsx
│       └── PaymentSuccess.tsx
├── pages/
│   ├── index.tsx        # Landing page
│   ├── login.tsx
│   ├── register.tsx
│   ├── dashboard.tsx
│   ├── upload.tsx
│   ├── fine/
│   │   ├── [id].tsx     # Fine detail page
│   │   └── create.tsx   # Create new fine
│   ├── payment/
│   │   ├── subscribe.tsx
│   │   └── success.tsx
│   └── profile.tsx      # User profile
├── hooks/               # Custom React hooks
│   ├── useAuth.ts       # Authentication state
│   ├── useApi.ts        # API communication
│   ├── useUpload.ts     # File upload logic
│   └── usePayment.ts    # Payment processing
├── utils/
│   ├── api.ts           # API client configuration
│   ├── auth.ts          # Authentication utilities
│   ├── format.ts        # Date/price formatting
│   └── validation.ts    # Form validation
├── types/               # TypeScript definitions
│   ├── api.ts           # API response types
│   ├── user.ts          # User types
│   └── fine.ts          # Fine-related types
└── styles/
    ├── globals.css      # Global styles
    └── components.css   # Component-specific styles
```

---

## API Client Setup

### Backend API Configuration
```typescript
// frontend/utils/api.ts
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### TypeScript Types
```typescript
// frontend/types/api.ts
export interface User {
  id: string;
  email: string;
  full_name: string;
  subscription_type: 'basic' | 'professional' | 'premium';
  credits_remaining: number;
  created_at: string;
}

export interface Fine {
  id: string;
  user_id: string;
  document_url: string;
  incident_date: string;
  incident_description: string;
  fine_type: string;
  fine_amount: number;
  status: 'uploaded' | 'processing' | 'generated' | 'paid' | 'completed';
  generated_letter_url?: string;
  created_at: string;
}

export interface DefenseLetter {
  id: string;
  fine_id: string;
  content: string;
  status: 'draft' | 'final';
  generated_at: string;
}

export interface Payment {
  id: string;
  user_id: string;
  amount: number;
  payment_type: 'subscription' | 'one_time';
  stripe_payment_id: string;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
}
```

---

## Authentication System

### Auth Hook
```typescript
// frontend/hooks/useAuth.ts
import { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { User } from '../types/api';

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

export const useAuth = (): AuthState => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get('/users/profile');
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('auth_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    const { token, user } = response.data;
    localStorage.setItem('auth_token', token);
    setUser(user);
  };

  const register = async (data: RegisterData) => {
    const response = await api.post('/auth/register', data);
    const { token, user } = response.data;
    localStorage.setItem('auth_token', token);
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  return { user, loading, login, register, logout };
};
```

### Protected Route Component
```typescript
// frontend/components/auth/ProtectedRoute.tsx
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/useAuth';
import { ReactNode } from 'react';

interface ProtectedRouteProps {
  children: ReactNode;
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
};
```

---

## Document Upload System

### Upload Component
```typescript
// frontend/components/upload/UploadZone.tsx
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useRouter } from 'next/router';
import { api } from '../../utils/api';

export const UploadZone = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const router = useRouter();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);

      // Upload file
      const response = await api.post('/uploads/fine-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        },
      });

      // Redirect to fine details page
      router.push(`/fine/${response.data.fine_id}`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [router]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer ${
        isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
      }`}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <div>
          <div className="text-lg font-medium">Uploading...</div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="text-sm text-gray-600 mt-1">{progress}%</div>
        </div>
      ) : (
        <div>
          <div className="text-lg font-medium">
            {isDragActive ? 'Drop the file here' : 'Upload your fine document'}
          </div>
          <div className="text-gray-600 mt-1">
            Drag & drop or click to select (PDF, PNG, JPG)
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## Fine Details Form

### Fine Creation Form
```typescript
// frontend/components/fine/FineForm.tsx
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { api } from '../../utils/api';

interface FineFormProps {
  fineId: string;
}

export const FineForm = ({ fineId }: FineFormProps) => {
  const [loading, setLoading] = useState(false);
  const [fine, setFine] = useState(null);
  const [formData, setFormData] = useState({
    incident_date: '',
    incident_time: '',
    location: '',
    fine_type: '',
    fine_amount: '',
    incident_description: '',
    witness_info: '',
    additional_notes: '',
  });
  const router = useRouter();

  useEffect(() => {
    if (fineId) {
      fetchFine();
    }
  }, [fineId]);

  const fetchFine = async () => {
    try {
      const response = await api.get(`/fines/${fineId}`);
      setFine(response.data);
    } catch (error) {
      console.error('Failed to fetch fine:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.put(`/fines/${fineId}`, formData);
      
      // Redirect to payment or letter generation
      router.push(`/fine/${fineId}/generate`);
    } catch (error) {
      console.error('Failed to update fine:', error);
      alert('Failed to save details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Incident Date
          </label>
          <input
            type="date"
            name="incident_date"
            value={formData.incident_date}
            onChange={handleInputChange}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Incident Time
          </label>
          <input
            type="time"
            name="incident_time"
            value={formData.incident_time}
            onChange={handleInputChange}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">
            Location
          </label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleInputChange}
            placeholder="Street, city, or specific location"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Fine Type
          </label>
          <select
            name="fine_type"
            value={formData.fine_type}
            onChange={handleInputChange}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            required
          >
            <option value="">Select fine type</option>
            <option value="parking">Parking Violation</option>
            <option value="speeding">Speeding</option>
            <option value="red_light">Red Light</option>
            <option value="no_entry">No Entry</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Fine Amount (€)
          </label>
          <input
            type="number"
            name="fine_amount"
            value={formData.fine_amount}
            onChange={handleInputChange}
            step="0.01"
            min="0"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            required
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">
            Incident Description
          </label>
          <textarea
            name="incident_description"
            value={formData.incident_description}
            onChange={handleInputChange}
            rows={4}
            placeholder="Describe what happened in detail..."
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            required
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">
            Additional Notes
          </label>
          <textarea
            name="additional_notes"
            value={formData.additional_notes}
            onChange={handleInputChange}
            rows={3}
            placeholder="Any other relevant information..."
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
          />
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Generate Defense Letter'}
        </button>
      </div>
    </form>
  );
};
```

---

## Payment Integration

### Stripe Payment Form
```typescript
// frontend/components/payment/PaymentForm.tsx
import { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { useRouter } from 'next/router';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

interface PaymentFormProps {
  fineId: string;
  amount: number;
  planType: 'single' | 'subscription';
}

export const PaymentForm = ({ fineId, amount, planType }: PaymentFormProps) => {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handlePayment = async () => {
    setLoading(true);

    try {
      // Create payment intent
      const response = await fetch('/api/create-payment-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fineId, amount, planType }),
      });

      const { clientSecret } = await response.json();

      // Get Stripe instance
      const stripe = await stripePromise;

      if (!stripe) {
        throw new Error('Stripe failed to load');
      }

      // Confirm payment
      const { error } = await stripe.confirmPayment({
        elements: stripe.elements(),
        clientSecret,
        confirmParams: {
          return_url: `${window.location.origin}/payment/success?fineId=${fineId}`,
        },
      });

      if (error) {
        console.error('Payment failed:', error);
        alert('Payment failed. Please try again.');
      }
    } catch (error) {
      console.error('Payment error:', error);
      alert('Payment processing failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h3 className="text-lg font-medium mb-4">Payment Details</h3>
      
      <div className="mb-4">
        <div className="flex justify-between items-center">
          <span>Defense Letter Generation</span>
          <span className="font-medium">€{amount}</span>
        </div>
        {planType === 'subscription' && (
          <div className="text-sm text-gray-600 mt-1">
            Monthly subscription - cancel anytime
          </div>
        )}
      </div>

      <div id="payment-element" className="mb-4">
        {/* Stripe Payment Element will be rendered here */}
      </div>

      <button
        onClick={handlePayment}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Processing...' : `Pay €${amount}`}
      </button>
    </div>
  );
};
```

---

## Dashboard Component

### User Dashboard
```typescript
// frontend/pages/dashboard.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../utils/api';
import { Fine } from '../types/api';
import Link from 'next/link';

export default function Dashboard() {
  const { user } = useAuth();
  const [fines, setFines] = useState<Fine[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFines();
  }, []);

  const fetchFines = async () => {
    try {
      const response = await api.get('/fines');
      setFines(response.data);
    } catch (error) {
      console.error('Failed to fetch fines:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'paid': return 'text-blue-600';
      case 'processing': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'uploaded': return 'Uploaded';
      case 'processing': return 'Processing';
      case 'generated': return 'Generated';
      case 'paid': return 'Paid';
      case 'completed': return 'Completed';
      default: return status;
    }
  };

  if (loading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-600">
          Welcome back, {user?.full_name}! 
          {user?.subscription_type && (
            <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              {user.subscription_type} Plan
            </span>
          )}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-2">Total Fines</h3>
          <p className="text-3xl font-bold text-blue-600">{fines.length}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-2">Completed</h3>
          <p className="text-3xl font-bold text-green-600">
            {fines.filter(f => f.status === 'completed').length}
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-2">Credits Remaining</h3>
          <p className="text-3xl font-bold text-purple-600">
            {user?.credits_remaining || 0}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Your Fines</h2>
            <Link 
              href="/fine/create"
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Add New Fine
            </Link>
          </div>
        </div>

        <div className="p-6">
          {fines.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">No fines uploaded yet</p>
              <Link 
                href="/fine/create"
                className="text-blue-600 hover:text-blue-800"
              >
                Upload your first fine document
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {fines.map((fine) => (
                <div 
                  key={fine.id} 
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium">{fine.fine_type}</h3>
                      <p className="text-sm text-gray-600">
                        {fine.incident_date} - €{fine.fine_amount}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {fine.location}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded-full text-sm ${getStatusColor(fine.status)}`}>
                        {getStatusText(fine.status)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-4 flex justify-between items-center">
                    <Link
                      href={`/fine/${fine.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      View Details
                    </Link>
                    
                    {fine.status === 'generated' && (
                      <Link
                        href={`/fine/${fine.id}/payment`}
                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                      >
                        Complete Payment
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## Next Steps for Implementation

### Week 1: Setup Foundation
1. **Create Next.js project** with TypeScript
2. **Setup API client** with authentication interceptors
3. **Create basic auth components** (login/register)
4. **Setup routing structure**

### Week 2: Core Features
1. **Implement document upload** with drag & drop
2. **Create fine details form** with validation
3. **Build user dashboard** with fine listing
4. **Add navigation and layout** components

### Week 3: Payment Integration
1. **Setup Stripe integration** with webhooks
2. **Create payment forms** for single/subscription payments
3. **Implement success/error pages**
4. **Add subscription management**

### Week 4: Polish & Testing
1. **Add loading states** and error handling
2. **Implement responsive design**
3. **Add accessibility features**
4. **Test end-to-end user flows**

---

*Frontend Integration Guide*  
*Created: 2025-11-11*  
*Status: Ready for Implementation*