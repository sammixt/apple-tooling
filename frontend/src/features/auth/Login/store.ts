import { createApi } from '@reduxjs/toolkit/query/react';
import { apiBase } from '../../../../src/services/api';

export const loginAuthApi = createApi({
  baseQuery: apiBase,
  reducerPath: 'loginAuthApi',
  tagTypes: ['login'],
  endpoints: (builder) => {
    return {
      googleAuth: builder.mutation({
        query: ({ url }) => ({
          method: 'GET',
          url,  // Ensure this `url` is properly passed in the action
        }),
        invalidatesTags: ['login'],
      }),
    };
  },
});

export const {
  useGoogleAuthMutation,
  reducerPath,
} = loginAuthApi;
