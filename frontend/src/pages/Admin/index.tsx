import {
  Box,
  Button,
  CircularProgress,
  Flex,
  Input,
  Text,
  VStack,
  useToast,
  FormControl,
  FormLabel,
  FormErrorMessage,
  Switch,
  Tooltip,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Select,
  ModalFooter,
} from '@chakra-ui/react';
import { Table } from '../../components/table/table';
import { useEffect, useMemo, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { FaUserCircle } from 'react-icons/fa';
import { FileInfo, ItemListQuery } from '../../types';
import {
  EMPTY_USERS,
  EMPTY_ROLES,
  useItemListQueryParams,
} from '../../hooks/query';
import {
  useListUsersQuery,
  useAddUserMutation,
  useUpdateUserMutation,
  useUpdateUserStatusMutation,
  useListRolesQuery,
  useGeteRoleListQuery,
} from './store';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
} from '@chakra-ui/react';
import RoleManagement from './RoleManagement';

const INITIAL_TABLE_STATE: ItemListQuery<FileInfo> = {
  page: 1,
  pageSize: 25,
  sorting: [{ id: 'created_at', desc: true }],
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

function Admin() {
  const {
    query,
    setPage,
    setPageSize,
    setSorting,
    setDateFilter,
    setRoleIdFilter,
  } = useItemListQueryParams<FileInfo>(INITIAL_TABLE_STATE);

  const toast = useToast();

  const [isDataLoading, setIsDataLoading] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('');
  const [formErrors, setFormErrors] = useState({
    name: '',
    email: '',
    role: '',
  });
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [addUser] = useAddUserMutation();
  const [updateUser] = useUpdateUserMutation();
  const [updateUserStatus] = useUpdateUserStatusMutation();
  const [roleId, setRoleId] = useState('');
  const [isEditMode, setIsEditModel] = useState(false);
  const [userId, setUserId] = useState('');
  const [isActive, setIsActive] = useState(false);
  const [userPermissions, setUserPermissions] = useState({}); // State to manage the modal visibility
  const [isUserManagement, setIsUserManagement] = useState({}); // State to manage the modal visibility

  const [isFormDirty, setIsFormDirty] = useState(false); // Tracks if the form has unsaved changes

  const [initialFormValues, setInitialFormValues] = useState({
    role: '',
    isActive: '',
  });
  useEffect(() => {
    setIsEditModel(false);
    const storedUserPermissions =
      JSON.parse(localStorage.getItem('userPermissions')) || {};
    setUserPermissions(storedUserPermissions);

    // Set states based on permissions
    setIsUserManagement(!!storedUserPermissions['user_management']);
  }, []); // Run only once

  // Run queries only when permissions are fully determined
  const shouldFetchUsers = isUserManagement === true;

  const {
    data = EMPTY_USERS,
    isLoading,
    refetch,
  } = useListUsersQuery(
    { query },
    { skip: !shouldFetchUsers, refetchOnMountOrArgChange: true }
  );
  const {
    data: rolesData = EMPTY_ROLES,
    isLoading: isRoleLoading,
    refetch: refetchRoles,
  } = useListRolesQuery(
    { query },
    { skip: !shouldFetchUsers, refetchOnMountOrArgChange: true }
  );

  const {
    data: rolesListData = EMPTY_ROLES,
    isLoading: isRoleListLoading,
    refetch: refetchRolesList,
  } = useGeteRoleListQuery(
    { query },
    { skip: !shouldFetchUsers, refetchOnMountOrArgChange: true }
  );

  const handleToggle = async (id: number, newState: boolean) => {
    try {
      // Call the API to update the server with the new state
      await updateUserStatus({
        user_id: id,
        body: {
          is_active: newState, // Use `is_active` instead of `status`
        },
      }).unwrap();

      // Show a success toast
      toast({
        title: newState ? 'Activate' : 'Deactivate',
        description: `User successfully updated to ${
          newState ? 'Activate' : 'Deactivate'
        }`,
        status: 'success',
        duration: 2000,
        isClosable: true,
        position: 'top',
      });
    } catch (error) {
      // Show an error toast if the update fails
      toast({
        title: 'Failed to update user state',
        description:
          error?.message || 'Something went wrong. Please try again later.',
        status: 'error',
        duration: 5000,
        isClosable: true,
        position: 'top',
      });
    } finally {
      // Refetch data to reflect the updated state
      refetch();
    }
  };
  const options = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  };
  useEffect(() => {
    if (rolesData.roles?.length && !role) {
      // setRole(rolesData.roles[0].id);
    }
  }, [rolesData, role]);

  const columns = useMemo<ColumnDef<any>[]>(
    () => [
      {
        accessorKey: 'name',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Name
          </Box>
        ),
        cell: (info) => <span>{info.getValue()}</span>,
        enableSorting: false,
        meta: {
          width: '5px',
        },
      },
      {
        accessorKey: 'email',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Email
          </Box>
        ),
        cell: (info) => <span>{info.getValue()}</span>,
        meta: {
          width: '5px',
        },
        enableSorting: false,
      },
      {
        accessorKey: 'role',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Role
          </Box>
        ),
        cell: (info) => <span>{info.getValue()?.name}</span>,
        enableSorting: false,
        meta: {
          width: '50px',
        },
      },
      {
        accessorKey: 'last_login_at',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Last Login
          </Box>
        ),
        accessorFn: (row) => {
          if (row.last_login_at) {
            const temp = new Date(row.last_login_at);
            return temp.toLocaleString('en-US', options);
          } else {
            return 'NA';
          }
        },
        cell: (info) => <span>{info.getValue()}</span>,
        enableSorting: true,
        meta: {
          width: '150px',
        },
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
          if (row.updated_at) {
            const temp = new Date(row.updated_at);
            return temp.toLocaleString('en-US', options);
          } else {
            return 'NA';
          }
        },
        cell: (info) => <span>{info.getValue()}</span>,
        meta: {
          width: '150px',
        },
        enableSorting: false,
      },
      {
        accessorKey: 'created_at',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Created At
          </Box>
        ),
        accessorFn: (row) => {
          if (row.created_at) {
            const temp = new Date(row.created_at);
            return temp.toLocaleString('en-US', options);
          } else {
            return 'NA';
          }
        },
        cell: (info) => <span>{info.getValue()}</span>,
        enableSorting: true,
        meta: {
          width: '150px',
        },
      },
      {
        accessorKey: 'id',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Active
          </Box>
        ),
        enableSorting: false,
        meta: {
          width: '50px',
        },
        cell: (info) => {
          const isActive = info.row.original.is_active;
          const tooltipLabel = isActive
            ? 'Deactivate this item'
            : 'Activate this item';
          return (
            <Tooltip label={tooltipLabel} aria-label={tooltipLabel}>
              <span>
                <Switch
                  isChecked={isActive}
                  onChange={() => handleToggle(info.getValue(), !isActive)}
                  colorScheme={isActive ? 'green' : 'red'}
                  size="md"
                />
              </span>
            </Tooltip>
          );
        },
      },
      {
        accessorKey: 'actions',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Actions
          </Box>
        ),
        cell: (info) => {
          const user = info.row.original;

          const openEditModal = (user) => {
            setIsFormDirty(true);
            setIsSubmitting(true);
            setIsEditModel(true);
            setIsActive(user.is_active);
            setName(user.name);
            setEmail(user.email);
            setRole(user.role?.id || '');
            setUserId(user.id || '');

            // Set initial values to ensure that they are tracked when checking if the form is dirty
            setInitialFormValues({
              role: user.role?.id || '',
              isActive: user.is_active,
            });

            setIsAddModalOpen(true);
          };

          const userPermissionsData =
            JSON.parse(localStorage.getItem('userPermissions')) || {};
          return (
            <>
              <Button
                onClick={() => openEditModal(user)}
                colorScheme="blue"
                size="sm"
                isDisabled={!userPermissionsData.user_management}
              >
                Edit
              </Button>
            </>
          );
        },
        enableSorting: false,
      },
    ],
    []
  );

  const handleRoleChange = async () => {
    const newErrors = {};
    // Validate role selection
    // Basic validation for name, email, and role
    let isValid = true;

    if (!role) {
      newErrors.role = 'Role is required';
      isValid = false;
    }

    setFormErrors(newErrors);
    if (isValid) {
      try {
        // Call the API to update the role in the backend
        await updateUser({
          user_id: userId,
          body: {
            role_id: parseInt(role), // Assuming role field is in the request body
            is_active: isActive,
          },
        }).unwrap();
        // Show a success toast
        toast({
          title: `Role Updated`,
          description: `User's successfully updated`,
          status: 'success',
          duration: 2000,
          isClosable: true,
          position: 'top',
        });

        setIsEditModel(false);
        setName('');
        setEmail('');
        setRole('');
        setUserId('');
        setIsAddModalOpen(false); // Open the modal
      } catch (error) {
        // Show an error toast if the update fails
        setIsEditModel(false); // Switch to edit mode
        toast({
          title: 'Failed to update role',
          description:
            error?.message || 'Something went wrong. Please try again later.',
          status: 'error',
          duration: 5000,
          isClosable: true,
          position: 'top',
        });
      } finally {
        // Refetch data to reflect the updated role
        refetch();
      }
    }
  };

  const handleChange = (event: any) => {
    setRoleId(event.target.value);
  };
  const currentDate = new Date().toISOString().split('T')[0]; // Current date in YYYY-MM-DD format
  const minDate = new Date();
  minDate.setFullYear(minDate.getFullYear() - 1); // Subtract 1 year from the current date
  const minDateString = minDate.toISOString().split('T')[0]; // Minimum date in YYYY-MM-DD format

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newStartDate = e.target.value;
    if (!endDate || newStartDate <= endDate) {
      setStartDate(newStartDate); // Only update if the new start date is <= end date
    } else {
      alert('Start date must be less than or equal to the end date.');
    }
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEndDate = e.target.value;
    if (!startDate || newEndDate >= startDate) {
      setEndDate(newEndDate); // Only update if the new end date is >= start date
    } else {
      alert('End date must be greater than or equal to the start date.');
    }
  };

  // Track changes to roleId
  useEffect(() => {
    setIsDataLoading(true); // Set loading state when roleId changes
    setRoleIdFilter(parseInt(roleId));

    setTimeout(() => {
      setIsDataLoading(false); // Set loading state to false after a delay
    }, 800);
  }, [roleId]);

  // Track changes to startDate or endDate
  useEffect(() => {
    setIsDataLoading(true); // Show loader when dates change
    setDateFilter(startDate, endDate);
    setTimeout(() => {
      setIsDataLoading(false); // Hide loader after a short delay
    }, 800);
  }, [startDate, endDate]);

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Basic validation for name, email, and role
    let isValid = true;
    const newErrors = { name: '', email: '', role: '' };

    // Validate name (5-20 characters)
    if (!name) {
      newErrors.name = 'Name is required';
      isValid = false;
    } else if (name.length < 3 || name.length > 20) {
      newErrors.name = 'Name must be between 3 and 20 characters';
      isValid = false;
    } else if (!/^[a-zA-Z\s]+$/.test(name)) {
      // Updated regex to allow only letters and spaces
      newErrors.name = 'Name cannot contain special characters or numbers';
      isValid = false;
    } else if (/\d/.test(name)) {
      // Ensures name doesn't contain numbers
      newErrors.name = 'Name cannot contain numbers';
      isValid = false;
    }

    // Validate email domain
    if (!email) {
      newErrors.email = 'Email is required';
      isValid = false;
    } else if (!/^[^\s@]+@turing\.com$/.test(email)) {
      newErrors.email = 'Email must belong to turing.com domain';
      isValid = false;
    }

    // Validate role selection
    if (!role) {
      newErrors.role = 'Role is required';
      isValid = false;
    }

    setFormErrors(newErrors);

    if (isValid) {
      setIsSubmitting(true);
      try {
        const res = await addUser({
          body: {
            name,
            email,
            role_id: parseInt(role), // Assuming role is set to the selected role ID
            is_active: isActive,
          },
          query,
        }).unwrap();
        setIsSubmitting(false);

        toast({
          title: 'User Added!',
          description: 'User added successfully!',
          status: 'success',
          duration: 2000,
          isClosable: true,
          position: 'top',
        });
        setName('');
        setEmail('');
        setRole(''); // Clear the selected role after successful submission
        setIsAddModalOpen(false);
        refetch();
      } catch (error) {
        setIsSubmitting(false);

        toast({
          title: 'Error adding user',
          description: error.data.detail,
          status: 'error',
          duration: 3000,
          isClosable: true,
          position: 'top',
        });
        setIsAddModalOpen(false);
      }
    }
  };

  const handleFieldChange = (e, field) => {
    const value = e.target.value;
    switch (field) {
      case 'name':
        setName(value);
        break;
      case 'email':
        setEmail(value);
        break;
      case 'role':
        setRole(value);
        break;
      default:
        break;
    }

    setFormErrors((prevErrors) => ({
      ...prevErrors,
      [field]: value.trim()
        ? ''
        : `${field.charAt(0).toUpperCase() + field.slice(1)} is required`,
    }));

    checkFormDirty();
  };
  useEffect(() => {
    checkFormDirty(); // Reevaluate form dirtiness if dependencies change
  }, [role, isActive]);

  const handleSwitchChange = (e) => {
    const newIsActive = e.target.checked;
    setIsActive(newIsActive);
    checkFormDirty();
  };

  const checkFormDirty = () => {
    const hasChanged =
      role != initialFormValues.role || isActive != initialFormValues.isActive;

    setIsFormDirty(!hasChanged);
  }; // Adjust debounce delay as needed

  const handleTabClick = () => {
    // Trigger your refetch call here
    refetchRoles();
    refetchRolesList();
  };

  function resetForm() {
    setName('');
    setEmail('');
    setRole('');
    setIsActive(false);
    setFormErrors({});
  }

  return (
    <Box 
      p={{ base: 0, md: 4 }}
      pt={{ base: 5, md: 6 }}
    >
      <Tabs>
        <TabList>
          {userPermissions.user_management && (
            <Tab onClick={handleTabClick}>User Assigned List</Tab>
          )}

          {userPermissions.user_management && <Tab>Role Management</Tab>}

          {/* <Tab>Permissions Management</Tab> */}
        </TabList>

        <TabPanels>
          {/* First Tab: User Assigned List */}
          {userPermissions.user_management && (
            <TabPanel>
              <Box p={4}>
                <Flex
                  p={{ base: '10px', md: '10px 0' }}
                  gap={{ base: '10px', md: '20px' }}
                  direction={{ base: 'column', md: 'row' }}
                  w="100%" 
                  alignItems="center"
                >
                  <Text>Filter by Role</Text>
                  <Select
                    placeholder="Select Role"
                    value={roleId}
                    onChange={handleChange}
                    width={{ base: '100%', md: '15%' }}
                  >
                    {rolesListData?.length > 0 ? (
                      rolesListData.map((roleItem) => (
                        <option key={roleItem.id} value={roleItem.id}>
                          {roleItem.name}
                        </option>
                      ))
                    ) : (
                      <option disabled>No roles available</option>
                    )}
                  </Select>
                  <Text>Start Date</Text>
                  <Input
                    type="date"
                    border="1px solid lightgray"
                    width={{ base: '100%', md: '20%' }}
                    name="start_date"
                    value={startDate || ''} // Handle null state gracefully
                    onChange={handleStartDateChange}
                    max={endDate || currentDate} // Start date cannot be after the end date
                    min={minDateString} // Minimum allowed start date
                  />
                  <Text>End Date</Text>
                  <Input
                    type="date"
                    border="1px solid lightgray"
                    width={{ base: '100%', md: '20%' }}
                    name="end_date"
                    value={endDate || ''} // Handle null state gracefully
                    onChange={handleEndDateChange}
                    max={currentDate} // End date cannot be after today
                    min={startDate || minDateString} // End date cannot be before the start date
                  />{' '}
                  {/* Clear Filters Button */}
                  <Button
                    onClick={() => {
                      setRoleId('');
                      setStartDate('');
                      setEndDate('');
                    }}
                    variant="outline"
                    colorScheme="blue"
                    width={{ base: '100%', md: 'auto' }}
                  >
                    Clear Filters
                  </Button>
                  {/* </Flex>
              <Flex justify="flex-end" mb={4}> */}
                  <Button
                    onClick={() => {
                      setIsAddModalOpen(true); // Opens the modal
                      setIsEditModel(false); // Switch to edit mode
                      setName(''); // Set name in form
                      setEmail(''); // Set email in form
                      setRole(''); // Set role in form
                      setUserId(''); // Set role in form
                    }}
                    colorScheme="teal"
                    width={{ base: '100%', md: 'auto' }}
                  >
                    Add User
                  </Button>
                </Flex>

                {/* Add User Modal */}

                <Modal
                  isOpen={isAddModalOpen}
                  onClose={() => {
                    setIsAddModalOpen(false);
                    resetForm();
                  }}
                  size="4xl"
                >
                  <ModalOverlay />
                  <ModalContent borderRadius="lg" boxShadow="lg" padding="4">
                    <ModalHeader
                      bg="gray.50"
                      borderTopRadius="lg"
                      borderBottom="1px solid"
                      borderColor="gray.200"
                      color="gray.800"
                      fontSize="lg"
                      fontWeight="bold"
                      p={4}
                    >
                      {isEditMode ? 'Edit User' : 'Add User'}
                    </ModalHeader>

                    <ModalBody border="1px solid" borderColor="gray.300">
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          if (isEditMode) {
                            handleRoleChange(); // Update role if in edit mode
                          } else {
                            handleFormSubmit(e); // Submit form if in add mode
                          }
                        }}
                      >
                        <VStack spacing={6} align="stretch">
                          {/* Name Field */}
                          <FormControl isInvalid={!!formErrors.name}>
                            <FormLabel
                              htmlFor="name"
                              fontSize="sm"
                              fontWeight="medium"
                              color="gray.600"
                            >
                              Name
                            </FormLabel>
                            <Input
                              id="name"
                              type="text"
                              value={name}
                              onChange={(e) => handleFieldChange(e, 'name')}
                              placeholder="Enter your name"
                              isDisabled={isEditMode}
                              borderColor="gray.300"
                              borderWidth="1px"
                              focusBorderColor="blue.400"
                              borderRadius="md"
                              size="md"
                              padding="8px"
                            />
                            <FormErrorMessage>
                              {formErrors.name}
                            </FormErrorMessage>
                          </FormControl>

                          {/* Email Field */}
                          <FormControl isInvalid={!!formErrors.email}>
                            <FormLabel
                              htmlFor="email"
                              fontSize="sm"
                              fontWeight="medium"
                              color="gray.600"
                            >
                              Email
                            </FormLabel>
                            <Input
                              id="email"
                              type="email"
                              value={email}
                              onChange={(e) => handleFieldChange(e, 'email')}
                              placeholder="Enter your email"
                              borderColor="gray.300"
                              borderWidth="1px"
                              focusBorderColor="blue.400"
                              borderRadius="md"
                              size="md"
                              padding="8px"
                              isDisabled={isEditMode}
                            />
                            <FormErrorMessage>
                              {formErrors.email}
                            </FormErrorMessage>
                          </FormControl>

                          {/* Role Field */}
                          <FormControl isInvalid={!!formErrors.role}>
                            <FormLabel
                              htmlFor="role"
                              fontSize="sm"
                              fontWeight="medium"
                              color="gray.600"
                            >
                              Role
                            </FormLabel>
                            <Select
                              id="role"
                              value={role}
                              onChange={(e) => handleFieldChange(e, 'role')}
                              placeholder="Select a role"
                              borderColor="gray.300"
                              borderWidth="1px"
                              focusBorderColor="blue.400"
                              borderRadius="md"
                              size="md"
                            >
                              {rolesListData?.length > 0 ? (
                                rolesListData.map((roleItem) => (
                                  <option key={roleItem.id} value={roleItem.id}>
                                    {roleItem.name}
                                  </option>
                                ))
                              ) : (
                                <option disabled>No roles available</option>
                              )}
                            </Select>
                            <FormErrorMessage>
                              {formErrors.role}
                            </FormErrorMessage>
                          </FormControl>

                          {/* Active Toggle */}
                          <FormControl>
                            <FormLabel
                              htmlFor="active"
                              fontSize="sm"
                              fontWeight="medium"
                              color="gray.600"
                            >
                              Active
                            </FormLabel>
                            <Switch
                              id="active"
                              isChecked={isActive}
                              onChange={handleSwitchChange}
                              colorScheme={isActive ? 'green' : 'red'}
                              size="lg"
                            />
                          </FormControl>
                        </VStack>
                      </form>
                    </ModalBody>

                    <ModalFooter
                      bg="gray.50"
                      borderTop="1px solid"
                      borderColor="gray.200"
                    >
                      <Button
                        colorScheme="blue"
                        mr={3}
                        onClick={(e) => {
                          e.preventDefault();
                          if (isEditMode) {
                            handleRoleChange(); // Update role if in edit mode
                          } else {
                            handleFormSubmit(e); // Submit form if in add mode
                          }
                        }}
                        px={6}
                        borderRadius="full"
                        isDisabled={isFormDirty} // Disable button if form hasn't changed
                      >
                        Save
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => {
                          setIsAddModalOpen(false);
                          resetForm();
                        }}
                        borderRadius="full"
                      >
                        Cancel
                      </Button>
                    </ModalFooter>
                  </ModalContent>
                </Modal>

                {/* Existing Code for Table */}

                {isDataLoading ? (
                  <Loader />
                ) : (
                  // Your other component content goes here
                  <Table
                    id="usersList"
                    columns={columns}
                    data={data?.users}
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
            </TabPanel>
          )}

          {/* Second Tab: Create Role */}
          {userPermissions.user_management && (
            <TabPanel>
              <Box>
                <RoleManagement />
              </Box>
            </TabPanel>
          )}
        </TabPanels>
      </Tabs>
    </Box>
  );
}

export { Admin as Component };
