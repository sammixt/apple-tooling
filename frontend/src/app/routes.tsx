import React from 'react';
import {
  createBrowserRouter,
  isRouteErrorResponse,
  useRouteError,
} from 'react-router-dom';
import { NotFound } from '../pages/NotFound';
import { AuthRoute } from '../components/auth-route/auth-route';
import DefaultLayout from '../components/default-layout/default-layout';
import { NEWDASHBOARD } from './path';

function ErrorBoundary() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    if (error.status === 404) {
      return <NotFound homeUrl={NEWDASHBOARD} />;
    }
  }

  console.error(error);

  return <NotFound homeUrl={NEWDASHBOARD} />;
}

export function createRouter() {
  const getUserPermissions = () => {
    try {
      return JSON.parse(localStorage.getItem('userPermissions')) || {};
    } catch {
      return {};
    }
  };

  const userPermissions = getUserPermissions();

  const routerConfig = [
    {
      path: '/',
      ErrorBoundary,
      element: (
        <AuthRoute>
          <DefaultLayout />
        </AuthRoute>
      ),
      children: [
        {
          path: '/',
          lazy: () => import('../features/redirect/Redirect'),
        },
        {
          path: '/dashboard',
          lazy: () => import('../pages/NewDashboard'),
        },
        {
          path: '/upload',
          lazy: () => import('../pages/Upload'),
        },
        {
          path: '/activity-logs',
          lazy: async () => {
            if (!getUserPermissions().logs) {
              throw new Error('Not authorized');
            }
            return import('../pages/ActivityLogs');
          },
        },
        {
          path: '/logs',
          lazy: async () => {
            if (!getUserPermissions().logs) {
              throw new Error('Not authorized');
            }
            return import('../pages/Logs');
          },
        },
        {
          path: '/admin',
          lazy: async () => {
            const permissions = getUserPermissions();
            if (!(permissions.user_management)) {
              throw new Error('Not authorized');
            }
            return import('../pages/Admin');
          },
        },
      ],
    },
    {
      path: '/login',
      lazy: () => import('../features/auth/Login'),
    },
  ];

  const router = createBrowserRouter(routerConfig);

  return router;
}
