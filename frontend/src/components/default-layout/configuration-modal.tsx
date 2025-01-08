import React, { useState, useEffect, useRef } from 'react';
import {
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
  Switch,
  FormControl,
  FormLabel,
  HStack,
  Flex,
  useToast,
} from '@chakra-ui/react';
import { useGetConfigQuery, useUpdateConfigMutation } from './store';
import './ConfigurationModal.css';

const ConfigurationModal = ({ isOpen, onClose }) => {
  const [isConfiguration, setisConfiguration] = useState({});
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(true);
  const initialSettings = useRef({});

  useEffect(() => {
    const storedUserPermissions =
      JSON.parse(localStorage.getItem('userPermissions')) || {};
    setisConfiguration(!!storedUserPermissions['configuration']);
  }, []);

  const shouldFetchConfig = isConfiguration === true;

  const {
    data: config,
    isLoading: isRoleLoading,
    refetch,
  } = useGetConfigQuery(null, {
    skip: !shouldFetchConfig,
    refetchOnMountOrArgChange: true,
  });
  const [updateConfig] = useUpdateConfigMutation();
  const toast = useToast();

  useEffect(() => {
    if (isOpen && config?.configuration) {
      // Initialize settings with the configuration data when the modal opens
      setSettings(config.configuration);
      initialSettings.current = config.configuration; // Store initial settings for comparison
    }
  }, [isOpen, config]);

  const handleSave = async () => {
    setLoading(true);
    const updatedConfig = {
      configuration: settings,
    };

    try {
      await updateConfig(updatedConfig).unwrap();
      toast({
        status: 'success',
        isClosable: true,
        position: 'top',
        duration: 5000,
        title: 'Updated',
        description: 'Configuration updated successfully',
      });
      onClose();
    } catch (error) {
      console.error('Error updating configuration:', error);
      toast({
        status: 'error',
        isClosable: true,
        position: 'top',
        duration: 5000,
        title: 'Error',
        description: 'Error updating configuration',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchChange = (key) => {
    setSettings((prevSettings) => {
      const newSettings = { ...prevSettings };
      if (key === 'enable_turing_s3_upload') {
        newSettings['enable_penguin_s3_upload'] = newSettings[key];
      }
      if (key === 'enable_penguin_s3_upload') {
        newSettings['enable_turing_s3_upload'] = newSettings[key];
      }
      newSettings[key] = !newSettings[key];
      return newSettings;
    });
    setIsSubmitting(false);
  };

  const handleCancel = () => {
    setSettings(initialSettings.current); // Reset settings to initial settings
    setIsSubmitting(true);
    onClose();
  };

  // Check if current settings differ from initial settings to determine if there are changes
  const isSaveEnabled =
    JSON.stringify(settings) !== JSON.stringify(initialSettings.current);

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        setIsSubmitting(true);
        onClose();
      }}
      size="4xl"
    >
      <ModalOverlay />
      <ModalContent className="modal">
        <ModalHeader className="modal-header">
          Configuration Settings
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          {Object.keys(settings).map((key) => (
            <div key={key} className="row">
              <FormControl
                display="flex"
                alignItems="center"
                className="form-control"
              >
                <HStack justify="space-between" width="100%">
                  <FormLabel htmlFor={key} mb={1} fontWeight="bold">
                    {key
                      .replace(/_/g, ' ')
                      .split(' ')
                      .map(
                        (word) => word.charAt(0).toUpperCase() + word.slice(1)
                      )
                      .join(' ')}
                  </FormLabel>
                  <Switch
                    id={key}
                    isChecked={settings[key]}
                    onChange={() => handleSwitchChange(key)}
                    colorScheme="green"
                    isDisabled={loading}
                  />
                </HStack>
              </FormControl>
            </div>
          ))}
        </ModalBody>

        <ModalFooter className="modal-footer">
          <Flex justify="center" width="100%" alignItems="center">
            <Button
              onClick={handleSave}
              className="save-button"
              isLoading={loading}
              loadingText="Saving..."
              isDisabled={!isSaveEnabled} // Disable if there are no changes
              mr={4} // Adds margin-right between the Save and Cancel buttons
            >
              Save
            </Button>
            <Button
              variant="ghost"
              onClick={handleCancel}
              className="cancel-button"
              isDisabled={loading}
            >
              Cancel
            </Button>
          </Flex>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ConfigurationModal;
