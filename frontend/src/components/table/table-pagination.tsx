import {
  Flex,
  IconButton,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Select,
  Text,
  Tooltip,
} from '@chakra-ui/react';
import { useCallback, type ChangeEvent, type Dispatch } from 'react';
import {
  MdKeyboardArrowLeft,
  MdKeyboardArrowRight,
  MdKeyboardDoubleArrowLeft,
  MdKeyboardDoubleArrowRight,
} from 'react-icons/md';

export interface TablePaginationProps {
  page: number;
  pageCount: number;
  onChangePage: Dispatch<number>;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  limit: number;
  limitOptions?: number[];
  onChangeLimit: Dispatch<number>;
  // optional for backward compatibility
  total?: number;
}

const DEFAULT_LIMIT_OPTIONS = [25, 50, 75, 100];

export function TablePagination({
  page,
  pageCount,
  onChangePage,
  hasNextPage,
  hasPreviousPage,
  limit,
  limitOptions = DEFAULT_LIMIT_OPTIONS,
  total,
  onChangeLimit,
}: TablePaginationProps) {
  const goFirstPage = useCallback(() => {
    onChangePage(1);
  }, [onChangePage]);
  const goPreviousPage = useCallback(() => {
    onChangePage(page - 1);
  }, [onChangePage, page]);
  const goNextPage = useCallback(() => {
    onChangePage(page + 1);
  }, [onChangePage, page]);
  const goLastPage = useCallback(() => {
    onChangePage(pageCount);
  }, [onChangePage, pageCount]);

  const goToPage = useCallback(
    (page: string | number) => {
      onChangePage(Number(page));
    },
    [onChangePage]
  );

  const onPageSizeSelectorChange = useCallback(
    (e: ChangeEvent<HTMLSelectElement>) => {
      onChangeLimit(Number(e.target.value));
    },
    [onChangeLimit]
  );

  return (
    <Flex justifyContent="space-between" p={4}>
      <Flex>
        <Tooltip label="First Page">
          <IconButton
            aria-label="First Page"
            icon={<MdKeyboardDoubleArrowLeft />}
            isDisabled={!hasPreviousPage}
            onClick={goFirstPage}
            mr={4}
          />
        </Tooltip>
        <Tooltip label="Previous Page">
          <IconButton
            aria-label="Previous Page"
            icon={<MdKeyboardArrowLeft />}
            isDisabled={!hasPreviousPage}
            onClick={goPreviousPage}
          />
        </Tooltip>
      </Flex>

      <Flex alignItems="center" pl={8} pr={8}>
        <Text pr={8}>
          Page{' '}
          <Text as="span" fontWeight="bold">
            {page}
          </Text>{' '}
          of{' '}
          <Text as="span" fontWeight={'bold'}>
            {Math.max(pageCount, 1)}
          </Text>
        </Text>
        <Text>Go to page:</Text>{' '}
        <NumberInput
          ml={2}
          mr={8}
          w={28}
          min={1}
          max={Math.max(pageCount, 1)}
          onChange={goToPage}
          value={page}
        >
          <NumberInputField />
          <NumberInputStepper>
            <NumberIncrementStepper />
            <NumberDecrementStepper />
          </NumberInputStepper>
        </NumberInput>
        <Select
          w={32 + (total ? (total > 1000 ? 16 : 8) : 0)}
          value={limit}
          onChange={onPageSizeSelectorChange}
        >
          {limitOptions.map((pageSize) => (
            <option key={pageSize} value={pageSize}>
              Show {pageSize} {total ? `of ${total}` : ''}
            </option>
          ))}
        </Select>
      </Flex>

      <Flex>
        <Tooltip label="Next Page">
          <IconButton
            aria-label="Next Page"
            icon={<MdKeyboardArrowRight />}
            isDisabled={!hasNextPage}
            onClick={goNextPage}
          />
        </Tooltip>
        <Tooltip label="Last Page">
          <IconButton
            aria-label="Last Page"
            icon={<MdKeyboardDoubleArrowRight />}
            isDisabled={!hasNextPage}
            onClick={goLastPage}
            ml={4}
          />
        </Tooltip>
      </Flex>
    </Flex>
  );
}

export default TablePagination;
