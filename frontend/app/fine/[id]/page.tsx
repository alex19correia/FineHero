'use client';

import FineDetailsForm from '@/components/fine/fine-details-form';
import { useParams } from 'next/navigation';

export default function FineDetailsPage() {
  const params = useParams();
  const { id } = params;

  return (
    <div className="container mx-auto px-6 py-16">
      <div className="flex flex-col items-center justify-center">
        <FineDetailsForm fineId={id as string} />
      </div>
    </div>
  );
}
