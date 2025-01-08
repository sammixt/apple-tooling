import { createApi } from '@reduxjs/toolkit/query/react';
import { apiBase } from '../../services/api';
import {
  IdName,
  ItemListQuery,
  ItemListResponse,
  UploadedFiles,
} from '../../types';
import { createQueryBuilder } from '../../services/query-builder';

export const uploadApi = createApi({
  baseQuery: apiBase,
  reducerPath: 'uploadApi',
  tagTypes: ['UploadFile', 'Upload'],
  endpoints: (builder) => {
    // TODO: update the urls
    const baseURL = '/processor';

    return {
      uploadedFilesList: builder.query<
        ItemListResponse<UploadedFiles>,
        {
          query: ItemListQuery<UploadedFiles>;
        }
      >({
        query: ({ query: q }) => {
          console.log('q = ', q);
          const qb = createQueryBuilder(q);
          console.log('qb = ', qb.query());
          return `${baseURL}/?${qb.query()}`;
        },
        providesTags: [{ type: 'UploadFile', id: 'UPLOADFILE' }],
      }),
      uploadFile: builder.mutation({
        query: ({ body, query }) => ({
          method: 'POST',
          url: `${baseURL}/?${query}`,
          body: body,
        }),
        invalidatesTags: ['Upload'],
      }),
      getWorkstreams: builder.query<IdName[], null>({
        query: () => {
          return '/processor/workstreams/';
        },
        providesTags: ['UploadFile'],
      }),
      postUploadFile: builder.mutation({
        query: ({ body, url }) => ({
          method: 'POST',
          url: `${baseURL}${url}`,
          body: body,
        }),
        invalidatesTags: ['Upload'],
      }),
      getUploadFile: builder.mutation({
        query: ({ url }) => ({
          method: 'GET',
          url: `${baseURL}${url}`,
        }),
        invalidatesTags: ['Upload'],
      }),
    };
  },
});

export const {
  useUploadedFilesListQuery,
  useUploadFileMutation,
  useGetWorkstreamsQuery,
  usePostUploadFileMutation,
  useGetUploadFileMutation,
  reducerPath,
} = uploadApi;