import {
  Box,
  Button,
  CircularProgress,
  Flex,
  Input,
  Text,
  VStack,
  Tooltip,
  Badge,
  IconButton,
  ModalFooter,
  Select,
  useToast,
} from '@chakra-ui/react';
import { Table } from '../../components/table/table';
import { useEffect, useMemo, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { CopyIcon, DownloadIcon, ViewIcon } from '@chakra-ui/icons';
import { FaDownload } from 'react-icons/fa';
import ReactJson from 'react-json-view';
import CustomModal from '../../components/modal/modal';
import { FileInfo, ItemListQuery } from '../../types';
import { EMPTY_FILES, useItemListQueryParams } from '../../hooks/query';
import {
  useListFilesQuery,
  useGetWorkstreamsQuery,
  useGetViewDataByIdMutation,
} from './store';
import { config } from '../../services/config';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
} from '@chakra-ui/react';

const INITIAL_TABLE_STATE: ItemListQuery<FileInfo> = {
  page: 1,
  pageSize: 25,
  sorting: [{ id: 'updated_at', desc: true }],
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
function Dashboard() {
  const {
    query,
    setPage,
    setPageSize,
    setSorting,
    setDateFilter,
    setWorkstreamFilter,
    setSearch,
  } = useItemListQueryParams<FileInfo>(INITIAL_TABLE_STATE);
  const [workstream, setWorkStream] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [fileData, setFileData] = useState<any>();
  const [fileContentLoading, setFileContentLoading] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(false); // State to track loading

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const {
    data = EMPTY_FILES,
    isLoading,
    isError,
    error,
    refetch,
  } = useListFilesQuery({ query }, { refetchOnMountOrArgChange: true });
  const toast = useToast();

  const handleModalClose = () => {
    setIsOpen(false);
  };
  const { data: workstreams = [] } = useGetWorkstreamsQuery(null);
  const [getViewDataById] = useGetViewDataByIdMutation();

  const handleViewClick = async (id, name) => {
    try {
      toast({
        status: 'success',
        isClosable: true,
        position: 'top',
        duration: 5000,
        title: 'File started download',
        description: 'Downloading the file will take time.',
      });

      // Fetch file content via API request
      // const res = await axios.get(`${config.apiUrl}/s3files/${id}/get-all`);
      const res = await getViewDataById({
        id, // Example ID
      }).unwrap();
      const url = `/s3files/${id}/get-all`;

      const fileContent = res?.file_content?.content;

      if (!fileContent) {
        throw new Error('File content is empty or not available.');
      }

      // Convert file content to a JSON string
      const json = JSON.stringify(fileContent, null, 2);

      // Create a Blob from the JSON string
      const blob = new Blob([json], { type: 'application/json' });

      // Create a link element to trigger the download
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${name}.json`; // Include ID in filename

      // Programmatically trigger the download
      link.click();

      // Clean up URL object to free resources
      URL.revokeObjectURL(link.href);
    } catch (e: any) {
      setFileData({});
      toast({
        status: 'error',
        isClosable: true,
        position: 'top',
        duration: 5000,
        title: 'Error',
        description: 'Something went wrong',
      });
      console.error('Error fetching or downloading file:', e.message);
    } finally {
      setFileContentLoading(false);
    }
  };

  const handleCopy = (url: string) => {
    navigator.clipboard.writeText(url);
    // alert('URL copied to clipboard!');
    toast({
      status: 'success',
      isClosable: true,
      position: 'top',
      duration: 5000,
      title: 'Copied',
      description: 'URL copied to clipboard!',
    });
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
            Action
          </Box>
        ),
        cell: (info) => {
          // Fetch stored user permissions
          const storedUserPermissions =
            JSON.parse(localStorage.getItem('userPermissions')) || {};

          return (
            <Tooltip label="Download Json File">
              <IconButton
                key={`${info.row.original.updated_at}-${info.row.original.workstream}`} // Ensure unique key
                icon={<FaDownload />}
                variant="ghost"
                colorScheme="cyan"
                onClick={() =>
                  handleViewClick(
                    info.getValue(),
                    `${info.row.original.updated_at}-${info.row.original.workstream}`
                  )
                }
                aria-label="Download File"
                isDisabled={!storedUserPermissions['download_from_s3']} // Disable the button if permission is missing
              />
            </Tooltip>
          );
        },
        meta: {
          width: '20px', // Define the width here (can be dynamic as needed)
        },
        enableSorting: false,
      },
      {
        accessorKey: 'updated_at',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Updated At
          </Box>
        ),
        accessorFn: (row) => {
          const temp = new Date(row.updated_at); // Convert to Date object
          return temp.toISOString().split('T')[0]; // Format to YYYY-MM-DD
        },
        enableSorting: true,
      },
      {
        accessorKey: 'workstream',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
            px="2"
            py="1"
          >
            Work Stream
          </Box>
        ),
        enableSorting: false, // Disable sorting for this column
        meta: {
          width: '150px', // Define the width here (can be dynamic as needed)
        },
        cell: (info) => {
          const rawValue = info.getValue(); // Get the raw value of 'workstream'
          // Remove the numeric prefix and the following hyphen, if present
          const processedValue: any =
            typeof rawValue === 'string'
              ? rawValue.replace(/^\d+-/, '')
              : rawValue;

          return <Text whiteSpace="nowrap">{processedValue}</Text>;
        },
      },
      {
        accessorKey: 'file_url',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            S3 Url
          </Box>
        ),
        cell: (info) => {
          const fileUrl: any = info.getValue(); // Get the S3 URL
          const fileName = fileUrl.split('/').pop(); // Extract file name from URL

          return (
            <Flex align="center" gap="5px">
              <Tooltip label={fileUrl} placement="top">
                <Text isTruncated maxWidth="400px">
                  {fileName}
                </Text>
              </Tooltip>
              <Tooltip label="Copy S3 URL" placement="top">
                <IconButton
                  icon={<CopyIcon />}
                  size="sm"
                  onClick={() => handleCopy(info.getValue())}
                  aria-label="Copy S3 URL"
                />
              </Tooltip>
            </Flex>
          );
        },
      },
      {
        accessorKey: 'file_stats.stats_data',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Stats Overview
          </Box>
        ),
        cell: (info) => {
          const stats = info.getValue();
          const workstream = info.row.original.workstream; // Accessing workstream from the row data
          return (
            <Box gap="5px">
              <Flex alignItems="center" justify="space-between" mb="5px">
                <Text>Conversations:</Text>
                <Badge colorScheme="purple">
                  {stats?.totalConversations ?? 'NA'}
                </Badge>
              </Flex>
              {workstream !== '2410-sft-reasoning' && (
              <Flex alignItems="center" justify="space-between" mb="5px">
                <Text>SFT/Ideal:</Text>
                <Badge colorScheme="green">
                  {stats?.ideal_sft ?? 'NA'}
                </Badge>
              </Flex>             
             )}
           {workstream !== '2410-sft-reasoning' && (
              <Flex alignItems="center" justify="space-between" mb="5px">
                <Text>RLHF:</Text>
                <Badge colorScheme="blue">
                  {stats?.rlhf ?? 'NA'}
                </Badge>
              </Flex>
  )}
              {/* Conditionally render Section Sum if the workstream matches */}
              {workstream === '2410-sft-reasoning' && (
                <Flex alignItems="center" justify="space-between" mb="5px">
                  <Text>Total Section Sum:</Text>
                  <Badge colorScheme="pink">
                    {stats?.section_sum ?? 'NA'}
                  </Badge>
                </Flex>
              )}
                                       {workstream !== '2410-sft-reasoning' && (

              <Flex alignItems="center" justify="space-between">
                <Text>Total Turns:</Text>
                <Badge colorScheme="orange">
                  {stats?.totalUserTurns ?? 'NA'}
                </Badge>
              </Flex>
                                       )}
            </Box>
          );
        },
        enableSorting: false,
      },      
      {
        accessorKey: 'combined_stats',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Other Stats Overview
          </Box>
        ),
        cell: (info) => {
          const value = info.row.original.file_stats?.stats_data || {};
          const workstream = info.row.original.workstream; // Accessing the workstream
          const [isOpen, setIsOpen] = useState(false);
          const [modalContent, setModalContent] = useState<any>(null);
          const [modalTitle, setModalTitle] = useState('');
      
          const handleIconClick = (title: string, content: any) => {
            setModalTitle(title);
            setModalContent(content);
            setIsOpen(true);
          };
      
          const handleClose = () => {
            setIsOpen(false);
          };
      
          return (
            <>
              <Box>
                <Flex direction="column" gap="4px">
                  {/* Conditionally display only the "Category" when workstream matches */}
                  <Flex align="center" justify="space-between" whiteSpace="nowrap">
                    <Text marginRight="8px">Category:</Text>
                    <Tooltip label="View Category Details">
                      <IconButton
                        icon={<ViewIcon />}
                        size="sm"
                        onClick={() =>
                          handleIconClick('Category Details', value.categoryGroups)
                        }
                        aria-label="View Category Details"
                      />
                    </Tooltip>
                  </Flex>
      
                  {/* Display other fields only if workstream is not '2410-sft-reasoning' */}
                  {workstream !== '2410-sft-reasoning' && (
                    <>
                      <Flex align="center" justify="space-between" whiteSpace="nowrap">
                        <Text marginRight="8px">Subcategory:</Text>
                        <Tooltip label="View Subcategory Details">
                          <IconButton
                            icon={<ViewIcon />}
                            size="sm"
                            onClick={() =>
                              handleIconClick(
                                'Subcategory Details',
                                value.subcategoryGroups
                              )
                            }
                            aria-label="View Subcategory Details"
                          />
                        </Tooltip>
                      </Flex>
                      <Flex align="center" justify="space-between" whiteSpace="nowrap">
                        <Text marginRight="8px">Difficulty Distribution:</Text>
                        <Tooltip label="View Difficulty Details">
                          <IconButton
                            icon={<ViewIcon />}
                            size="sm"
                            onClick={() =>
                              handleIconClick(
                                'Difficulty Distribution Details',
                                value.difficultyLevel
                              )
                            }
                            aria-label="View Difficulty Details"
                          />
                        </Tooltip>
                      </Flex>
                      <Flex align="center" justify="space-between" whiteSpace="nowrap">
                        <Text marginRight="8px">Language Distribution:</Text>
                        <Tooltip label="View Language Distribution Details">
                          <IconButton
                            icon={<ViewIcon />}
                            size="sm"
                            onClick={() =>
                              handleIconClick(
                                'Language Distribution Details',
                                value.mainCodingLanguageGroups
                              )
                            }
                            aria-label="View Language Distribution Details"
                          />
                        </Tooltip>
                      </Flex>
                      <Flex align="center" justify="space-between" whiteSpace="nowrap">
                        <Text marginRight="8px">Images Distribution:</Text>
                        <Tooltip label="View Image Distribution Details">
                          <IconButton
                            icon={<ViewIcon />}
                            size="sm"
                            onClick={() =>
                              handleIconClick(
                                'Image Distribution Details',
                                value.image_distribution_groups
                              )
                            }
                            aria-label="View Image Distribution Details"
                          />
                        </Tooltip>
                      </Flex>
                    </>
                  )}
                </Flex>
              </Box>
              <Modal isOpen={isOpen} onClose={handleClose} size="lg">
                <ModalOverlay />
                <ModalContent>
                  <ModalHeader>{modalTitle}</ModalHeader>
                  <ModalCloseButton />
                  <ModalBody
                    style={{
                      maxHeight: '400px',
                      overflowY: 'auto',
                    }}
                  >
                    {modalContent ? (
                      <ReactJson
                        src={modalContent}
                        name={false}
                        theme="rjv-default"
                        collapsed={2}
                        displayDataTypes={false}
                        displayObjectSize={false}
                      />
                    ) : (
                      'No details available'
                    )}
                  </ModalBody>
                  <ModalFooter>
                    <Button colorScheme="blue" onClick={handleClose}>
                      Close
                    </Button>
                  </ModalFooter>
                </ModalContent>
              </Modal>
            </>
          );
        },
        enableSorting: false,
      }
      
    ],
    []
  );
  const handleChange = (event: any) => {
    setWorkStream(event.target.value);
  };

  const currentDate = new Date().toISOString().split('T')[0]; // Get the current date in YYYY-MM-DD format
  const minDate = new Date();
  minDate.setFullYear(minDate.getFullYear() - 1); // Subtract 1 year from the current date
  const minDateString = minDate.toISOString().split('T')[0]; // Minimum date in YYYY-MM-DD format

  const handleStartDateChange = (e: any) => {
    const newStartDate = e.target.value;
    if (newStartDate <= endDate || !endDate) {
      setStartDate(newStartDate);
    }
  };

  const handleEndDateChange = (e: any) => {
    const newEndDate = e.target.value;
    if (newEndDate <= currentDate) {
      setEndDate(newEndDate);
    }
  };

  // Track changes to workstream
  // Track changes to workstream
  useEffect(() => {
    setIsDataLoading(true); // Set loading state when workstream changes

    // Update workstream filter asynchronously
    setWorkstreamFilter(workstream);

    // Use a timeout or delay to ensure state changes happen after the workstream is processed
    setTimeout(() => {
      setIsDataLoading(false); // Set loading state to false after a delay
    }, 500); // Adjust the delay as needed (500ms in this case)
  }, [workstream]);

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

  return (
    <Box p={4}>
      {/* <Flex p="10px 0" alignItems={'center'} gap={'10px'}>
       
      </Flex> */}
      <Flex
        p={{ base: '10px', md: '10px 0' }} // Adjust padding for small screens
        alignItems="center"
        gap={{ base: '10px', md: '20px' }} // Smaller gap for smaller screens
        direction={{ base: 'column', md: 'row' }} // Stack items on small screens
        w="100%" // Full width container
      >
        <Text>Filter by WorkStream</Text>

        <Select
            placeholder="Select Workstream"
            value={workstream}
            onChange={handleChange}
            width={{ base: '100%', md: '15%' }} // Full width on small screens
          >
            {workstreams?.workstream
              ?.slice() // Create a shallow copy to avoid mutating the original array
              .sort((a, b) => a.replace(/^\d+-/, '').localeCompare(b.replace(/^\d+-/, ''))) // Sort alphabetically, ignoring numeric prefixes
              .map((ws: string) => (
                <option key={ws} value={ws}>
                  {ws.replace(/^\d+-/, '')} {/* Remove starting numeric values */}
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
            setWorkStream('');
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
        // Your other component content goes here
        <Table
          id="fileList"
          columns={columns}
          data={data?.s3_files}
          isLoading={isLoading}
          pageCount={data?.pageCount}
          page={query.page}
          pageSize={query.pageSize}
          sorting={query.sorting}
          setPage={setPage}
          setPageSize={setPageSize}
          setSorting={setSorting}
          containerProps={{
            style: {
              padding: '8px', // Reduce padding
              gap: '8px', // Reduce gap between cells
            },
          }}
          rowProps={{
            style: {
              padding: '4px 8px', // Compact row padding
            },
          }}
        />
      )}
      <CustomModal
        onClose={handleModalClose}
        isOpen={isOpen}
        header={'File Content'}
      >
        {fileContentLoading ? (
          <VStack justifyContent="center" height="42vh">
            <CircularProgress isIndeterminate size="120px" />
          </VStack>
        ) : (
          <ReactJson enableClipboard={false} src={fileData} />
        )}
      </CustomModal>
    </Box>
  );
}

export { Dashboard as Component };
