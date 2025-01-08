import { ColumnSort } from '@tanstack/react-table';
import type { QueryFilter, SCondition } from '@dataui/crud-request';

export interface ItemListQuery<T> {
  page: number;
  pageSize: number;
  sorting: ColumnSort[];
  fields?: (keyof T)[] | undefined;
  filters?: QueryFilter[] | undefined;
  search?: SCondition | undefined;
  start_date?: string | undefined;
  end_date?: string | undefined;
  user_name?: string | undefined;
  log_level?: string | undefined;
  workstream?: string | undefined;
  role_id?: number | undefined;

}

export interface ItemListResponse<T> {
  items: T[];
  page: number;
  pageSize: number;
  pageCount: number;
  total: number;
}

export interface ItemFileListResponse<T> {
  s3_files: T[];
  page: number;
  pageSize: number;
  pageCount: number;
  total: number;
}

export interface IdName {
  id: string;
  workstream_id: string;
  name: string;
}
export interface ItemLogsListResponse<T> {
  items: T[];
  page: number;
  pageCount: number;
  pages: number;
  total: number;
}
export type ItemUsersListResponse<T> = {
  users: T[];
  page: number;
  pageCount: number;
  pages: number;
  total: number;
};
