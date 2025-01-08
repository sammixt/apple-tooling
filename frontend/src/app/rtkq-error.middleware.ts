import { isRejectedWithValue } from '@reduxjs/toolkit';
import type {
  Middleware,
  MiddlewareAPI,
  PayloadAction,
} from '@reduxjs/toolkit';
import { createStandaloneToast, UseToastOptions } from '@chakra-ui/react';
import { clearDetails } from '../features/auth/store';
import { theme } from './theme';

const { toast } = createStandaloneToast(theme);

type ErrorDataAction = PayloadAction<{
  data: {
    message: string;
  };
  status: number;
}>;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function isErrorDataAction(action: any): action is ErrorDataAction {
  return action.payload && action.payload.data && action.payload.status;
}

const TOAST_DEFAULTS: UseToastOptions = {
  title: 'Error',
  status: 'error',
  isClosable: true,
  position: 'top',
  duration: 5000,
};

export const rtkqErrorMiddleware: Middleware =
  (api: MiddlewareAPI) => (next) => (action) => {
    if (isRejectedWithValue(action)) {
      // Clean up all toasts to avoid to many error messages
      toast.closeAll();

      if (isErrorDataAction(action)) {
        const { status } = action.payload;

        if (status === 401) {
          // flash
          toast({
            ...TOAST_DEFAULTS,
            title: 'Your token has expired',
            description: 'Please sign in again to continue',
          });

          // dispatch logout
          api.dispatch(clearDetails());

          // navigate
          // Will be called by AuthRoute once the token disappear.
          // Or we can grab router here and call router.navigate
          // Or use window.history directly
          // window.location.replace('/login');

          return next(action);
        }

        if (status === 403) {
          // flash
          toast({
            ...TOAST_DEFAULTS,
            title: 'Unauthorized',
            description:
              'Your current role does not allow to perform some of the requested operations',
          });
          api.dispatch(clearDetails());

          return next(action);
        }
      }

      // toast({
      //   ...TOAST_DEFAULTS,
      //   description: isErrorDataAction(action)
      //     ? action.payload.data.message
      //     : action.error.message,
      // });
    }

    return next(action);
  };

export const createToast = (title: string, description: string) => {
  toast.closeAll();
  toast({
    ...TOAST_DEFAULTS,
    title,
    description
  });
}
