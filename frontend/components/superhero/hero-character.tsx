import Image from 'next/image';
import { clsx } from 'clsx';

type HeroCharacterProps = {
  className?: string;
  width?: number;
  height?: number;
};

export default function HeroCharacter({
  className,
  width = 300,
  height = 300,
}: HeroCharacterProps) {
  return (
    <div className={clsx('relative', className)}>
      <Image
        src="/images/superhero/finehero-character.png"
        alt="FineHero Superhero"
        width={width}
        height={height}
        priority
      />
    </div>
  );
}
