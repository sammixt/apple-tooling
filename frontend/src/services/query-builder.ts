import {
  RequestQueryBuilder,
  type QuerySortOperator,
} from '@dataui/crud-request';
import { ItemListQuery } from '../types';

export function createQueryBuilder<T>(
  query: ItemListQuery<T>
): RequestQueryBuilder {
  const qb = RequestQueryBuilder.create()
    .sortBy(
      query.sorting.map((s) => ({
        field: s.id,
        order: (s.desc ? 'DESC' : 'ASC') as QuerySortOperator,
      }))
    )
    .setLimit(query.pageSize && query.pageSize <= 10 ? 25 : query.pageSize)
    .setPage(query.page);

  // Handle field selection
  if (query.fields) {
    qb.select(query.fields.map((field) => field.toString()));
  }

  // Apply filters
  if (query.filters) {
    for (const filter of query.filters) {
      qb.setFilter(filter);
    }
  }

  // Apply search
  if (query.search) {
    qb.search(query.search);
  }

  if (query.sorting && query.sorting.length > 0) {
    const sortField = query.sorting[0];
    const sortValue = `${sortField.id},${sortField.desc ? 'DESC' : 'ASC'}`;
    qb.queryObject = {
      ...qb.queryObject,
      sort: sortValue,
    };
  }

  // Add date filters manually
  if (query.start_date) {
    qb.queryObject = {
      ...qb.queryObject,
      start_date: query.start_date,
    };
  }

  if (query.end_date) {
    qb.queryObject = {
      ...qb.queryObject,
      end_date: query.end_date,
    };
  }

  // Add custom log level
  if (query.log_level) {
    qb.queryObject = {
      ...qb.queryObject,
      log_level: query.log_level,
    };
  }

  // Add custom user name
  if (query.user_name) {
    qb.queryObject = {
      ...qb.queryObject,
      user_name: query.user_name,
    };
  }

  // Add workstream filter if present
  if (query.workstream) {
    qb.queryObject = {
      ...qb.queryObject,
      workstream: query.workstream,
    };
  }

  // Add role_id filter if present
  if (query.role_id) {
    qb.queryObject = {
      ...qb.queryObject,
      role_id: query.role_id,
    };
  }

  return qb;
}
