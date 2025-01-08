import { createApi } from '@reduxjs/toolkit/query/react';
import { apiBase } from '../../services/api';
import { FileInfo, ItemListQuery, ItemLogsListResponse ,LogRow} from '../../types';
import { createQueryBuilder } from '../../services/query-builder';

export const logsApi = createApi({
  baseQuery: apiBase,
  reducerPath: 'logApi', // Fixed typo in 'logsAPi'
  tagTypes: ['logs', 'LogLevels'], // Ensure 'LogLevels' is included here
  endpoints: (builder) => {
    const baseURL = '/logs/';

    return {
      listFiles: builder.query<
        ItemLogsListResponse<LogRow>,
        {
          query: ItemListQuery<LogRow>;
        }
      >({
        query: ({ query: q }) => {
          const qb = createQueryBuilder(q);
          return `${baseURL}?${qb.query()}`;
        },
        providesTags: [{ type: 'logs', id: 'LIST' }], // Fixed tag type consistency
      }),
      logLevels: builder.query<string[], null>({ // Specify the expected response type
        query: () => '/log-levels',
        providesTags: ['LogLevels'],
      }),
    };
  },
});

export const { useListFilesQuery, useLogLevelsQuery , reducerPath} = logsApi;
