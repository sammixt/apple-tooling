import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { StrictMode } from 'react';
import * as ReactDOM from 'react-dom/client';
import { Provider as ReduxProvider } from 'react-redux';
import { RouterProvider } from 'react-router-dom';
import { PersistGate } from 'redux-persist/integration/react';
import { createRouter } from './app/routes';
import { persistor, store } from './app/store';
import { config } from './services/config';
import { theme } from './app/theme';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

const router = createRouter();

root.render(
  // <StrictMode>
    <GoogleOAuthProvider clientId={config.googleClientId}>
      <ReduxProvider store={store}>
        <PersistGate loading={null} persistor={persistor}>
          <>
            <ColorModeScript initialColorMode={theme.config.initialColorMode} />
            <ChakraProvider theme={theme}>
              <RouterProvider router={router} />
            </ChakraProvider>
          </>
        </PersistGate>
      </ReduxProvider>
    </GoogleOAuthProvider>
  // </StrictMode>
);
