import { configureStore as rtkConfigureStore } from '@reduxjs/toolkit';
import { persistStore, REGISTER, PERSIST } from 'redux-persist';
import authReducer, { reducerPath as AUTH } from '../features/auth/store';
import { rtkqErrorMiddleware } from './rtkq-error.middleware';
import { setupListeners } from '@reduxjs/toolkit/query';
import {
  dashboardApi,
  reducerPath as DASHBOARD,
} from '../pages/Dashboard/store';
import { uploadApi, reducerPath as UPLOAD } from '../pages/Upload/store';
import { logsApi, reducerPath as LOGS } from '../pages/Logs/store';
import { newDashboardApi, reducerPath as NEWDASHBOARD } from '../pages/NewDashboard/store';
import { adminApi, reducerPath as ADMIN } from '../pages/Admin/store';
import { configureApi, reducerPath as CONFIG } from '../components/default-layout/store';
import { loginAuthApi, reducerPath as LOGIN } from '../features/auth/Login/store';
import { activityLogsApi, reducerPath as ACTIVITYLOGS } from '../pages/ActivityLogs/store';

export function configureStore() {
  const store = rtkConfigureStore({
    reducer: {
      [AUTH]: authReducer,
      [DASHBOARD]: dashboardApi.reducer,
      [UPLOAD]: uploadApi.reducer,
      [LOGS]: logsApi.reducer,
      [NEWDASHBOARD]: newDashboardApi.reducer,
      [ADMIN]: adminApi.reducer,
      [CONFIG]: configureApi.reducer,
      [LOGIN]: loginAuthApi.reducer,
      [ACTIVITYLOGS]: activityLogsApi.reducer,

    },
    devTools: {
      name: 'Penguin S3 Dashboard',
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [REGISTER, PERSIST],
        },
      }).concat(
        rtkqErrorMiddleware,
        dashboardApi.middleware,
        uploadApi.middleware,
        logsApi.middleware,
        newDashboardApi.middleware,
        adminApi.middleware,
        configureApi.middleware,
        loginAuthApi.middleware,
        activityLogsApi.middleware,
      ),
  });
  // Do not provide default configuration for root level. Each slice should do its own keeping.
  const persistor = persistStore(store);
  setupListeners(store.dispatch);
  return { store, persistor };
}
export const { store, persistor } = configureStore();
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
