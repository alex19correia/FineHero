'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { useMutation } from '@tanstack/react-query';

export default function UploadZone() {
  const [progress, setProgress] = useState(0);
  const router = useRouter();

  const mutation = useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post('/api/v1/uploads/fine-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          setProgress(percentCompleted);
        },
      });
    },
    onSuccess: (data) => {
      router.push(`/fine/${data.data.fine_id}`);
    },
  });

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        mutation.mutate(file);
      }
    },
    [mutation]
  );

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
      className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center ${
        isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
      }`}
    >
      <input {...getInputProps()} />
      {mutation.isPending ? (
        <div>
          <div className="text-lg font-medium">A enviar...</div>
          <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
            <div
              className="h-2 rounded-full bg-blue-600 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-1 text-sm text-gray-600">{progress}%</div>
        </div>
      ) : (
        <div>
          <div className="text-lg font-medium">
            {isDragActive ? 'Larga o ficheiro aqui' : 'Carregar Multa'}
          </div>
          <div className="mt-1 text-gray-600">
            Arrasta e larga ou clica para selecionar (PDF, PNG, JPG)
          </div>
        </div>
      )}
    </div>
  );
}
