import { createApi } from '@reduxjs/toolkit/query/react';
import { apiBase } from '../../services/api';
import { FileInfo, ItemListQuery, ItemFileListResponse } from '../../types';
import { createQueryBuilder } from '../../services/query-builder';

export const newDashboardApi = createApi({
  baseQuery: apiBase,
  reducerPath: 'newDashboardApi',
  tagTypes: ['newDashboard', 'workstream'], // Updated tagTypes for consistency
  endpoints: (builder) => {
    const baseURL = '/s3files/';

    return {
      // Query to list files
      listFiles: builder.query<
        ItemFileListResponse<FileInfo>,
        { query: ItemListQuery<FileInfo> }
      >({
        query: ({ query: q }) => {
          const qb = createQueryBuilder(q);
          return `${baseURL}?${qb.query()}`;
        },
        providesTags: [{ type: 'newDashboard', id: 'LIST' }],
      }),

      // Query to fetch workstreams
      getWorkstreams: builder.query<any, null>({
        query: () => '/s3files-workstream/',
        providesTags: ['workstream'],
      }),

      // Mutation to fetch data by ID
      getViewDataById: builder.mutation<any, { id: string }>({
        query: ({ id }) => ({
          url: `/s3files/${id}/get-all`,
          method: 'GET', // Adjust method if needed (e.g., POST, PUT)
        }),
      }),
    };
  },
});

// Export hooks and reducerPath
export const { useListFilesQuery, useGetWorkstreamsQuery,useGetViewDataByIdMutation,reducerPath } = newDashboardApi;
