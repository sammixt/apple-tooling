import { type SortDirection } from '@tanstack/react-table';
import { Text, Icon } from '@chakra-ui/react';
import { MdArrowDownward, MdArrowUpward } from 'react-icons/md';
import { ReactNode } from 'react';
export interface TableSorterProps {
  direction: false | SortDirection;
}

const ICONS: Record<SortDirection | 'false', null | ReactNode> = {
  false: null,
  asc: <Icon as={MdArrowUpward} fontSize="1em" />,
  desc: <Icon as={MdArrowDownward} fontSize={12} />,
};

export function TableSorter({ direction }: TableSorterProps) {
  return (
    <Text as="span" ml={4}>
      {ICONS[direction || 'false']}
    </Text>
  );
}
