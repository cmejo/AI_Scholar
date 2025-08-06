import React from 'react';

interface MobileGridProps {
  children: React.ReactNode;
  columns?: 1 | 2 | 3 | 4;
  gap?: 'small' | 'medium' | 'large';
  className?: string;
  responsive?: boolean;
}

export const MobileGrid: React.FC<MobileGridProps> = ({
  children,
  columns = 2,
  gap = 'medium',
  className = '',
  responsive = true
}) => {
  const gapClasses = {
    small: 'gap-2',
    medium: 'gap-4',
    large: 'gap-6'
  };

  const columnClasses = responsive ? {
    1: 'grid-cols-1',
    2: 'grid-cols-1 xs:grid-cols-2',
    3: 'grid-cols-1 xs:grid-cols-2 sm:grid-cols-3',
    4: 'grid-cols-2 xs:grid-cols-2 sm:grid-cols-3 md:grid-cols-4'
  } : {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4'
  };

  return (
    <div className={`grid ${columnClasses[columns]} ${gapClasses[gap]} ${className}`}>
      {children}
    </div>
  );
};

interface MobileGridItemProps {
  children: React.ReactNode;
  span?: 1 | 2 | 3 | 4;
  className?: string;
}

export const MobileGridItem: React.FC<MobileGridItemProps> = ({
  children,
  span = 1,
  className = ''
}) => {
  const spanClasses = {
    1: 'col-span-1',
    2: 'col-span-2',
    3: 'col-span-3',
    4: 'col-span-4'
  };

  return (
    <div className={`${spanClasses[span]} ${className}`}>
      {children}
    </div>
  );
};