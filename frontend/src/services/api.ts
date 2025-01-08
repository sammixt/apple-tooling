import { fetchBaseQuery } from '@reduxjs/toolkit/query';
import { RootState } from '../app/store';
import { config } from './config';

function inferBaseUrl(): string {
  return config.apiUrl;
}

export const apiBase = fetchBaseQuery({
  baseUrl: inferBaseUrl(),
  prepareHeaders(headers, { getState }) {
    // Do not use selector to avoid cyclic dependency
    const token = (getState() as RootState).auth.token;

    console.log('token------');
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  },
  credentials: 'include',
});
