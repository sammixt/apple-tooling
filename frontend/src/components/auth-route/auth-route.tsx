import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';

import { useAppSelector } from '../../hooks/store';
import { getAuthToken } from '../../features/auth/store';
import { LOGIN } from '../../app/path';

export interface AuthRouteProps {
  children: ReactNode;
  redirectTo?: string;
}

export function AuthRoute({ children, redirectTo = LOGIN }: AuthRouteProps) {
  const authToken = useAppSelector(getAuthToken);

  if (!authToken) {
    // User is not logged in, redirect them to the login page
    return <Navigate to={redirectTo} replace />;
  }

  return children;
}
