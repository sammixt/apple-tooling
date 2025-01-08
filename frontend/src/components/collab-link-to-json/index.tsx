import { useState } from "react";
import {
  VStack,
  HStack,
  Button,
  Input,
  Text,
  Spinner,
  Box,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Table as ChakraTable,
  Thead,
  Tr,
  Th,
  Tbody,
  Select,
  Td
} from "@chakra-ui/react";
import { ErrorType } from '../../types';
import { usePostUploadFileMutation } from "../../pages/Upload/store";
import ReactJson from "react-json-view";
import { useAppSelector } from '../../hooks/store';
import { getProfile } from '../../features/auth/store';

const CollabLinkToJson = () => {
  const profile = useAppSelector(getProfile);
  const [link, setLink] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [response, setResponse] = useState<object>({});
  const [isError, setIsError] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [client, setClient] = useState<string>("");
  const [postUploadFile] = usePostUploadFileMutation();

  const handleLinkChange = (value: string) => {
    setLink(value);
  };

  const isValidLink = (link: string) =>
    /^https:\/\/colab\.research\.google\.com\/drive\/[a-zA-Z0-9_-]+$/.test(link);

  const handleUploadLink = async () => {
    setIsSubmitting(true);
    setIsError(false);
    setResponse({});

    try {
      const res = await postUploadFile({
        body: {},
        url:`/convert-colab-link-to-json?link=${encodeURIComponent(link)}&annotator_email=${encodeURIComponent(profile?.email)}&client=${encodeURIComponent(client)}`
      }).unwrap();

      setResponse(res);
      setIsError(false);
    } catch (error: any) {
      setResponse(error?.data || { error: "An error occurred." });
      setIsError(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownload = () => {
    if (!isError && response) {
      const json = JSON.stringify(response, null, 2);
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "response.json";
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  const openModal = () => {
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  return (
    <VStack spacing={4} width="full" align="center">
      <Text fontSize="lg" fontWeight="bold">
        Enter Collaboration Link That Needs Converting
      </Text>

      <HStack width="full" maxWidth="500px">
        <Input
          placeholder="Enter collaboration link"
          value={link}
          onChange={(e) => handleLinkChange(e.target.value)}
          borderColor={isValidLink(link) ? "green.400" : "red.400"}
        />
      </HStack>

      <Select
        placeholder="Client"
        value={client}
        onChange={(e) => setClient(e.target.value)}
        width="full"
        maxWidth="500px"
      >
        <option value="penguin">Penguin</option>
        <option value="bytedance">Bytedance</option>
      </Select>

      <Button
        backgroundColor="black"
        color="white"
        _hover={{ backgroundColor: "gray.700" }}
        width="full"
        maxWidth="500px"
        onClick={handleUploadLink}
        isDisabled={!isValidLink(link) || isSubmitting || !client}
        leftIcon={isSubmitting ? <Spinner size="sm" /> : undefined}
      >
        {isSubmitting ? "Uploading..." : "Convert to JSON and Validate"}
      </Button>

      {Object.keys(response).length > 0 && (
        <Button
          onClick={openModal}
          colorScheme={isError ? "red" : "blue"}
          variant="solid"
          mt={2}
        >
          {isError ? "View Errors" : "View JSON"}
        </Button>
      )}

      {!isError && Object.keys(response).length > 0 && (
        <Button
          onClick={handleDownload}
          colorScheme="green"
          variant="solid"
          mt={2}
        >
          Download JSON
        </Button>
      )}

      {/* Modal */}
      <Modal isOpen={isModalOpen} onClose={closeModal} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{isError ? "Validation Error" : "JSON"}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
          {isError && <>
              <div>Error Report</div>
              {response?.summary ? (
                <ChakraTable variant="simple" size="sm" mt={2} mb={4}>
                  <Thead>
                    <Tr>
                      <Th>Error Type</Th>
                      <Th isNumeric>Count</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {response?.summary.error_types.map(
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
                        {response?.summary.total_errors}
                      </Td>
                    </Tr>
                  </Tbody>
                </ChakraTable>
              ) : (
                <Text>No summary data available</Text>
              )}
            </> }
            {isError && <div>Error Details</div>}
            <ReactJson
              src={isError ? response?.errors : response}
              name={false}
              theme={{
                base00: "#f5f5f5",
                base07: "#333",
                base08: "#d32f2f",
                base09: "#1976d2",
              }}
              collapsed={2} // Uncollapsed by default
              displayDataTypes={false}
              displayObjectSize={false}
              style={{
                width: "100%",
                maxWidth: "500px",
                backgroundColor: "#f9f9f9",
                borderRadius: "8px",
                border: "1px solid #ccc",
                padding: "16px",
                overflowX: "auto",
              }}
            />
          </ModalBody>
          <ModalFooter>
            <Button onClick={closeModal} colorScheme="blue">
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  );
};

export default CollabLinkToJson;
