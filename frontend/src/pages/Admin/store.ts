import { createApi } from '@reduxjs/toolkit/query/react';
import { apiBase } from '../../services/api';
import { UsersInfo, ItemListQuery, ItemUsersListResponse, RoleInfo } from '../../types';
import { createQueryBuilder } from '../../services/query-builder';

export const adminApi = createApi({
  baseQuery: apiBase,
  reducerPath: 'adminApi',
  tagTypes: ['admin', 'user','roles'], // Added 'user' tag for more granular caching
  endpoints: (builder) => {
    const baseURL = '/users/';

    return {
      // List Users: Fetch all users with dynamic query parameters
      ListUsers: builder.query<ItemUsersListResponse<UsersInfo>, { query: ItemListQuery<UsersInfo> }>({
        query: ({ query: q }) => {
          const qb = createQueryBuilder(q); 

          const queryString = qb.query();
  
          return `${baseURL}?${queryString}`;
        },
        providesTags: [{ type: 'user', id: 'LIST' }], // Cache invalidation tag
      }),

      // Add User: Create a new user
      AddUser: builder.mutation<
        UsersInfo,
        { body: UsersInfo }
      >({
        query: ({ body }) => ({
          method: 'POST',
          url: baseURL,
          body,
        }),
      }),

      // Update User: Update existing user dynamically based on `user_id`
      UpdateUser: builder.mutation<
        RoleInfo,
        { user_id: string | number; body: Partial<RoleInfo> }
      >({
        query: ({ user_id, body }) => ({
          method: 'PUT',
          url: `${baseURL}${user_id}`, 
          body,
        }),
      }),
        // Update User: Update existing user dynamically based on `user_id`
        UpdateUserStatus: builder.mutation<
        RoleInfo,
        { user_id: string | number; body: Partial<RoleInfo> }
      >({
        query: ({ user_id, body }) => ({
          method: 'PUT',
          url: `${baseURL}${user_id}/update-status`, 
          body,
        }),
      }),
        // List Users: Fetch all users with dynamic query parameters
        ListRoles: builder.query<
        ItemUsersListResponse<RoleInfo>,
        { query: ItemListQuery<RoleInfo> }
      >({
        query: ({ query: q }) => {
          const qb = createQueryBuilder(q);
          return `${'/roles/'}?${qb.query()}`;
        },
        providesTags: [{ type: 'roles', id: 'LIST' }], // Use tag for cache invalidation
      }),

      // Add User: Create a new user
       AddRole: builder.mutation<
        RoleInfo,
        { body: RoleInfo }
      >({
        query: ({ body }) => ({
          method: 'POST',
          url: `/roles/`,
          body,
        }),
      }),

      // Update User: Update existing user dynamically based on `user_id`
      UpdateRole: builder.mutation<
        RoleInfo,
        { roleId: string | number; body: Partial<RoleInfo> }
      >({
        query: ({ roleId, body }) => ({
          method: 'PUT',
          url: `/roles/${roleId}`,
          body,
        }),
      }),
        // Update User: Update existing user dynamically based on `user_id`
        DeleteRole: builder.mutation<
        RoleInfo,
        { roleId: string | number; body: Partial<RoleInfo> }
      >({
        query: ({ roleId, body }) => ({
          method: 'DELETE',
          url: `roles/${roleId}`, // Inject roleId into the URL
          body,
        }),
      }),
      // List Users: Fetch all users with dynamic query parameters
      GeteRoleList: builder.query<ItemUsersListResponse<UsersInfo>, { query: ItemListQuery<UsersInfo> }>({
        query: ({ query: q }) => { 
          return `/roles/role-list/all`;
        },
        providesTags: [{ type: 'user', id: 'LIST' }], // Cache invalidation tag
      }),
    };
  },
});

export const {
  useListUsersQuery,
  useAddUserMutation,
  useUpdateUserMutation,
  useUpdateUserStatusMutation,
  useListRolesQuery,
  useAddRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
  useGeteRoleListQuery,
  reducerPath,
} = adminApi;
