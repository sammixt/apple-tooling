import React from 'react';
import {
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
  Flex,
  HStack,
  useClipboard,
  Text,
} from '@chakra-ui/react';
import './ConfigurationModal.css';
import { useGetTokenQuery } from './store';

const TokenModal = ({ isOpen, onClose }) => {
  const handleCancel = () => {
    onClose();
  };

  const { data: token, isLoading } = useGetTokenQuery(null, {
    refetchOnMountOrArgChange: true,
  });

  const accessToken = token?.access_token;

  const truncatedToken = accessToken
    ? `${accessToken.slice(0, 24)}...`
    : 'Failed to get Token. Please try again later.';

  const { hasCopied, onCopy } = useClipboard(accessToken || '');

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        onClose();
      }}
      size="xl"
    >
      <ModalOverlay />
      <ModalContent className="modal">
        <ModalHeader className="modal-header">Token</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Flex direction="column" align="center" gap={5} padding={5}>
            <Text color="gray.500" textAlign="center" fontWeight="bold">
              This is a Bearer token and is valid for 24 hours.
            </Text>
            <Text fontSize="xs" color="gray.400" textAlign="center">
              Use this token in the Authorization header as: <br />
              <b>Authorization: Bearer &lt;your-token&gt;</b>
            </Text>
            <HStack spacing={4} marginBottom={4}>
              <Text
                fontSize="md"
                color="gray.600"
                isTruncated
                maxW="400px"
                title={accessToken || 'No token available'}
              >
                Token: {truncatedToken}
              </Text>
              <Button
                size="sm"
                onClick={onCopy}
                colorScheme={hasCopied ? 'green' : 'blue'}
              >
                {hasCopied ? 'Copied!' : 'Copy'}
              </Button>
            </HStack>
          </Flex>
        </ModalBody>

        <ModalFooter className="modal-footer">
          <Flex justify="center" width="100%" alignItems="center">
            <Button
              variant="ghost"
              onClick={handleCancel}
              className="cancel-button"
            >
              Close
            </Button>
          </Flex>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default TokenModal;
