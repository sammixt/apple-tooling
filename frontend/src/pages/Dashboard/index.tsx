import {
  Box,
  Button,
  CircularProgress,
  Flex,
  Input,
  Text,
  VStack,
} from '@chakra-ui/react';
import { Table } from '../../components/table/table';
import { useMemo, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import ReactJson from 'react-json-view';
import CustomModal from '../../components/modal/modal';
import { FileInfo, ItemListQuery } from '../../types';
import { EMPTY_FILES, useItemListQueryParams } from '../../hooks/query';
import { useListFilesQuery } from './store';
import { useDebounce } from 'react-use';
import { config } from '../../services/config';
import { Modal, ModalOverlay, ModalContent, ModalHeader, ModalCloseButton, ModalBody, ModalFooter } from '@chakra-ui/react';

const INITIAL_TABLE_STATE: ItemListQuery<FileInfo> = {
  page: 1,
  pageSize: 25,
  sorting: [
    {
      id: 'updated_at', 
      desc: true,
    },
  ],
};

function Dashboard() {
  const { query, setPage, setPageSize, setSorting, setSearch } =
    useItemListQueryParams<FileInfo>(INITIAL_TABLE_STATE);
  const [workStream, setWorkStream] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [fileData, setFileData] = useState<any>();
  const [fileContentLoading, setFileContentLoading] = useState(false);
  const {
    data = EMPTY_FILES,
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

  useDebounce(
    () => {
      setSearch(
        workStream
          ? {
              workstream: workStream,
            }
          : undefined
      );
    },
    500,
    [workStream]
  );

  const handleModalClose = () => {
    setIsOpen(false);
  };

  const handleViewClick = async (id: number) => {
    try {
      setIsOpen(true);
      setFileContentLoading(true);
    } catch (e: any) {
      setFileData({});
      console.error(e.message);
    }
    setFileContentLoading(false);
  };

      // Other columns remain unchanged...
 

      const columns = useMemo<ColumnDef<any>[]>(
        () => [
          {
            accessorKey: 'id',
            header: () => <span>Action</span>,
            cell: (info) => (
              <Button
                variant="link"
                colorScheme="cyan"
                onClick={() => handleViewClick(info.getValue() as number)}
              >
                View
              </Button>
            ),
            enableSorting: false,
          },
          {
            accessorKey: 'updated_at',
            header: () => <span style={{ display: 'inline-block', width: '100px' }}>Updated At</span>,
            accessorFn: (row) => {
              const temp = new Date(row.updated_at); // Convert to Date object
              return temp.toISOString().split('T')[0]; // Format to YYYY-MM-DD (e.g., 2024-12-04)
            },
            enableSorting: true,
            // Optionally, define sorting logic in case you need custom behavior
            sortingFn: 'basic', // Default sorting function (optional, if you want to define custom sorting)
          },
          
          {
            accessorKey: 'workstream',
            cell: (info) => info.getValue(),
            header: () => <span>Work Stream</span>,
            enableSorting: false,
          },
          {
            accessorKey: 'file_url',
            header: () => 'S3 URL',
            size: 10,
            // enableSorting: true,
          },
          {
            accessorKey: 'file_stats.stats_data.totalConversations',
            header: () => <span>Conversation Count</span>,
            cell: (info) => info.getValue() ?? 'NA',
            // enableSorting: true,
          },
          {
            accessorKey: 'file_stats.stats_data.ideal_sft',
            header: 'SFT/Ideal Count',
            cell: (info) => info.getValue() ?? 'NA',
            // enableSorting: true,
          },
          {
            accessorKey: 'file_stats.stats_data.rlhf',
            header: 'RLHF Count',
            cell: (info) => info.getValue() ?? 'NA',
            // enableSorting: true,
          },
          {
            accessorKey: 'file_stats.stats_data.totalUserTurns',
            header: 'Total Turn Count',
            cell: (info) => info.getValue() ?? 'NA',
            // enableSorting: true,
          },
          {
            accessorKey: 'file_stats.stats_data.categoryGroups',
            header: 'Category',
            cell: (info) => {
              const [isOpen, setIsOpen] = useState(false);
              const value = info.getValue();
          
              const handleReadMoreClick = () => {
                setIsOpen(true);
              };
          
              const handleClose = () => {
                setIsOpen(false);
              };
          
              return (
                <>
                  <Button variant="link" colorScheme="blue" onClick={handleReadMoreClick}>
                    View
                  </Button>
                  <Modal isOpen={isOpen} onClose={handleClose} size="lg">
                    <ModalOverlay />
                    <ModalContent>
                      <ModalHeader>Category Details</ModalHeader>
                      <ModalCloseButton />
                      <ModalBody
                        style={{
                          maxHeight: '400px', // Set a maximum height for the content
                          overflowY: 'auto',  // Enable vertical scrolling
                        }}
                      >
                        {value ? (
                          <ReactJson
                            src={value}
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
          },
          {
            accessorKey: 'file_stats.stats_data.subcategoryGroups',
            header: 'Sub-Category',
            cell: (info) => {
              const [isOpen, setIsOpen] = useState(false);
              const value = info.getValue();
          
              const handleReadMoreClick = () => {
                setIsOpen(true);
              };
          
              const handleClose = () => {
                setIsOpen(false);
              };
          
              return (
                <>
                  <Button variant="link" colorScheme="blue" onClick={handleReadMoreClick}>
                    View
                  </Button>
                  <Modal isOpen={isOpen} onClose={handleClose} size="lg">
                    <ModalOverlay />
                    <ModalContent>
                      <ModalHeader>Subcategory Group Details</ModalHeader>
                      <ModalCloseButton />
                      <ModalBody
                        style={{
                          maxHeight: '400px', // Set a maximum height for the content
                          overflowY: 'auto',  // Enable vertical scrolling
                        }}
                      >
                        {value ? (
                          <ReactJson
                            src={value}
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
          },
          {
            accessorKey: 'file_stats.stats_data.difficultyLevel',
            header: 'Difficulty Distribution',
            cell: (info) => {
              const [isOpen, setIsOpen] = useState(false);
              const value = info.getValue();
          
              const handleReadMoreClick = () => {
                setIsOpen(true);
              };
          
              const handleClose = () => {
                setIsOpen(false);
              };
          
              return (
                <>
                  <Button variant="link" colorScheme="blue" onClick={handleReadMoreClick}>
                    View
                  </Button>
                  <Modal isOpen={isOpen} onClose={handleClose} size="lg">
                    <ModalOverlay />
                    <ModalContent>
                      <ModalHeader>Subcategory Group Details</ModalHeader>
                      <ModalCloseButton />
                      <ModalBody
                        style={{
                          maxHeight: '400px', // Set a maximum height for the content
                          overflowY: 'auto',  // Enable vertical scrolling
                        }}
                      >
                        {value ? (
                          <ReactJson
                            src={value}
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
          },
          {
            accessorKey: 'file_stats.stats_data.mainCodingLanguageGroups',
            header: 'Language Distribution',
            cell: (info) => {
              const [isOpen, setIsOpen] = useState(false);
              const value = info.getValue();
          
              const handleReadMoreClick = () => {
                setIsOpen(true);
              };
          
              const handleClose = () => {
                setIsOpen(false);
              };
          
              return (
                <>
                  <Button variant="link" colorScheme="blue" onClick={handleReadMoreClick}>
                    View
                  </Button>
                  <Modal isOpen={isOpen} onClose={handleClose} size="lg">
                    <ModalOverlay />
                    <ModalContent>
                      <ModalHeader>Subcategory Group Details</ModalHeader>
                      <ModalCloseButton />
                      <ModalBody
                        style={{
                          maxHeight: '400px', // Set a maximum height for the content
                          overflowY: 'auto',  // Enable vertical scrolling
                        }}
                      >
                        {value ? (
                          <ReactJson
                            src={value}
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
          },
        ],
        []
      );

  return (
    <Box p={4}>
      <Flex p="10px 0" alignItems={'center'} gap={'10px'}>
        <Text>Filter by WorkStream</Text>
        <Input
          border="1px solid lightgray"
          width="25%"
          placeholder="Search by workstream"
          name="workstream"
          value={workStream}
          onChange={(e) => {
            setWorkStream(e.target.value);
          }}
        />
      </Flex>
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
      />
      <CustomModal
        onClose={handleModalClose}
        isOpen={isOpen}
        header={'File Content'}
      >
        {fileContentLoading ? (
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
          <ReactJson enableClipboard={false} src={fileData} />
        )}
      </CustomModal>
    </Box>
  );
}
export { Dashboard as Component };
