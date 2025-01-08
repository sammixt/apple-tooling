import {
  Box,
  Button,
  CircularProgress,
  Flex,
  IconButton,
  Input,
  Select,
  Text,
  VStack,
} from '@chakra-ui/react';
import { Table } from '../../components/table/table';
import { useEffect, useMemo, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { FileInfo, ItemListQuery } from '../../types';
import { EMPTY_ACTIVITY_LOGS, useItemListQueryParams } from '../../hooks/query';
import { useListFilesQuery } from './store';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from '@chakra-ui/react';
import { ViewIcon } from '@chakra-ui/icons';
import ReactJson from 'react-json-view';
import CustomModal from '../../components/modal/modal';

const INITIAL_TABLE_STATE: ItemListQuery<FileInfo> = {
  page: 1,
  pageSize: 25,
  sorting: [
    {
      id: 'timestamp',
      desc: true,
    },
  ],
  start_date: '', // Add initial empty value for start_date
  end_date: '', // Add initial empty value for end_date
  log_level: '', // Add initial empty value for log_level
  user_name: '', // Add initial empty value for user_name
};
// Define a loader component
const Loader = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    height="100vh"
  >
    <CircularProgress isIndeterminate color="teal" />
  </Box>
);

function ActivityLogs() {
  const {
    query,
    setPage,
    setPageSize,
    setSorting,
    setDateFilter,
    setUserNameFilter,
  } = useItemListQueryParams<FileInfo>(INITIAL_TABLE_STATE);
  const [userName, setUserName] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [logLevel, setlogLevel] = useState(''); // State to hold the selected value
  const [isOpen, setIsOpen] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(false); // State to track loading

  // API call hook using dynamic query
  const {
    data = EMPTY_ACTIVITY_LOGS,
    isLoading,
    isError,
    error,
    refetch,
  } = useListFilesQuery(
    { query },
    {
      refetchOnMountOrArgChange: true,
    }
  );
  const DetailsModal = ({ isOpen, onClose, details, isLoading }) => (
    <CustomModal onClose={onClose} isOpen={isOpen} header="Details">
      {isLoading ? (
        <VStack justifyContent="center" height="42vh">
          <CircularProgress isIndeterminate size="120px" />
        </VStack>
      ) : (
        <ReactJson enableClipboard={false} src={details} />
      )}
    </CustomModal>
  );

  const [modalDetails, setModalDetails] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenModal = (details) => {
    setModalDetails(details);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalDetails(null);
    setIsModalOpen(false);
  };

  const columns = useMemo<ColumnDef<any>[]>(
    () => [
      {
        accessorKey: 'user',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            User Name
          </Box>
        ),
        cell: (info) => {
          const value = info.getValue();
          return value?.name || 'Unknown';
        },
        enableSorting: false,
      },
      {
        accessorKey: 'user',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            User Email
          </Box>
        ),

        cell: (info) => {
          const value = info.getValue();
          return value?.email || 'Unknown';
        },
        enableSorting: false,
      },
      {
        accessorKey: 'action',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Action
          </Box>
        ),
        cell: (info) => info.getValue(),
        enableSorting: false,
      },
      {
        accessorKey: 'details',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Details
          </Box>
        ),
        cell: (info) => {
          const value = info.getValue();
          return (
            <IconButton
              aria-label="View Details"
              icon={<ViewIcon />}
              // colorScheme="teal"
              size="sm"
              onClick={() => handleOpenModal(value)}
            />
          );
        },
        enableSorting: false,
      },
      {
        accessorKey: 'resource',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Resource
          </Box>
        ),
        cell: (info) => info.getValue(),
        enableSorting: false,
      },
      {
        accessorKey: 'timestamp',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Timestamp
          </Box>
        ),
        accessorFn: (row) => {
          const temp = new Date(row.timestamp);
          return temp.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
          });
        },
        enableSorting: true,
      },
    ],
    []
  );
  const currentDate = new Date().toISOString().split('T')[0]; // Get the current date in YYYY-MM-DD format
  const minDate = new Date();
  minDate.setFullYear(minDate.getFullYear() - 1); // Subtract 1 year from the current date
  const minDateString = minDate.toISOString().split('T')[0]; // Minimum date in YYYY-MM-DD format
  
  // Handle User Name change
  const handleUserNameChange = (e: any) => {
    const newUserName = e.target.value;
    if (!newUserName) {
      setUserName('');
    }
    else setUserName(newUserName)
  };

  // Handle Start Date change
  const handleStartDateChange = (e: any) => {
    const newStartDate = e.target.value;
    if (newStartDate <= currentDate) {
      setStartDate(newStartDate);
    }
  };
  
  // Handle End Date change
  const handleEndDateChange = (e: any) => {
    const newEndDate = e.target.value;
    // End date can be the same as start date but should not be earlier than it
    if (newEndDate >= startDate && newEndDate <= currentDate) {
      setEndDate(newEndDate);
    }
  };
  
  // Track changes to startDate or endDate
  useEffect(() => {
    setIsDataLoading(true); // Show loader when dates change
    
    // Set date filter asynchronously
    setDateFilter(startDate, endDate);

    // set username filter
    setUserNameFilter(userName)
  
    // Use a timeout or delay to ensure state changes happen after the date filter is applied
    setTimeout(() => {
      setIsDataLoading(false); // Hide loader after a short delay
    }, 500); // Adjust the delay as needed (500ms in this case)
  }, [startDate, endDate, userName]);
  
  
  
  const handleChange = (event: any) => {
    setlogLevel(event.target.value);
  };
  return (
    <Box p={4}>
     <Flex
        p={{ base: '10px', md: '10px 0' }} // Adjust padding for small screens
        alignItems="center"
        gap={{ base: '10px', md: '20px' }} // Smaller gap for smaller screens
        direction={{ base: 'column', md: 'row' }} // Stack items on small screens
        w="100%" // Full width container
      >

        <Input
          type="text"
          border="1px solid lightgray"
          width={{ base: '100%', md: '20%' }} // Full width on small screens
          name="user_name"
          placeholder="Enter User Name"
          value={userName}
          onChange={handleUserNameChange}
        />

        <Text>Start Date</Text>

        <Input
          type="date"
          border="1px solid lightgray"
          width={{ base: '100%', md: '20%' }} // Full width on small screens
          name="start_date"
          value={startDate}
          onChange={handleStartDateChange}
          max={endDate || currentDate} // Prevent setting start date after the end date
          min={minDateString} // Minimum date is 1 year before today
        />

        <Text>End Date</Text>

        <Input
          type="date"
          border="1px solid lightgray"
          width={{ base: '100%', md: '20%' }} // Full width on small screens
          name="end_date"
          value={endDate}
          onChange={handleEndDateChange}
          max={currentDate} // Prevent setting end date after today
          min={minDateString} // Minimum date is 1 year before today
        />

        {/* Clear Filters Button */}
        <Button
          onClick={() => {
            setUserName('');
            setlogLevel('');
            setStartDate('');
            setEndDate('');
          }}
          variant="outline"
          colorScheme="blue"
          width={{ base: '100%', md: 'auto' }} // Button full width on small screens
        >
          Clear Filters
        </Button>
      </Flex>
      {isDataLoading ? (
        <Loader />
      ) : (
        <Table
          id="fileList"
          columns={columns}
          data={data?.logs}
          isLoading={isLoading}
          pageCount={data?.pageCount}
          page={query.page}
          pageSize={query.pageSize}
          sorting={query.sorting}
          setPage={setPage}
          setPageSize={setPageSize}
          setSorting={setSorting}
        />
      )}
      <>
        {/** Your Table Component Here **/}
        <DetailsModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          details={modalDetails}
        />
      </>
    </Box>
  );
}
export { ActivityLogs as Component };
