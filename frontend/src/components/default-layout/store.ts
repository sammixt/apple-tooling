import { createApi } from '@reduxjs/toolkit/query/react';
import { apiBase } from '../../services/api';

// Define the types of your configuration response
interface ConfigResponse {
  configuration: {
    enable_penguin_s3_upload: boolean;
    enable_turing_s3_upload: boolean;
    upload_date_restriction:boolean;
  };
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  email: string;
}

// Define the type for the configuration update payload
interface ConfigUpdatePayload {
  enable_penguin_s3_upload: boolean;
  enable_turing_s3_upload: boolean;
}

export const configureApi = createApi({
  baseQuery: apiBase,
  reducerPath: 'configApi',
  tagTypes: ['config'],
  endpoints: (builder) => ({
    // Define the query to fetch the configuration data
    getConfig: builder.query<ConfigResponse, null>({
      query: () => '/config',
      providesTags: ['config'],
    }),
    getToken: builder.query<TokenResponse, null>({
      query: () => '/processor/token/',
    }),

    // Define the mutation to update the configuration
    updateConfig: builder.mutation<void, ConfigUpdatePayload>({
      query: (config) => ({
        url: '/config',
        method: 'POST',
        body: config,
      }),
      // Invalidates the cache for 'config' so it will refetch the latest configuration
      invalidatesTags: ['config'],
    }),
  }),
});

// Export hooks and the reducer
export const { useGetConfigQuery,useGetTokenQuery, useUpdateConfigMutation,reducerPath } = configureApi;
