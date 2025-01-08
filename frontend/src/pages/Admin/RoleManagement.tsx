import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Box,
  Text,
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Input,
  AlertDialog,
  AlertDialogOverlay,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
  useDisclosure,
  Checkbox,
  Stack,
  FormControl,
  FormErrorMessage,
  ModalCloseButton,
  FormLabel,
  Divider,
  VStack,
  HStack,
  useToast,
} from '@chakra-ui/react';
import { Table } from '../../components/table/table';
import { ColumnDef } from '@tanstack/react-table';
import { FileInfo, ItemListQuery } from '../../types';
import { EMPTY_ROLES, useItemListQueryParams } from '../../hooks/query';
import {
  useListRolesQuery,
  useAddRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
} from './store';
const INITIAL_TABLE_STATE: ItemListQuery<FileInfo> = {
  page: 1,
  pageSize: 25,
  sorting: [{ id: 'created_at', desc: true }],
};

const RoleManagement = () => {
  const { query, setPage, setPageSize, setSorting } =
    useItemListQueryParams<FileInfo>(INITIAL_TABLE_STATE);
  const [roleId, setRoleId] = useState('');
  const [role_name, setRoleName] = useState('');
  const [description, setDescription] = useState('');

  const [selectAll, setSelectAll] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(true);

  const [permissions, setPermissions] = useState({
    logs: false, // Set logs permission to true by default
    upload_to_s3: false,
    user_management: false,
    download_from_s3: false,
    configuration: false,
    // role_management: false,
  });
  const [formErrors, setFormErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const {
    data = EMPTY_ROLES,
    isLoading,
    isError,
    error,
    refetch,
  } = useListRolesQuery({ query }, { refetchOnMountOrArgChange: true });
  const toast = useToast();

  const [selectedRole, setSelectedRole] = useState(null);
  const {
    isOpen: isFormOpen,
    onOpen: onFormOpen,
    onClose: onFormClose,
  } = useDisclosure();
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const [isEdit, setIsEdit] = useState(false);

  const [addRole] = useAddRoleMutation();
  const [updateRole] = useUpdateRoleMutation();
  const [deleteRole] = useDeleteRoleMutation();

  const [roleEdit, setRoleEdit] = useState({});
  const [isFormDirty, setIsFormDirty] = useState(false); // Tracks if the form has unsaved changes
  const [initialFormValues,setInitialFormValues]  = useState({role_name:'', description :'',permissions:{
    logs: false, // Set logs permission to true by default
    upload_to_s3: false,
    user_management: false,
    download_from_s3: false,
    configuration: false,
    // role_management: false,
  }})

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
            Role Name
          </Box>
        ),
        cell: (info) => <span>{info.getValue()}</span>,
        meta: {
          width: '150px',
        },
        enableSorting: false,
      },
      {
        accessorKey: 'description',
        header: () => (
          <Box
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            textTransform="capitalize"
          >
            Description
          </Box>
        ),
        cell: (info) => <span>{info.getValue()}</span>,
        meta: {
          width: '150px',
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
          const temp = new Date(row.updated_at);
          return temp.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
          });
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
          const temp = new Date(row.created_at);
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
      // {
      //   accessorKey: 'assigned_users',
      //   header: () => (
      //     <Box
      //       whiteSpace="nowrap"
      //       overflow="hidden"
      //       textOverflow="ellipsis"
      //       textTransform="capitalize"
      //     >
      //       Assigned Users
      //     </Box>
      //   ),
      //   cell: (info) => <span>{info.getValue()}</span>,
      //   enableSorting: true,
      // },
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
        meta: {
          width: '200px',
        },
        enableSorting: false,
        cell: (info) => {
          const role = info.row.original;
          return (
            <Box display="flex" gap="8px">
              <Button
                colorScheme="teal"
                size="sm"
                onClick={() => handleEditRole(role)}
              >
                Edit
              </Button>
              <Button
                colorScheme="red"
                size="sm"
                onClick={() => handleDeleteRole(role)}
                data={data?.roles}
              >
                Delete
              </Button>
            </Box>
          );
        },
      },
    ],
    []
  );
  
  useEffect(() => {
    setFormErrors({});
  }, []);
  const handleAddRole = () => {
    setFormErrors({});
    setPermissions({
      logs: false, // Set logs permission to true by default
      upload_to_s3: false,
      user_management: false,
      download_from_s3: false,
      configuration: false,
      // role_management: false,
    });
    setIsEdit(false);
    setRoleId('');
    setRoleName('');
    setDescription('');
    setSelectAll(false);
    setIsSubmitting(false);
    setSelectedRole(null); // Reset to create a new role
    onFormOpen();
  };

  const handleDeleteRole = (role) => {
    setSelectedRole(role); // Set selected role for deletion
    setRoleId(role.id);
    onDeleteOpen();
  };

  const handleEditRole = (role) => {
    setFormErrors({});
    setIsEdit(true);
    setFormErrors({});
    setIsFormDirty(true);

    if (role && role.permissions && typeof role.permissions === 'object') {
      const updatedPermissions = {
        logs: role.permissions.logs || false,
        upload_to_s3: role.permissions.upload_to_s3 || false,
        user_management: role.permissions.user_management || false,
        download_from_s3: role.permissions.download_from_s3 || false,
        configuration: role.permissions.configuration || false,
        // role_management: role.permissions.role_management || false,
      };
      setPermissions(updatedPermissions);
      setSelectAll(
        Object.values(updatedPermissions).every(
          (permission) => permission === true
        )
      );
      setInitialFormValues({
        role_name: role.name || '',
        description: role.description,
        permissions:updatedPermissions
      });
    }
    setSelectedRole(role); // Set selected role for editing
    setRoleId(role.id);
    setRoleName(role.name);
    setDescription(role.description);
    onFormOpen();
    // Set initial values to ensure that they are tracked when checking if the form is dirty
   
  };

  useEffect(() => {
    if (isEdit) {
      setRoleName(role_name);
      setDescription(description);
      setPermissions(permissions);
      setSelectAll(Object.values(permissions).every(val => val));
    } else {
      setRoleName('');
      setDescription('');
      setPermissions(permissions);
      setSelectAll(false);
    }
  }, [isEdit, data]);

  const handleSelectAll = () => {
    const toggleValue = !selectAll;
    const updatedPermissions = { ...permissions };

    // Toggle permissions based on "Select All"
    Object.keys(updatedPermissions).forEach((key) => {
      updatedPermissions[key] = toggleValue;
    });

    setPermissions(updatedPermissions);
    setSelectAll(toggleValue);
    validateForm('all',updatedPermissions);
  };

  const handleCheckboxChange = (permission) => {
    setIsSubmitting(false);
    setPermissions((prev) => {
      const updatedPermissions = { ...prev, [permission]: !prev[permission] };  
      const allSelected = Object.values(updatedPermissions).every(
        (value) => value === true
      );
  
      setSelectAll(allSelected);
      checkFormDirty();
      const selectedPermissions = Object.values(updatedPermissions).some(
        (permission) => permission === true
      );
      validateForm('permission',selectedPermissions?updatedPermissions:false);
      return updatedPermissions; // Returning the updated state
    });
  };
  

  const validateForm = (type,updatedPermissions = false) => {
    const errors = {};

    if(type == 'role_name' || type =='form'){
      if (role_name.trim() === '') {
        errors.role_name = 'Role Name cannot be empty';
      } else if (/^\d+$/.test(role_name)) {
        errors.role_name = 'Role Name cannot be a number';
      } else if (role_name.length < 5 || role_name.length > 50) {
        errors.role_name = 'Role Name must be between 5 and 50 characters';
      }  
    }
    if(type =='description' || type =='form'){
      if (description.trim() === '') {
        errors.description = 'Description cannot be empty';
      } else if (description.length < 5 || description.length > 200) {
        errors.description = 'Description must be between 5 and 200 characters';
      }
    }
   
    
   if(typeof updatedPermissions == 'object' && (type =='all'  || type == 'permission' || type =='form')){
    const selectedPermissions = Object.values(updatedPermissions).some(
      (permission) => permission === true
    );
    if (!selectedPermissions && !selectAll) {
      errors.permissions = 'At least one permission must be selected';
    }
   }
   else if(type =='all'  || type == 'permission' || type =='form'){
    const selectedPermissions = Object.values(permissions).some(
      (permission) => permission === true
    );
    if (!selectedPermissions && !selectAll) {
      errors.permissions = 'At least one permission must be selected';
    }
   }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  useEffect(()=>{
     setPermissions(permissions)
  },[permissions])
  const handleSave = async () => {
    try {
      if (validateForm('form')) {
        setLoading(true);
        // Prepare the request body
        const body = {
          role_name,
          permissions,
          description,
        };
        // Sending the addRole request
        const res = await addRole({
          body: {
            name: role_name,
            description,
            permissions,
          },
          query,
        }).unwrap();

        if (res) {
          // If the request is successful, show a toast and reset state
          toast({
            title: 'Role Created',
            description: 'Role Created successfully!',
            status: 'success',
            duration: 2000,
            isClosable: true,
            position: 'top',
          });

          // Reset inputs and permissions to default state
          setDescription('');
          setRoleName('');
          setPermissions({
            logs: false, // Set logs permission to true by default
            upload_to_s3: false,
            user_management: false,
            download_from_s3: false,
            configuration: false,
            // role_management: false,
          });

          // Close modal after successful save
          onFormClose();
          // Refetch data or any updates needed
          refetch();
        }
      }
    } catch (error) {
      // Handle any errors that occur during the addRole call
      console.error('Error adding role:', error);
      toast({
        title: 'Failed to add role!',
        description:
          error.data?.detail || 'An error occurred while adding the role.',
        status: 'error',
        duration: 2000,
        position: 'top',
        isClosable: true,
      });
    } finally {
      // Stop the loading state, regardless of success or failure
      setLoading(false);
      setIsSubmitting(true)
    }
  };
  const handleUpdateRole = async () => {
    try {
      if (validateForm('form')) {
        setLoading(true);

        // Prepare the request body
        const body = {
          role_name,
          permissions,
          description,
        };

        // Sending the addRole request
        const res = await updateRole({
          roleId: parseInt(roleId),
          body: {
            name: role_name,
            description,
            permissions,
          },
          query,
        }).unwrap();

        if (res) {
          // If the request is successful, show a toast and reset state
          toast({
            title: 'Role Updated',
            description: 'Role updated successfully!',
            status: 'success',
            duration: 2000,
            isClosable: true,
            position: 'top',
          });

          // Reset inputs and permissions to default state
          setDescription('');
          setRoleName('');
          setPermissions({
            logs: false, // Set logs permission to true by default
            upload_to_s3: false,
            user_management: false,
            download_from_s3: false,
            configuration: false,
            // role_management: false,
          });
          localStorage.setItem('userPermissions', JSON.stringify(permissions)); // Store permissions in localStorage
          window.dispatchEvent(new Event('localStorageUpdated'));
          // Close modal after successful Update
          onFormClose();
          // Refetch data or any updates needed
          refetch();
          
        }
      }
    } catch (error) {
      // Handle any errors that occur during the updatRole call
      console.error('Error updating role:', error);
      toast({
        title: 'Failed to updat role!',
        description:
          error.data?.detail || 'An error occurred while updating the role.',
        status: 'error',
        duration: 2000,
        isClosable: true,
        position: 'top',
      });
    } finally {
      // Stop the loading state, regardless of success or failure
      setLoading(false);
    }
  };
  const checkFormDirty = () => {
    const hasChanged = 
    role_name != initialFormValues.role_name || 
    description != initialFormValues.description ||
    !arePermissionsEqual(permissions, initialFormValues.permissions);


     setIsFormDirty(!hasChanged);
  }
  const arePermissionsEqual = (currentPermissions, initialPermissions) => {
    // Check if both objects have the same keys
    const currentKeys = Object.keys(currentPermissions);
    const initialKeys = Object.keys(initialPermissions);
  
    if (currentKeys.length !== initialKeys.length) return false;
  
    // Compare values for each key
    return currentKeys.every(
      (key) =>
        key in initialPermissions && currentPermissions[key] === initialPermissions[key]
    );
  };
  
  
  useEffect(() => {
    checkFormDirty(); // Reevaluate form dirtiness if dependencies change
  }, [ role_name,description,permissions]);

  const DeleteConfirmDialog = ({ isOpen, onClose, role }) => {
    const cancelRef = useRef();

    const handleDelete = async () => {
      let res = {};
      try {
        onDeleteClose();
        // Sending the addRole request
        res = await deleteRole({
          roleId: parseInt(roleId),
          query,
        }).unwrap();
        // If the request is successful, show a toast and reset state
        toast({
          title: 'Role Deleted',
          description: 'Role deleted successfully!',
          status: 'error',
          position: 'top',
          duration: 4000,
          isClosable: true,
        });
        setRoleId('');
        refetch();
      } catch (err) {
        toast({
          title: 'Error in delete!',
          description: err.data?.detail,
          status: 'error',
          position: 'top',
          duration: 4000,
          isClosable: true,
        });
        refetch();
      }
    };

    return (
      <AlertDialog
        isOpen={isOpen}
        leastDestructiveRef={cancelRef}
        onClose={onClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Delete Role
            </AlertDialogHeader>
            <AlertDialogBody>
              Are you sure you want to delete the role "{role?.name}"? This
              action cannot be undone.
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onClose}>
                Cancel
              </Button>
              <Button colorScheme="red" onClick={handleDelete} ml={3}>
                Delete
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    );
  };

  return (
    <Box>
      {/* <Text fontSize="2xl" mb={4}>
        Role Management CRUD
      </Text> */}
        <Modal isOpen={isFormOpen} onClose={()=>{
          onFormClose()
          setIsSubmitting(true)
        }} size="4xl">
      <ModalOverlay />
      <ModalContent borderRadius="lg" boxShadow="lg">
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
          {isEdit ? 'Update Role' : 'Create Role'}
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody p={6} bg="white">
          {/* Role Name */}
          <FormControl mb={6} isInvalid={!!formErrors.role_name}>
            <FormLabel fontWeight="medium" color="gray.700" mb={2}>
              Role Name
            </FormLabel>
            <Input
              placeholder="Enter role name"
              value={role_name}
              onChange={(e) => {
                setRoleName(e.target.value);
                setIsSubmitting(false);
                checkFormDirty()

                if (formErrors.role_name) {
                  validateForm('role_name');
                }
              }}
              focusBorderColor="blue.500"
              border="1px solid"
              borderColor="gray.300"
              borderRadius="md"
              _hover={{ borderColor: 'gray.400' }}
            />
            {formErrors.role_name && <FormErrorMessage>{formErrors.role_name}</FormErrorMessage>}
          </FormControl>

          {/* Description */}
          <FormControl mb={6} isInvalid={!!formErrors.description}>
            <FormLabel fontWeight="medium" color="gray.700" mb={2}>
              Description
            </FormLabel>
            <Input
              placeholder="Enter description"
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                checkFormDirty()

                setIsSubmitting(false);
                if (formErrors.description) {
                  validateForm('description');
                }
              }}
              focusBorderColor="blue.500"
              border="1px solid"
              borderColor="gray.300"
              borderRadius="md"
              _hover={{ borderColor: 'gray.400' }}
            />
            {formErrors.description && <FormErrorMessage>{formErrors.description}</FormErrorMessage>}
          </FormControl>

          <Text fontWeight="semibold" color="gray.700" mb={3}>
            Permissions
          </Text>

          <Box border="1px solid" borderColor="gray.200" borderRadius="md" p={4} bg="gray.50">
            <Checkbox
              isChecked={selectAll}
              onChange={handleSelectAll}
              colorScheme="blue"
              fontWeight="bold"
              size="lg"
              mb={4}
            >
              Select All
            </Checkbox>
            <Divider mb={3} />
            <VStack align="start" spacing={3}>
              {/* Render the individual permission checkboxes */}
              {['user_management', 'logs', 'upload_to_s3', 'download_from_s3', 'configuration'].map((permission) => (
                  <Checkbox
                    key={permission}
                    isChecked={permissions[permission]}
                    onChange={() => {
                      handleCheckboxChange(permission)
                    }}
                    colorScheme="blue"
                    fontWeight="medium"
                    size="lg"
                  >
                    {permission
                        .split('_')  // Split string by underscore
                        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())  // Capitalize each word
                        .join(' ')}  
                  </Checkbox>
                ))}

            </VStack>
          </Box>

          {formErrors.permissions && (
            <Text color="red.500" fontSize="sm">
              {formErrors.permissions}
            </Text>
          )}
        </ModalBody>

        <ModalFooter bg="gray.50" borderTop="1px solid" borderColor="gray.200">
          <Button
            colorScheme="blue"
            mr={3}
            onClick={(e) => {
              e.preventDefault();
              if (isEdit) {
                handleUpdateRole(); // Update role if in edit mode
              } else {
                handleSave(); // Submit form if in add mode
              }
            }}
            px={6}
            borderRadius="full"
            isDisabled={isFormDirty}
            isLoading={loading}
          >
            Save
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              onFormClose();
              setIsSubmitting(true);
            }}
            borderRadius="full"
          >
            Cancel
          </Button>
        </ModalFooter>
      </ModalContent>
       </Modal>

      <Button colorScheme="blue" onClick={handleAddRole} mb={4}>
        Add Role
      </Button>
      <Table
        id="roles"
        columns={columns}
        data={data?.roles}
        isLoading={isLoading}
        pageCount={data?.pageCount}
        page={query.page}
        pageSize={query.pageSize}
        sorting={query.sorting}
        setPage={setPage}
        setPageSize={setPageSize}
        setSorting={setSorting}
      />

      <DeleteConfirmDialog
        isOpen={isDeleteOpen}
        onClose={onDeleteClose}
        role={selectedRole}
      />
    </Box>
  );
};

export default RoleManagement;
