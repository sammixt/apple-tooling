import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  Button,
  ModalCloseButton,
  Alert,
  AlertIcon,
  Box,
  Text,
} from '@chakra-ui/react';
import { useGetConfigQuery } from '../default-layout/store';

interface UploadConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  handleUploadClick: () => void;
}

const UploadConfirmationModal: React.FC<UploadConfirmationModalProps> = ({
  isOpen,
  onClose,
  handleUploadClick,
}) => {
  // Function to handle upload on confirmation
  const handleConfirmUpload = () => {
    handleUploadClick(); // Trigger the upload
    onClose(); // Close the modal
  };
  const { data } = useGetConfigQuery(null);
  console.log(data);
  const isTuringUploadEnabled = data?.configuration.enable_turing_s3_upload;

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Confirm Upload</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          {isTuringUploadEnabled ? (
            <Alert status="info" borderRadius="md" mb={4}>
              <AlertIcon />
              <Box>
                <strong>Note:</strong> You are uploading to{' '}
                <strong>Turing S3</strong>.
              </Box>
            </Alert>
          ) : (
            <Alert status="warning" borderRadius="md" mb={4}>
              <AlertIcon />
              <Box>
                <strong>Note:</strong> You are uploading to a{' '}
                <strong>Penguin S3</strong>.
              </Box>
            </Alert>
          )}
          <Box
            mt={4}
            p={3}
            bg="gray.50"
            borderRadius="md"
            border="1px solid"
            borderColor="gray.200"
          >
            <Text fontSize="md" color="gray.800" mb={2}>
              <strong>Are you sure you want to upload this batch?</strong>
            </Text>
            <Text fontSize="sm" color="gray.600">
              This action cannot be undone.
            </Text>
          </Box>
        </ModalBody>
        <ModalFooter>
          <Button colorScheme="red" onClick={onClose}>
            Cancel
          </Button>
          <Button colorScheme="blue" onClick={handleConfirmUpload} ml={3}>
            Confirm Upload
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default UploadConfirmationModal;
