'use client';

import toast, { Toaster } from 'react-hot-toast';
import HeroCharacter from './hero-character';

export const SuperheroToaster = () => <Toaster />;

export const superheroToast = {
  success: (message: string) => {
    toast.custom((t) => (
      <div
        className={`${
          t.visible ? 'animate-enter' : 'animate-leave'
        } pointer-events-auto flex w-full max-w-md rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5`}
      >
        <div className="flex w-0 flex-1 items-center p-4">
          <div className="flex-shrink-0">
            <HeroCharacter width={50} height={50} />
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-900">FineHero chegou ao resgate! ✨</p>
            <p className="mt-1 text-sm text-gray-500">{message}</p>
          </div>
        </div>
        <div className="flex border-l border-gray-200">
          <button
            onClick={() => toast.dismiss(t.id)}
            className="flex w-full items-center justify-center rounded-none rounded-r-lg border border-transparent p-4 text-sm font-medium text-indigo-600 hover:text-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Fechar
          </button>
        </div>
      </div>
    ));
  },
  error: (message: string) => {
    toast.custom((t) => (
      <div
        className={`${
          t.visible ? 'animate-enter' : 'animate-leave'
        } pointer-events-auto flex w-full max-w-md rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5`}
      >
        <div className="flex w-0 flex-1 items-center p-4">
          <div className="flex-shrink-0">
            <HeroCharacter width={50} height={50} />
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-900">
              Ups! O FineHero precisa de um momento...
            </p>
            <p className="mt-1 text-sm text-gray-500">{message}</p>
          </div>
        </div>
        <div className="flex border-l border-gray-200">
          <button
            onClick={() => toast.dismiss(t.id)}
            className="flex w-full items-center justify-center rounded-none rounded-r-lg border border-transparent p-4 text-sm font-medium text-indigo-600 hover:text-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Fechar
          </button>
        </div>
      </div>
    ));
  },
};
