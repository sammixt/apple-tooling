import {
  Box,
  Button,
  CircularProgress,
  Flex,
  Input,
  Progress,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  VStack,
  useToast,
  Tooltip,
  Spinner,
  Badge,
  Table as ChakraTable,
  Thead,
  Tr,
  Th,
  Tbody,
  IconButton,
  Td,
  useDisclosure,
  Select,
} from '@chakra-ui/react';
import { DownloadIcon, ArrowUpIcon, ArrowDownIcon } from '@chakra-ui/icons';
import { FaDownload, FaUpload } from 'react-icons/fa';
import FileUpload from '../../components/file-upload';
import { Dispatch, SetStateAction, useEffect, useMemo, useRef, useState } from 'react';
import Table from '../../components/table/table';
import axios from 'axios';
import CustomModal from '../../components/modal/modal';
import { ErrorType, ItemListQuery, UploadedFiles } from '../../types';
import { EMPTY, useItemListQueryParams } from '../../hooks/query';
import {
  useGetUploadFileMutation,
  useGetWorkstreamsQuery,
  usePostUploadFileMutation,
  useUploadFileMutation,
  useUploadedFilesListQuery,
} from './store';
import { useAppSelector } from '../../hooks/store';
import { getProfile } from '../../features/auth/store';
import { config } from '../../services/config';
import dayjs from 'dayjs';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
} from '@chakra-ui/react';
import ReactJson from 'react-json-view';
import CollabLinkUpload from '../../components/collab-link-upload';
import CollabLinkToJson from '../../components/collab-link-to-json';
import UploadConfirmationModal from '../../components/modal/confirmation-modal';
import { useGetConfigQuery } from '../../components/default-layout/store';

const INITIAL_TABLE_STATE: ItemListQuery<UploadedFiles> = {
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
function Upload() {
  const profile = useAppSelector(getProfile);
  const { query, setPage, setPageSize, setSorting, setDateFilter, setWorkstreamFilter } =
    useItemListQueryParams<UploadedFiles>(INITIAL_TABLE_STATE);
  const {
    data = EMPTY,
    isLoading,
    refetch,
  } = useUploadedFilesListQuery({ query }, { refetchOnMountOrArgChange: true });

  const {
    data: config,
    isLoading: isRoleLoading,
  } = useGetConfigQuery(null, {
    skip: false,
    refetchOnMountOrArgChange: true,
  });

  const { data: workstreams = [] } = useGetWorkstreamsQuery(null);
  const [postUploadFile] = usePostUploadFileMutation();
  const [getUploadFile] = useGetUploadFileMutation();

  const [tabIndex, setTabIndex] = useState(0);
  // const [file, setFile] = useState<Blob | string>('');
  const [files, setFiles] = useState<File[]>([]);
  const [isValidFile, setIsValidFile] = useState(false);
  const [workstream, setWorkStream] = useState<string>('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [saveFile] = useUploadFileMutation();
  const [fileId, setFileId] = useState('');
  const [progress, setProgress] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [isDeliveryFileOpen, setIsDeliveryFileOpen] = useState(false);
  const [fileContentLoading, setFileContentLoading] = useState(false);
  const [batchData, setBatchData] = useState<any>();
  const [client, setClient] = useState('');
  const [uploadDate, setUploadDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split('T')[0]; // Default to today's date
  });
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [uploadState, setUploadState] = useState<{
    batchId: string | null;
    setIsUploading: Dispatch<SetStateAction<boolean>> | null;
  }>({
    batchId: null,
    setIsUploading: null, // Default to null
  });
  const [filterWorkstream, setFilterWorkstream] = useState<string>('');
  const [isDataLoading, setIsDataLoading] = useState(false); // State to track loading

  const handleOpenModal = (
    newBatchId: any,
    setIsUploading: Dispatch<SetStateAction<boolean>>
  ) => {
    setUploadState({
      batchId: newBatchId,
      setIsUploading: setIsUploading,
    });
    onOpen(); // Open the modal
  };

  const toast = useToast();
  const pollingIntervalRef :any = useRef(null);
  // const [doPoolling, setDoPoolling] = useState(false);

  useEffect(() => {
      const startPolling = async () => {
        const poll = async () => {  
          // Check if there are items with "in-progress" status
          const hasInProgress = data.items.some((item:any) => item.status == 'In progress');
          if (!hasInProgress) {
            // Stop polling if no "in-progress" status
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }else{
            refetch();
          }
        };
  
        // Start the polling at a 5-second interval
        pollingIntervalRef.current = setInterval(poll, 20000);
  
        // Run the first poll immediately
        await poll();
      };
  
      startPolling();
  
      // Cleanup the interval on component unmount
      return () => {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
        }
      };
   
  }, [refetch,data]);

  const handleWorkStreamChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newWorkstream = e.target.value;
    const isSFTReasoning = newWorkstream === 'sft_reasoning';

    if (files.length > 0) {
      const hasInvalidFiles = files.some(
        (file) =>
          (isSFTReasoning && file.type !== 'text/csv') || // For reasoning, only CSV allowed
          (!isSFTReasoning && file.type !== 'application/json') // For non-reasoning, only JSON allowed
      );

      if (hasInvalidFiles) {
        toast({
          status: 'error',
          isClosable: true,
          position: 'top',
          duration: null,
          title: 'Workstream Switch Error',
          description: `Cannot switch to ${
            isSFTReasoning ? 'SFT Reasoning' : 'another workstream'
          } because the selected files are not valid for the new workstream. Please remove the current files and try again.`,
        });
        return; // Prevent changing the workstream
      }
    }

    setWorkStream(newWorkstream); // Update the workstream if no issues
  };

  const handleChange = (selectedFiles: File[]) => {
    if (!workstream) {
      toast({
        status: 'error',
        isClosable: true,
        position: 'top',
        duration: null,
        title: 'Workstream not selected',
        description: 'Please select a workstream before uploading files.',
      });
      return;
    }

    const isSFTReasoning = workstream === 'sft_reasoning';

    // Validate file types and number of files
    const invalidFilesSft = selectedFiles.filter(
      (file) =>
        (isSFTReasoning && file.type !== 'text/csv') || // For `sft_reasoning`, allow only CSV
        (!isSFTReasoning && file.type !== 'application/json') // For other workstreams, allow only JSON
    );

    if (invalidFilesSft.length > 0) {
      toast({
        status: 'error',
        isClosable: true,
        position: 'top',
        duration: null,
        title: 'Invalid file type',
        description: isSFTReasoning
          ? 'Only CSV file is allowed for SFT Reasoning.'
          : 'Only JSON files are allowed for this workstream.',
      });
      return;
    }

    if (isSFTReasoning && selectedFiles.length > 1) {
      toast({
        status: 'error',
        isClosable: true,
        position: 'top',
        duration: null,
        title: 'Too many files',
        description: 'You can only upload one CSV file for SFT Reasoning.',
      });
      return;
    }

    if (!isSFTReasoning) {
      const tags = [
        'sft',
        'rlhf',
        'prompts',
        'human evals',
        'process supervision',
        'multimodality',
        'batch',
      ];

      // Helper function to check which tag a file matches
      const getFileTag = (fileName: string) =>
        tags.filter((tag) => fileName.toLowerCase().includes(tag));

      // Check if any file has multiple tags or different tags
      const fileTags = selectedFiles.map((file) => ({
        file,
        matchedTags: getFileTag(file.name),
      }));

      const invalidFiles = fileTags.filter(
        (file) => file.matchedTags.length < 1
      ); // Files with no or multiple tags
      if (invalidFiles.length > 0) {
        toast({
          status: 'error',
          isClosable: true,
          position: 'top',
          duration: null,
          title: 'Invalid file(s)',
          description: `Each file must contain one of these tags: 'sft', 'rlhf', 'prompts', 'human evals', 'process supervision', 'multimodality', 'batch.`,
        });
        return;
      }

      // Get the unique tag for the batch
      const batchTag = fileTags[0].matchedTags[0]; // Take the first file's tag for comparison

      const mixedTags = fileTags.some(
        (file) => file.matchedTags[0] !== batchTag
      );
      if (mixedTags) {
        toast({
          status: 'error',
          isClosable: true,
          position: 'top',
          duration: null,
          title: 'Invalid file batch',
          description: `All files must belong to the same tag. Found mixed tags like '${fileTags
            .map((file) => file.matchedTags[0])
            .join(', ')}'.`,
        });
        return;
      }
    }

    // If everything is valid, append files
    setFiles((prevFiles) =>
      isSFTReasoning ? selectedFiles : [...prevFiles, ...selectedFiles]
    );
    setIsValidFile(true);
  };
  const handleWorkstreamChangeFilter = (event: any) => {
    setFilterWorkstream(event.target.value);
    setWorkstreamFilter(event.target.value)
  };

  const handleFileRemove = (fileToRemove: File) => {
    setFiles((prevFiles) =>
      prevFiles.filter((file) => file.name !== fileToRemove.name)
    );
  };

  async function handleUpload() {
    try {
      setUploadLoading(true);

      const MAX_SIZE = 800 * 1024 * 1024; // 800 MB in bytes
      let totalSize = 0;
      const filesToUpload: any = [];

      // Check each file's size and calculate total size
      files.forEach((file) => {
        totalSize += file.size; // Add the file size to the total size
        if (totalSize > MAX_SIZE) {
          toast({
            status: 'error',
            isClosable: true,
            position: 'top',
            duration: null,
            title: 'File Size Exceeded',
            description:
              'The combined size of the selected files exceeds the 800 MB limit. Please remove some files or reduce their size.',
          });
          setUploadLoading(false);
          return;
        }
        filesToUpload.push(file); // Add file to the list to upload
      });

      // Create FormData and append files array correctly
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file)); // Correctly append as 'files[]'

      // Add other parameters
      const query = `workstream=${workstream}&user_email=${profile?.email}&user_name=${profile?.name}&delivery_date=${uploadDate}&client=penguin`;

      // Send the request with FormData
      let res;
      try {
        res = await saveFile({
          body: formData,
          query,
        }).unwrap();
      } catch (e: any) {
        console.log('error123 = ', e);
        toast({
          status: 'error',
          isClosable: true,
          position: 'top',
          duration: null,
          title: 'Failed to send files',
          description: e.data.detail,
        });
        return;
      }
      console.log('----------------res', res);

      // Handle the response
      if (res?.message) {
        toast({
          status: 'success',
          isClosable: true,
          position: 'top',
          duration: 5000,
          title: 'Files sent to backend',
          description: 'Uploading and validating the files will take time.',
        });
        setFileId(res?.id);
        setTabIndex(0);
      }
    } catch (e: any) {
      toast({
        status: 'error',
        isClosable: true,
        position: 'top',
        duration: 5000,
        title: 'Failed to send files',
        description: e,
      });
    } finally {
      setFiles([]); // Reset files after upload
      setWorkStream('');
      setIsValidFile(false);
      setUploadLoading(false);
      // Call refetch immediately
      refetch();
      // Schedule another refetch after 6 seconds
      // setTimeout(() => {
      //   refetch();
      // }, 6000);
    }
  }

  const handleSFTReasoningUpload = async () => {
    try {
      setUploadLoading(true);

      if (files.length !== 1) {
        toast({
          status: 'error',
          isClosable: true,
          position: 'top',
          duration: null,
          title: 'File Upload Error',
          description: 'Only one CSV file is allowed for SFT Reasoning.',
        });
        return;
      }

      const formData = new FormData();
      formData.append('file', files[0]); // Append the file
      formData.append('user_email', profile?.email || ''); // Add user email
      formData.append('user_name', profile?.name || ''); // Add user name
      formData.append('delivery_date', uploadDate); // Add delivery date
      formData.append('client', client);

      // const res = await axios.post(
      //   `${config.apiUrl}/processor/colab/`,
      //   formData
      // );
      //tested
      const res = await postUploadFile({
        body: formData,
        url: '/colab/',
      }).unwrap();
      if (res?.message) {
        toast({
          status: 'success',
          isClosable: true,
          position: 'top',
          duration: 5000,
          title: 'CSV File Uploaded',
          description: res.message,
        });
        setTabIndex(0);
      }
    } catch (e: any) {
      console.error(e);
      toast({
        status: 'error',
        isClosable: true,
        position: 'top',
        duration: null,
        title: 'File Upload Failed',
        description: e.response?.detail || 'An error occurred.',
      });
    } finally {
      setFiles([]);
      setUploadLoading(false);
      // Call refetch immediately
      refetch();

      // // Schedule another refetch after 6 seconds
      // setTimeout(() => {
      //   refetch();
      // }, 20000);
    }
  };

  const handleUploadClick = async () => {
    try {
      uploadState.setIsUploading?.(true);
      console.log(`Upload button clicked for batch ID: ${uploadState.batchId}`);
      // const res = await axios.post(
      //   `${config.apiUrl}/processor/uoload-s3/?batch_id=${batchId}`
      // );
      const res = await postUploadFile({
        body: {},
        url: `/uoload-s3/?batch_id=${uploadState.batchId}`,
      }).unwrap();
      toast({
        status: 'success',
        isClosable: true,
        position: 'top',
        duration: 5000,
        title: 'Batch has been uploaded',
        description: '',
      });
    } catch (e: any) {
      console.error(e);
      toast({
        status: 'error',
        isClosable: true,
        position: 'top',
        duration: 5000,
        title: 'Something went wrong',
        description: e.response.detail,
      });
    } finally {
      uploadState.setIsUploading?.(false);
      // Call refetch immediately
      refetch();

      // Schedule another refetch after 6 seconds
      // setTimeout(() => {
      //   refetch();
      // }, 6000);
      
    }
  };

  const handleModalDeliveryFileClose = () => {
    setIsDeliveryFileOpen(false);
  };

  const columns = useMemo(
    () => [
      {
        accessorKey: 'updated_at',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Date
          </Box>
        ),
        cell: (info) => {
          const rawValue = info.getValue();
          const formattedDate = rawValue
            ? dayjs(rawValue).format('YYYY-MM-DD') // Format for the date
            : 'NA';
          const formattedTime = rawValue
            ? dayjs(rawValue).format('hh:mm A') // Format for the time
            : '';

          return (
            <Box
              whiteSpace="nowrap"
              overflow="hidden"
              textOverflow="ellipsis"
              display="flex"
              flexDirection="column"
              alignItems="start"
            >
              <Box>{formattedDate}</Box>
              <Box fontSize="sm" color="gray.500">
                {formattedTime}
              </Box>
            </Box>
          );
        },
        enableSorting: true
      },
      {
        accessorKey: 'files',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Files
          </Box>
        ),
        cell: (info) => {
          const [showAll, setShowAll] = useState(false);

          const files = info.row.original.files as object[];
          const maxVisibleFiles = 3; // Number of files to show initially

          return (
            <div>
              {files
                .slice(0, showAll ? files.length : maxVisibleFiles)
                .map((file, index) => (
                  <span key={file.id}>
                    {file.name}
                    {index < files.length - 1 && ', '}
                  </span>
                ))}

              {files.length > maxVisibleFiles && (
                <Button
                  variant="link"
                  colorScheme="blue"
                  onClick={() => setShowAll((prev) => !prev)}
                >
                  {showAll
                    ? 'Hide'
                    : `Show ${files.length - maxVisibleFiles} more`}{' '}
                  {/* Remaining count */}
                </Button>
              )}
            </div>
          );
        },
        enableSorting: false,
      },
      {
        accessorKey: 'workstream',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Workstream
          </Box>
        ),
      },
      // { accessorKey: 'workstream_pre.name', header: 'Workstream' },
      // { accessorKey: 'name', header: 'File Name' },
      {
        accessorKey: 'status',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Processing Status
          </Box>
        ),
        cell: (info) => {
          const status = info.row.original.status || 'Failed';
          const isProgress = status === 'In progress';
          const isFailed = status === 'Failed'; // Check for 'Failed' status
          const batch_id = info.row.original.uuid;
          // Start the event stream when "In progress" status is encountered
          if (isProgress && progress <= 100) {
            // Ensure you handle the event stream logic if necessary
          }

          const is_uploaded: boolean = info.row.original.is_uploaded;

          if (isProgress) {
            return (
              <Box width="100px" margin="0 auto" textAlign="center">
                <VStack spacing={4}>
                  <Text fontSize="md" fontWeight="normal">
                    In Progress
                  </Text>
                  <Progress
                    isIndeterminate
                    size="lg"
                    colorScheme="green"
                    width="100%"
                  />
                </VStack>
              </Box>
            );
          } else if (isFailed) {
            return (
              <Tooltip
                label={info.row?.original.failed_reason}
                aria-label="Failed reason"
              >
                <Badge colorScheme="red" borderRadius="full" px="3" py="1">
                  {String(status) || 'NA'}
                </Badge>
              </Tooltip>
            );
          } else if (is_uploaded) {
            return (
              <Badge colorScheme="green" borderRadius="full" px="3" py="1">
                Uploaded to S3
              </Badge>
            );
          } else {
            return <Text>{String(status) || 'NA'}</Text>;
          }
        },
      },
      {
        accessorKey: 'user_email',
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
      },
      {
        accessorKey: 'stats',
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
          const stats: any = info.getValue();
          const workstream = info.row.original.workstream; // Accessing workstream from the row data

          return (
            <Box gap="5px">
              <Flex alignItems="center" justify="space-between" mb="5px">
                <Text>Conversations: </Text>
                <Badge colorScheme="purple">
                  {stats?.totalConversations ?? 'NA'}
                </Badge>
              </Flex>
              {workstream !== 'sft_reasoning' && (
              <Flex alignItems="center" justify="space-between" mb="5px">
                <Text>SFT/Ideal: </Text>
                <Badge colorScheme="green">{stats?.ideal_sft ?? 'NA'}</Badge>
              </Flex>
              )}
             {workstream !== 'sft_reasoning' && (
              <Flex alignItems="center" justify="space-between" mb="5px">
                <Text>RLHF: </Text>
                <Badge colorScheme="blue">{stats?.rlhf ?? 'NA'}</Badge>
              </Flex>
             )}
              {workstream !== 'sft_reasoning' && (
              <Flex alignItems="center" justify="space-between">
                <Text>Total Turns: </Text>
                <Badge colorScheme="orange">
                  {stats?.totalUserTurns ?? 'NA'}
                </Badge>
              </Flex>
              )}
              {workstream === 'sft_reasoning' && (
                <Flex alignItems="center" justify="space-between" mb="5px">
                  <Text>Total Sections:</Text>
                  <Badge colorScheme="pink">
                    {stats?.section_sum ?? 'NA'}
                  </Badge>
                </Flex>
              )}
            </Box>
          );
        },
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
        cell: (info: any) => {
          const [isOpen, setIsOpen] = useState(false);
          const [loadingDownload, setDownloadLoading] = useState(false); // Add loading state
          const errors = info.row.original.errors;
          const status = info.row.original.status;
          const is_uploaded: boolean = info.row.original.is_uploaded;
          const batchId = info.row.original.uuid;
          const [errorData, setErrorData] = useState<any>();
          const [isUploading, setIsUploading] = useState(false);

          const storedUserPermissions =
            JSON.parse(localStorage.getItem('userPermissions')) || {};

          const handleOpenErrorModal = () => {
            setIsOpen(true);
          };

          const handleCloseErrorModal = () => {
            setIsOpen(false);
          };

          const s3_path = info.row.original.s3_path || 'url not found';

          const handleDownloadDeliveryFileClick = async (
            batchId: string,
            batch_name: any
          ) => {
            setDownloadLoading(true); // Start loading when the click happens
            try {
              // const res = await axios.get(
              //   `${config.apiUrl}/processor/delivery-file/?batch_id=${batchId}`,
              //   { responseType: 'json' } // Ensure response is treated as JSON
              // );
              const res = await getUploadFile({
                url: `/delivery-file/?batch_id=${batchId}`,
              }).unwrap();
              // Create a Blob from the response data
              const blob = new Blob([JSON.stringify(res, null, 2)], {
                type: 'application/json',
              });

              // Create a download link
              const url = window.URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', `${batch_name}`); // Set download file name
              document.body.appendChild(link);
              link.click(); // Trigger the download
              document.body.removeChild(link); // Clean up the DOM
              window.URL.revokeObjectURL(url); // Release the blob URL
            } catch (e: any) {
              console.error('Error downloading file:', e.message);
            } finally {
              setDownloadLoading(false); // Stop loading after the process
            }
          };

          const batch_name = info.row.original.name;
          if (is_uploaded) {
            return (
              <Tooltip label={s3_path} placement="top">
                <Button
                  width="100%"
                  maxWidth="100px"
                  colorScheme="blue"
                  onClick={() =>
                    handleDownloadDeliveryFileClick(batchId, batch_name)
                  }
                  isDisabled={!storedUserPermissions['download_from_s3']} // Disable the button if permission is missing
                >
                  {loadingDownload ? <Spinner size="sm" /> : 'Download'}{' '}
                  {/* Show spinner when loading */}
                </Button>
              </Tooltip>
            );
          }

          const upload_tip_message = config?.configuration?.enable_penguin_s3_upload ? 'Upload to Penguin S3' : 'Upload to Turing S3';

          if (status === 'Completed') {
            return (
              <Flex direction="row" gap="10px" align="center">
                <Tooltip label={'Download JSON before Uploading'} placement="top">
                  <IconButton
                    icon={loadingDownload ? <Spinner size="sm" /> : <FaDownload />}
                    variant="ghost"
                    colorScheme="cyan"
                    onClick={() =>
                      handleDownloadDeliveryFileClick(batchId, batch_name)
                    }
                    aria-label="Download File"
                    isDisabled={!storedUserPermissions['download_from_s3']} // Disable the button if permission is missing
                  />
                </Tooltip>

                <Tooltip label={upload_tip_message} placement="top">
                  <IconButton
                    icon={isUploading ? <Spinner size="sm" /> : <FaUpload />}
                    variant="ghost"
                    colorScheme="cyan"
                    onClick={() => handleOpenModal(batchId, setIsUploading)}
                    aria-label="Upload File"
                    isDisabled={!storedUserPermissions['upload_to_s3']}
                  />
                </Tooltip>
              </Flex>
            );
          } else if (status === 'error') {
            return (
              <>
                <Button
                  width="100%"
                  maxWidth="100px"
                  colorScheme="red"
                  onClick={handleOpenErrorModal}
                >
                  View
                </Button>
                <Modal
                  isOpen={isOpen}
                  onClose={handleCloseErrorModal}
                  size="lg"
                >
                  <ModalOverlay />
                  <ModalContent>
                    <ModalHeader>Errors in Batch</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody
                      style={{
                        maxHeight: '400px',
                        overflowY: 'auto',
                      }}
                    >
                      {errors ? (
                        <ReactJson
                          src={errors}
                          name={false}
                          theme="rjv-default"
                          collapsed={2}
                          displayDataTypes={false}
                          displayObjectSize={false}
                        />
                      ) : (
                        'No Errors available'
                      )}
                    </ModalBody>
                    <ModalFooter>
                      <Button
                        colorScheme="blue"
                        onClick={handleCloseErrorModal}
                      >
                        Close
                      </Button>
                      {/* <Button colorScheme="blue" onClick={() => handleRemoveErrorsClick(batchId)}>
                        Remove Errors
                      </Button> */}
                    </ModalFooter>
                  </ModalContent>
                </Modal>
              </>
            );
          } else {
            return <div>--</div>; // No button for other statuses
          }
        },
        enableSorting: false, // Disable sorting for this action column
      },
      {
        accessorKey: 'has_validation_error',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Validation Error
          </Box>
        ),
        cell: (info) => {
          const [isOpen, setIsOpen] = useState(false);
          const [errorLoading, setErrorLoading] = useState(false);
          const [errorData, setErrorData] = useState<any>();

          const has_validation_error = info.row.original.has_validation_error;

          const batchId = info.row.original.uuid;

          const handleOpenFailedModal = () => {
            setIsOpen(true);
            setErrorData(
              info.row.original.failed_reason ?? 'No failed message provided'
            );
          };
          const handleOpenErrorModal = async () => {
            try {
              setIsOpen(true);
              setErrorLoading(true);
              // const res = await axios.get(
              //   `${config.apiUrl}/processor/errors/?batch_id=${batchId}`
              // );
              ///tested
              const res = await getUploadFile({
                url: `/errors/?batch_id=${batchId}`,
              }).unwrap();
              setErrorData(res);
            } catch (e: any) {
              console.error(e.message);
            } finally {
              setErrorLoading(false);
            }
          };

          const handleCloseErrorModal = () => {
            setIsOpen(false);
          };

          const status = info.row.original.status;

          // if (status !== 'Completed') {
          //   return <div>Still Processing</div>;
          // }

          const [isDownloading, setIsDownloading] = useState(false);

          const handleDownload = async (data) => {
            setIsDownloading(true);
            try {
              const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json',
              });
              const url = window.URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', `Error Details`);
              document.body.appendChild(link);
              link.click(); // Trigger the download
              document.body.removeChild(link); // Clean up the DOM
              window.URL.revokeObjectURL(url); // Release the blob URL
            } catch (e: any) {
              console.error('Error downloading file:', e.message);
            } finally {
              setIsDownloading(false);
            }
          };

          if (has_validation_error) {
            return (
              <>
                <Button
                  width="100%"
                  maxWidth="100px"
                  colorScheme="red"
                  onClick={handleOpenErrorModal}
                >
                  View
                </Button>
                <Modal
                  isOpen={isOpen}
                  onClose={handleCloseErrorModal}
                  size="lg"
                >
                  <ModalOverlay />
                  <ModalContent>
                    <ModalHeader> Validation Errors in Batch</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody
                      style={{
                        maxHeight: '400px',
                        overflowY: 'auto',
                      }}
                    >
                      {errorLoading ? (
                        <VStack
                          alignItems="center"
                          justifyContent="center"
                          direction="column"
                          justify="space-evenly"
                          w="full"
                          h="full"
                          height="42vh"
                        >
                          <CircularProgress isIndeterminate size="120px" />
                        </VStack>
                      ) : (
                        <>
                          <div>Error Report</div>
                          {errorData?.summary ? (
                            <ChakraTable
                              variant="simple"
                              size="sm"
                              mt={2}
                              mb={4}
                            >
                              <Thead>
                                <Tr>
                                  <Th>Error Type</Th>
                                  <Th isNumeric>Count</Th>
                                </Tr>
                              </Thead>
                              <Tbody>
                                {errorData.summary.error_types.map(
                                  (error: ErrorType, index: number) => (
                                    <Tr key={index}>
                                      <Td>{error.error_type}</Td>
                                      <Td isNumeric>{error.count}</Td>
                                    </Tr>
                                  )
                                )}
                                <Tr fontWeight="bold">
                                  <Td>Total Errors</Td>
                                  <Td isNumeric>
                                    {errorData.summary.total_errors}
                                  </Td>
                                </Tr>
                              </Tbody>
                            </ChakraTable>
                          ) : (
                            <Text>No summary data available</Text>
                          )}
                        </>
                      )}
                      <Flex justifyContent="space-between" gap={4}>
                        <Text>Error Details</Text>
                        <Button
                          width="100%"
                          maxWidth="100px"
                          colorScheme="blue"
                          onClick={() => handleDownload(errorData?.errors)}
                        >
                          {isDownloading ? <Spinner size="sm" /> : 'Download'}
                        </Button>
                      </Flex>
                      <ReactJson
                        src={
                          status === 'Failed'
                            ? { message: errorData }
                            : errorData?.errors
                        }
                        name={false}
                        theme="rjv-default"
                        collapsed={2}
                        displayDataTypes={false}
                        displayObjectSize={false}
                      />
                    </ModalBody>
                    <ModalFooter>
                      <Button
                        colorScheme="blue"
                        onClick={handleCloseErrorModal}
                      >
                        Close
                      </Button>
                      {/* <Button colorScheme="blue" onClick={() => handleRemoveErrorsClick(batchId)}>
                        Remove Errors
                      </Button> */}
                    </ModalFooter>
                  </ModalContent>
                </Modal>
              </>
            );
          } else {
            return (
              <Flex justify="center" align="center" height="100%">
                <div>--</div>
              </Flex>
            );
          }
        },
        enableSorting: false,
      },
    ],
    [progress]
  ); // Track changes in progress and connection status

  const currentDate = new Date().toISOString().split('T')[0];

  const minDate = new Date();
  minDate.setFullYear(minDate.getFullYear() - 1);
  const minDateString = minDate.toISOString().split('T')[0];

  const maxDate = new Date(currentDate);
  // maxDate.setDate(maxDate.getDate() + 7);
  const maxDateString = maxDate.toISOString().split('T')[0];

  useEffect(() => {
    setStartDate('');
    setEndDate('');
  }, []);

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newStartDate = e.target.value;
    setStartDate(newStartDate);
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEndDate = e.target.value;
    setEndDate(newEndDate);
  };
  useEffect(() => {
    // setSearch(startDate || endDate ? { startDate, endDate } : undefined);
    setDateFilter(startDate, endDate);
  }, [startDate, endDate, setDateFilter]);
  useEffect(() => {
    setIsDataLoading(true); // Set loading state when workstream changes

    // Update workstream filter asynchronously
    setFilterWorkstream(filterWorkstream);

    // Use a timeout or delay to ensure state changes happen after the workstream is processed
    setTimeout(() => {
      setIsDataLoading(false); // Set loading state to false after a delay
    }, 500); // Adjust the delay as needed (500ms in this case)
  }, [filterWorkstream]);

  const handleTabClick = () => {
    // Trigger your refetch call here
    refetch();
  };
  return (
    <Box p={{ base: 0, md: 8 }} pt={{ base: 5, md: 8 }}>
      <Tabs
        onChange={(index) => {
          setTabIndex(index); // Update the active tab index
        }}
        index={tabIndex}
      >
        <TabList>
          <Tab>Uploaded List</Tab>
          <Tab onClick={handleTabClick}>Upload File</Tab>
          <Tab>Collab Link To JSON</Tab>
          {/* <Tab>Upload Collab Links</Tab> */}
        </TabList>
        <TabPanels>
          {/* Uploaded List Tab */}
          <TabPanel>
            <Flex 
              p={{ base: '10px', md: '10px 0' }}
              gap={{ base: '10px', md: '20px' }}
              direction={{ base: 'column', md: 'row' }}
              w="100%"
              alignItems="center"
            >
                 <Text display={{ base: 'none', md: 'block' }}>Filter by WorkStream</Text>
              
                 <Select
                    placeholder="Select Workstream"
                    value={filterWorkstream}
                    onChange={handleWorkstreamChangeFilter}
                    width={{ base: '100%', md: '15%' }} // Full width on small screens
                  >
                    {workstreams
                      ?.slice() // Create a shallow copy to avoid mutating the original array
                      .sort((a, b) => a.name.localeCompare(b.name)) // Sort alphabetically by name
                      .map((ws: { id: string; name: string }) => (
                        <option key={ws.id} value={ws.id}>
                          {ws.name.replace(/^\d+-/, '')} {/* Remove starting numeric values */}
                        </option>
                      ))}
                  </Select>

              <Text display={{ base: 'none', md: 'block' }}>Start Date</Text>
              <Input
                type="date"
                border="1px solid lightgray"
                width={{ base: '100%', md: '20%' }}
                name="start_date"
                value={startDate}
                onChange={handleStartDateChange}
                min={minDateString}
                max={endDate || maxDateString}
                placeholder="dd/mm/yyyy" // Optional
              />

              <Text display={{ base: 'none', md: 'block' }}>End Date</Text>
              <Input
                type="date"
                border="1px solid lightgray"
                width={{ base: '100%', md: '20%' }}
                name="end_date"
                value={endDate}
                onChange={handleEndDateChange}
                min={startDate || minDateString}
                max={maxDateString}
                placeholder="dd/mm/yyyy" // Optional
              />
              {/* Clear Filters Button */}
              <Button
                onClick={() => {
                  setStartDate('');
                  setEndDate('');
                  setFilterWorkstream('')
                }}
                variant="outline"
                colorScheme="blue"
                width={{ base: '100%', md: 'auto' }}
              >
                Clear Filters
              </Button>
            </Flex>

            {isDataLoading ? (
              <Loader />
            ) : (
            <Table
              id="uploaded-list"
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
          </TabPanel>

          {/* Upload File Tab */}
          <TabPanel>
            {uploadLoading ? (
              <VStack
                alignItems="center"
                justifyContent="center"
                w="full"
                h="full"
                height="72vh"
              >
                <CircularProgress isIndeterminate size="120px" />
                <Text>
                  File upload and validation may take a long time to process.
                </Text>
              </VStack>
            ) : (
              <FileUpload
                handleUpload={() => {
                  if (workstream === 'sft_reasoning') {
                    handleSFTReasoningUpload();
                  } else {
                    handleUpload();
                  }
                }}
                handleChange={handleChange}
                handleFileRemove={handleFileRemove}
                workstream={workstream}
                isValidFile={isValidFile}
                handleWorkStreamChange={handleWorkStreamChange}
                workstreams={workstreams}
                files={files}
                uploadDate={uploadDate}
                setUploadDate={setUploadDate}
                client={client}
                setClient={setClient}
                isValidateDate={config?.configuration.upload_date_restriction}
              />
            )}
          </TabPanel>
          <TabPanel>
            {/* <CollabLinkToJson /> */}
            {tabIndex === 2 && <CollabLinkToJson key={tabIndex} />}
          </TabPanel>
          {/* <TabPanel>
            <CollabLinkUpload setTabIndex={setTabIndex} refetch={refetch}/>
          </TabPanel> */}
        </TabPanels>
      </Tabs>

      <CustomModal
        onClose={handleModalDeliveryFileClose}
        isOpen={isDeliveryFileOpen}
        header="File Content"
      >
        {fileContentLoading ? (
          <VStack
            alignItems="center"
            justifyContent="center"
            w="full"
            h="full"
            height="42vh"
          >
            <CircularProgress isIndeterminate size="120px" />
          </VStack>
        ) : (
          <ReactJson enableClipboard={false} src={batchData} />
        )}
      </CustomModal>

      <UploadConfirmationModal
        isOpen={isOpen}
        onClose={onClose}
        handleUploadClick={handleUploadClick}
      />
    </Box>
  );
}

export { Upload as Component };
