import { useMemo, useCallback } from 'react';

const PAGE_SIZE_KEY = 'persist:pageSize';

export const usePersistPageSize = (
  id: string | undefined,
  pageSize: number,
  setPageSize: (value: number) => void
) => {
  const pageSizePersisted = useMemo(() => {
    try {
      if (id) {
        const pageSizeFromLocalStorage = localStorage.getItem(PAGE_SIZE_KEY);
        if (pageSizeFromLocalStorage) {
          const pageSizeParsed: Record<string, number> = JSON.parse(
            pageSizeFromLocalStorage
          );
          if (pageSizeParsed[id]) {
            setPageSize(pageSizeParsed[id]);
            return pageSizeParsed[id];
          }
        }
      }
      return pageSize;
    } catch (e) {
      return pageSize;
    }
  }, [id, pageSize, setPageSize]);

  const onChangeLimit = useCallback(
    (value: number) => {
      try {
        if (id) {
          const pageSizeFromLocalStorage = localStorage.getItem(PAGE_SIZE_KEY);
          if (pageSizeFromLocalStorage) {
            const pageSizeParsed: Record<string, number> = JSON.parse(
              pageSizeFromLocalStorage
            );
            pageSizeParsed[id] = value;
            localStorage.setItem(PAGE_SIZE_KEY, JSON.stringify(pageSizeParsed));
          } else {
            localStorage.setItem(
              PAGE_SIZE_KEY,
              JSON.stringify({ [id]: value })
            );
          }
        }
        setPageSize(value);
      } catch (e) {
        setPageSize(value);
      }
    },
    [id, setPageSize]
  );

  return useMemo(
    () => ({
      pageSize: pageSizePersisted,
      setPageSize: onChangeLimit,
    }),
    [onChangeLimit, pageSizePersisted]
  );
};
