'use client';

import { motion } from 'framer-motion';
import HeroCharacter from './hero-character';

type AnimationSequenceProps = {
  children: React.ReactNode;
};

export default function AnimationSequence({ children }: AnimationSequenceProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -100 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
    >
      {children}
    </motion.div>
  );
}
