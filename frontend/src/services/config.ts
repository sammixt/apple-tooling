declare global {
  interface Window {
    env?: Partial<{
      VITE_API_HOST: string;
      VITE_GOOGLE_CLIENT_ID: string;
      VITE_GOOGLE_REDIRECT_URL: string;
      VITE_CLIENT_NAME: string;
    }>;
  }
}

class Configuration {
  get apiUrl(): string {
    return (
      window.env?.VITE_API_HOST ??
      (import.meta.env.VITE_API_HOST ||
        'https://penguin-dashboard.turing.com/api')
    );
  }

  get googleClientId(): string {
    return (
      window.env?.VITE_GOOGLE_CLIENT_ID ??
      (import.meta.env.VITE_GOOGLE_CLIENT_ID ||
        '549557403268-q5qdc6v4r5k8btg6hstleu3jviiapgnf.apps.googleusercontent.com')
    );
  }

  get googleRedirectUrl(): string | undefined {
    return (
      window.env?.VITE_GOOGLE_REDIRECT_URL ??
      (import.meta.env.VITE_GOOGLE_REDIRECT_URL ||
        'https://www.googleapis.com/oauth2/v1/userinfo')
    );
  }
}

export const config = new Configuration();
