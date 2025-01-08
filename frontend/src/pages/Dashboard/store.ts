import { createApi } from '@reduxjs/toolkit/query/react';
import { apiBase } from '../../services/api';
import { FileInfo, ItemListQuery, ItemFileListResponse } from '../../types';
import { createQueryBuilder } from '../../services/query-builder';

export const dashboardApi = createApi({
  baseQuery: apiBase,
  reducerPath: 'dashboardApi',
  tagTypes: ['dashboard'],
  endpoints: (builder) => {
    // TODO: update the urls
    const baseURL = '/s3files/';

    return {
      listFiles: builder.query<
        ItemFileListResponse<FileInfo>,
        {
          query: ItemListQuery<FileInfo>;
        }
      >({
        query: ({ query: q }) => {
          const qb = createQueryBuilder(q);
          return `${baseURL}?${qb.query()}`;
        },
        providesTags: [{ type: 'dashboard', id: 'LIST' }],
      }),
    };
  },
});

export const { useListFilesQuery, reducerPath } = dashboardApi;

// https://jsonblob.com/api/1299382526802780160?sort%5B0%5D=file.url%2CDESC&limit=10&page=1&join%5B0%5D=conversations%7C%7Cid%2Cstatus
// https://jsonblob.com/api/1299363698899279872?sort[0]=createdAt%2CDESC&limit=10&page=1&filter[0]=workstream||%24eq||rlfh
// https://jsonblob.com/api/1299363698899279872?sort[0]=file.url%2CASC&limit=10&page=1&s={"workstream"%3A"rlhd"}
