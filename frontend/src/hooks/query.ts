import { ColumnSort } from '@tanstack/react-table';
import { SetStateAction, useCallback, useState } from 'react';
import { ItemListQuery } from '../types';
import { ComparisonOperator } from '@dataui/crud-request';

export const INITIAL_QUERY = Object.freeze({
  pageSize: 25,
  page: 1,
  sorting: [],
});

export const EMPTY_FILES = Object.freeze({
  s3_files: [],
  total: 0,
  page: 1,
  pageCount: 0,
});
export const EMPTY_LOGS = Object.freeze({
  items: [],
  total: 0,
  page: 1,
  pageCount: 0,
});
export const EMPTY = Object.freeze({
  items: [],
  total: 0,
  page: 1,
  pageCount: 0,
});
export const EMPTY_USERS = Object.freeze({
  users: [],
  total: 0,
  page: 1,
  pageCount: 0,
});
export const EMPTY_ROLES = Object.freeze({
  roles: [],
  total: 0,
  page: 1,
  pageCount: 0,
});
export const EMPTY_ACTIVITY_LOGS = Object.freeze({
  logs: [],
  total: 0,
  page: 1,
  pageCount: 0,
});
export const useItemListQueryParams = <T>(
  initial: ItemListQuery<any> = INITIAL_QUERY
) => {
  const [query, setQuery] = useState<ItemListQuery<any>>(initial);

  return {
    query,
    setPageSize: useCallback((pageSize: number) => {
      setQuery((query) => ({
        ...query,
        pageSize,
        page: 1,
      }));
    }, []),

    setPage: useCallback((page: number) => {
      setQuery((query) => ({
        ...query,
        page,
      }));
    }, []),

    setDateFilter: useCallback((start_date: string, end_date: string) => {
      setQuery((query) => ({
        ...query,
        start_date: start_date || undefined,
        end_date: end_date || undefined,
      }));
    }, []),

    setLogLevelFilter: useCallback((log_level: string) => {
      setQuery((query) => ({
        ...query,
        log_level,
      }));
    }, []),

    setUserNameFilter: useCallback((user_name: string) => {
      setQuery((query) => ({
        ...query,
        user_name,
      }));
    }, []),

    setWorkstreamFilter: useCallback((workstream: string) => {
      setQuery((query) => ({
        ...query,
        workstream,
      }));
    }, []),

    setRoleIdFilter: useCallback((role_id: any) => {
      setQuery((query) => ({
        ...query,
        role_id,
      }));
    }, []),

    setSorting: useCallback((sorting: SetStateAction<ColumnSort[]>) => {
      setQuery((query) => ({
        ...query,
        sorting:
          typeof sorting === 'function' ? sorting(query.sorting) : sorting,
        page: 1,
      }));
    }, []),

    reset: useCallback(() => setQuery(initial), [initial]),
  };
};
