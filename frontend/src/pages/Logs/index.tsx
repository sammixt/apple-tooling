import {
  Box,
  Button,
  CircularProgress,
  Flex,
  Input,
  Select,
  Text,
  VStack,
} from '@chakra-ui/react';
import { Table } from '../../components/table/table';
import { useEffect, useMemo, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { FileInfo, ItemListQuery } from '../../types';
import { EMPTY_LOGS, useItemListQueryParams } from '../../hooks/query';
import { useListFilesQuery, useLogLevelsQuery } from './store';

const INITIAL_TABLE_STATE: ItemListQuery<FileInfo> = {
  page: 1,
  pageSize: 25,
  sorting: [
    {
      id: 'created_at',
      desc: true,
    },
  ],
  start_date: '', // Add initial empty value for start_date
  end_date: '', // Add initial empty value for end_date
  log_level: '', // Add initial empty value for log_level
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

function Logs() {
  const {
    query,
    setPage,
    setPageSize,
    setSorting,
    setDateFilter,
    setLogLevelFilter,
  } = useItemListQueryParams<FileInfo>(INITIAL_TABLE_STATE);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [logLevel, setlogLevel] = useState(''); // State to hold the selected value
  const [isOpen, setIsOpen] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(false); // State to track loading

  // API call hook using dynamic query
  const {
    data = EMPTY_LOGS,
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
  // Fetch log levels using the query hook
  const { data: logTypes } = useLogLevelsQuery(null);

  const handleModalClose = () => {
    setIsOpen(false);
  };

  const columns = useMemo<ColumnDef<any>[]>(
    () => [
      {
        accessorKey: 'id',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Id
          </Box>
        ),

        cell: (info) => info.getValue(),
        enableSorting: true,
      },
      {
        accessorKey: 'log_message',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Log Message
          </Box>
        ),

        cell: (info) => {
          const [isExpanded, setIsExpanded] = useState(false);
          let logMessage: any = info.getValue();

          // Remove extra spaces (leading, trailing, and multiple spaces between words)
          logMessage = logMessage.trim().replace(/\s+/g, ' ');

          // Split the log message into words
          const words = logMessage.split(' ');

          // Limit the number of words to show initially
          const previewText =
            words.slice(0, 20).join(' ') + (words.length > 20 ? '...' : '');

          // Toggle between the full text and the truncated text
          const handleToggle = () => setIsExpanded(!isExpanded);

          return (
            <div>
              <div style={{}}>{isExpanded ? logMessage : previewText}</div>
              {words.length > 20 && (
                <button
                  onClick={handleToggle}
                  style={{
                    marginTop: '5px',
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  {isExpanded ? 'View Less' : 'View More'}
                </button>
              )}
            </div>
          );
        },
        enableSorting: false,
      },
    ],
    []
  );
  const currentDate = new Date().toISOString().split('T')[0]; // Get the current date in YYYY-MM-DD format
  const minDate = new Date();
  minDate.setFullYear(minDate.getFullYear() - 1); // Subtract 1 year from the current date
  const minDateString = minDate.toISOString().split('T')[0]; // Minimum date in YYYY-MM-DD format

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

    // Use a timeout or delay to ensure state changes happen after the date filter is applied
    setTimeout(() => {
      setIsDataLoading(false); // Hide loader after a short delay
    }, 500); // Adjust the delay as needed (500ms in this case)
  }, [startDate, endDate]);

  useEffect(() => {
    setLogLevelFilter(logLevel);
  }, [logLevel]);

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
        <Text>Filter by Log Level</Text>

        <Select
              placeholder="Select Log Level"
              value={logLevel}
              onChange={handleChange}
              width={{ base: '100%', md: '15%' }} // Full width on small screens
            >
              {logTypes?.logLevels
                ?.slice() // Create a shallow copy to avoid mutating the original array
                .sort((a: string, b: string) => a.localeCompare(b)) // Sort alphabetically
                .map((logType: string) => (
                  <option key={logType} value={logType}>
                    {logType} {/* Render the log type */}
                  </option>
                ))}
            </Select>


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
          data={data?.items}
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
    </Box>
  );
}
export { Logs as Component };
