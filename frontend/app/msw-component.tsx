'use client';
import { useEffect } from 'react';

export default function MSWComponent({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (process.env.NODE_ENV === 'development') {
        require('../mocks/browser');
      }
    }
  }, []);

  return <>{children}</>;
}
