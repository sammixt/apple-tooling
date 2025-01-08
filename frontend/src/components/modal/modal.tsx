import {
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from '@chakra-ui/react';

export interface CustomModalProps {
  onClose: () => void;
  isOpen: boolean;
  header: string;
  children: React.ReactNode;
}

export default function CustomModal({
  onClose,
  isOpen,
  header,
  children,
}: CustomModalProps) {
  return (
    <Modal
      onClose={onClose}
      isOpen={isOpen}
      scrollBehavior={'inside'}
      size={'xl'}
    >
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{header}</ModalHeader>
        <ModalCloseButton />
        <ModalBody>{children}</ModalBody>
        <ModalFooter>
          <Button onClick={onClose}>Close</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
