import {
  Box,
  Table as ChakraTable,
  HStack,
  Spinner,
  TableContainer,
  TableRowProps,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  type TableProps as ChakraTableProps,
} from '@chakra-ui/react';
import {
  ColumnDef,
  Row,
  SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type TableOptions,
} from '@tanstack/react-table';
import {
  useEffect,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react';
import LoadingOverlay from 'react-loading-overlay-ts';
import { TablePagination, TablePaginationProps } from './table-pagination';
import { TableSorter } from './table-sorter';
import { usePersistPageSize } from './usePersistPageSize';
import _ from 'lodash';

const NONE = {};

export interface TableProps<T> extends Omit<ChakraTableProps, 'children'> {
  id?: string;
  className?: string;
  // Data display
  data: T[];
  columns: ColumnDef<T, unknown>[];
  isLoading: boolean;
  onTableInstanceChange?: ((rows: Row<T>[]) => void) | undefined;

  // Pagination
  hasPagination?: boolean;
  pageCount: number;
  page: number;
  pageSize: number;
  total?: number;
  setPage: Dispatch<number>;
  setPageSize: Dispatch<number>;
  manualPagination?: boolean;

  // Sorting
  sorting?: SortingState;
  setSorting?: Dispatch<SetStateAction<SortingState>>;
  manualSorting?: boolean;

  // Table overrides
  tableProps?: Omit<ChakraTableProps, 'children'>;

  // UI ad decoration
  emptyElement?: ReactNode;
  getRowProps?: (
    row: Row<T>,
    index: number
  ) => Omit<TableRowProps, 'children'> | undefined;
}

export function Table<T>({
  id,
  className,

  columns,
  tableProps,

  hasPagination = true,
  page,
  pageSize: pageSizeState,
  pageCount,
  total,
  setPage,
  setPageSize,
  manualPagination = true,

  data,
  isLoading,
  onTableInstanceChange,

  sorting,
  setSorting,
  manualSorting = true,

  emptyElement,
  getRowProps,
}: TableProps<T>) {
  const { pageSize, setPageSize: onChangeLimit } = usePersistPageSize(
    id,
    pageSizeState,
    setPageSize
  );
  const tableOptions: TableOptions<T> = {
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),

    manualSorting,
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),

    manualPagination,
    pageCount,
    getPaginationRowModel: getPaginationRowModel(),

    state: {
      pagination: {
        pageIndex: page - 1,
        pageSize,
      },
      sorting: sorting?.length
        ? sorting
        : [
            {
              id: 'updated_at', // This should match the accessorKey of your column
              desc: true, 
            },
            {
              id: 'created_at', // This should match the accessorKey of your column
              desc: true, 
            },
            {
              id: 'timestamp', // This should match the accessorKey of your column
              desc: true, 
            },
          ], // Default sorting state set to 'desc' for the `updated_at` column
    },

    getFilteredRowModel: getFilteredRowModel(),
    enableSortingRemoval: false,
  };

  const table = useReactTable<T>(tableOptions);

  const paginationProps: TablePaginationProps = {
    page,
    pageCount: manualPagination ? pageCount : table.getPageCount(),
    onChangePage: setPage,
    limit: pageSize,
    onChangeLimit,
    hasNextPage: table.getCanNextPage(),
    hasPreviousPage: table.getCanPreviousPage(),
    total,
  };

  const shouldRenderEmpty = !isLoading && !data?.length && !!emptyElement;

  const rows = table.getRowModel().rows;

  const filteredRows = table.getFilteredRowModel().rows;

  useEffect(() => {
    if (onTableInstanceChange) onTableInstanceChange(filteredRows);
  }, [filteredRows.length, onTableInstanceChange]);

  // Function to convert string to camelCase
  const toCamelCase = (str: any) => {
    return str
      .toLowerCase()
      .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr: any) => chr.toUpperCase());
  };

  // Determine if a scrollbar should be added (when there are more than 10 rows)
  const tableContainerStyle = {
    height: 'calc(100vh - 150px)', // Adjust this height based on the header and other elements
    overflowY: 'auto',
  };

  return (
    <LoadingOverlay active={isLoading} spinner={<Spinner />}>
      <TableContainer id={id} style={tableContainerStyle}>
        <ChakraTable
          variant="striped"
          whiteSpace={'wrap'}
          {...tableProps}
          className={className}
          border="1px solid lightgrey"
        >
       <Thead bg="gray.300">
        {table.getHeaderGroups().map((headerGroup) => (
          <Tr key={headerGroup.id}>
            {headerGroup.headers.map((header: any) => (
              <Th
                key={header.id}
                colSpan={header.colSpan}
                onClick={header.column.getToggleSortingHandler()}
                width={header.column.columnDef.meta?.width || '50px'}
                fontWeight="bold"
                {...header.column.columnDef.meta}
              >
                <HStack gap={0}>
                  <span className="headerText">
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </span>

                  {!header.isPlaceholder && header.column.getCanSort() && (
                    <TableSorter direction={header.column.getIsSorted()} />
                  )}
                </HStack>
              </Th>
            ))}
          </Tr>
        ))}
      </Thead>


          <Tbody>
            {rows.length === 0  && !isLoading? (
              <Tr>
                <Td colSpan="100%" style={{ textAlign: 'center', padding: '20px 0' }}>
                  <Box style={{ fontWeight: 'bold' }}>Data is not available</Box>
                </Td>
              </Tr>
            ) : (
              rows.map((row, rowIndex) => {
                const rowProps = getRowProps?.(row, rowIndex) ?? NONE;
                const rowBgColor = 'white'; // Alternating row colors

                return (
                  <Tr key={row.id} {...rowProps} bg={rowBgColor}>
                    {row.getVisibleCells().map((cell) => (
                      <Td key={cell.id} {...cell.column.columnDef.meta}>
                        <Box className="tbodyText">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </Box>
                      </Td>
                    ))}
                  </Tr>
                );
              })
            )}
          </Tbody>

          {shouldRenderEmpty && (
            <Tbody>
              <Tr>
                <Td colSpan={columns && columns.length}>{emptyElement}</Td>
              </Tr>
            </Tbody>
          )}
        </ChakraTable>
      </TableContainer>
      {hasPagination && <TablePagination {...paginationProps} />}
    </LoadingOverlay>
  );
}

export default Table;
