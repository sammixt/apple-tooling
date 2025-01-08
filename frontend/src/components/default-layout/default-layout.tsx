import React, { useCallback, useEffect, useState } from 'react';
import {
  Avatar,
  Box,
  Button,
  Flex,
  Image,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Spacer,
  Switch,
  Text,
} from '@chakra-ui/react';
import TuringLogo from './assets/TuringLogo.png';
import { Outlet, useNavigate } from 'react-router-dom';
import { clearDetails, getProfile } from '../../features/auth/store';
import { useAppDispatch, useAppSelector } from '../../hooks/store';
import { DASHBOARD,ACTIVITYLOGS, LOGIN, UPLOAD, LOGS, NEWDASHBOARD, ADMIN } from '../../app/path';
import ConfigurationModal from './configuration-modal';
import TokenModal from './TokenModal';

function DefaultLayout() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const profile = useAppSelector(getProfile);

  const [isNewDashboardEnabled, setIsNewDashboardEnabled] = useState(true); // Default is set to true to show New Dashboard by default
  const [isModalOpen, setIsModalOpen] = useState(false); // State to manage the modal visibility
  const [userPermissions, setUserPermissions] = useState({}); // State to manage the modal visibility
  const [isTokenModalOpen, setIsTokenModalOpen] = useState(false); // State to manage the modal visibility

  const openTokenModal = () => {
    setIsTokenModalOpen(true)
  }

  const handleLogout = useCallback(() => {
    dispatch(clearDetails());
    navigate(LOGIN);
  }, [dispatch, navigate]);

  const handleLogs = useCallback(() => {
    navigate(LOGS);
  }, [navigate]);

  const handleConfiguration = useCallback(() => {
    setIsModalOpen(true); // Open the modal when the configuration is clicked
  }, []);

  const handleActivityLogs = useCallback(() => {
    navigate(ACTIVITYLOGS);
  }, [navigate]);

  
  useEffect(() => {
    // Function to sync localStorage updates
    const syncPermissions = () => {
      const storedUserPermissions =
        JSON.parse(localStorage.getItem('userPermissions')) || {};
      setUserPermissions(storedUserPermissions);
    };

    // Listen for custom localStorage update events
    window.addEventListener('localStorageUpdated', syncPermissions);

    // Initial fetch on component mount
    syncPermissions();

    return () => {
      window.removeEventListener('localStorageUpdated', syncPermissions);
    };
  }, []);
  const handleValidate = () => {
    navigate(UPLOAD);
  };
  const handleAdmin = useCallback(() => {
    navigate(ADMIN);
  }, [dispatch, navigate]);
  return (
    <Box>
      <Flex
        justifyItems="space-between"
        boxShadow={'0 2px 8px rgba(0, 0, 0, 0.1)'}
        p="0 10px"
      >
        <Image
          height={'60px'}
          src={TuringLogo}
          cursor="pointer"
          onClick={() => navigate(NEWDASHBOARD)}
        />
        <Spacer />
        <Flex justifyContent="flex-end" align={'center'} gap={2}>
          <Button
            variant={location.pathname === NEWDASHBOARD ? 'solid' : 'link'}
            colorScheme="blue"
            onClick={() => navigate(NEWDASHBOARD)}
          >
            Dashboard
          </Button>

          <Button
            variant={location.pathname === UPLOAD ? 'solid' : 'link'}
            colorScheme="blue"
            onClick={handleValidate}
          >
            Upload
          </Button>
          <Menu>
            <MenuButton>
              <Avatar size="sm" name={profile?.name} />
            </MenuButton>
            <MenuList minWidth="auto">
               
            <MenuItem onClick={openTokenModal}>Get Token</MenuItem>

               {userPermissions.logs && (
              <MenuItem onClick={handleLogs}>Logs</MenuItem>
             )} 
             {userPermissions.logs && (
              <MenuItem onClick={handleActivityLogs}>Activity Logs</MenuItem>
            )}
             
            {userPermissions.configuration && (
              <MenuItem onClick={handleConfiguration}>Configuration</MenuItem>
            )}
              {(userPermissions.user_management) && (
                 <MenuItem onClick={handleAdmin}>Admin Control</MenuItem>
            )}
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </MenuList>
          </Menu>
        </Flex>
      </Flex>

      {/* Render the modal when isModalOpen is true */}
      <ConfigurationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)} // Close modal
        isNewDashboardEnabled={isNewDashboardEnabled} // Pass the state
        setIsNewDashboardEnabled={setIsNewDashboardEnabled} // Pass the toggle function
      />

      <TokenModal isOpen={isTokenModalOpen} onClose={() => setIsTokenModalOpen(false)} />

      <Outlet />
    </Box>
  );
}

export default DefaultLayout;
