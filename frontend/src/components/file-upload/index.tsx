import { Box, Button, Select, VStack, Text, Input } from '@chakra-ui/react';
import React, { useState } from 'react';
import ReactFiles, { File } from 'react-files';

interface FileUploadProps {
  handleChange: (files: File[]) => void;
  handleUpload: React.MouseEventHandler<HTMLButtonElement>;
  workstream: string;
  handleWorkStreamChange: React.ChangeEventHandler<HTMLSelectElement>;
  isValidFile: boolean;
  workstreams: Array<{ id: string; name: string }>;
  files: File[];
  handleFileRemove: (file: File) => void; // To remove files individually
  uploadDate: string; // Upload date value
  setUploadDate: React.Dispatch<React.SetStateAction<string>>;
  client: string;
  setClient: React.Dispatch<React.SetStateAction<string>>;
  isValidateDate: boolean | undefined;
}

const FileUpload = (props: FileUploadProps) => {
  const {
    handleChange,
    handleUpload,
    workstream,
    handleWorkStreamChange,
    isValidFile,
    workstreams,
    files,
    handleFileRemove,
    uploadDate,
    setUploadDate,
    client,
    setClient,
    isValidateDate,
  } = props;

  const currentDate = new Date();
  const currentDateString = currentDate.toISOString().split('T')[0];

  const minDate = new Date(currentDate);
  minDate.setDate(currentDate.getDate() - 7);
  const minDateString = minDate.toISOString().split('T')[0];

  const maxDate = new Date(currentDate);
  maxDate.setDate(currentDate.getDate() + 7);
  const maxDateString = maxDate.toISOString().split('T')[0];

  const [uploadDateState, setUploadDateState] = useState(uploadDate || currentDateString);

  const isSFTReasoning = workstream === 'sft_reasoning';
  const acceptedFileTypes = isSFTReasoning ? ['.csv'] : ['.json'];
  const uploadBoxMessage = isSFTReasoning
    ? 'Drag & Drop your Deliverable file here or click to browse'
    : 'Drag & Drop your Deliverable files here or click to browse';

  const isFileUploadDisabled = !workstream;

  const handleFileChange = (newFiles: File[]) => {
    if (isSFTReasoning && newFiles.length > 1) {
      console.error('Only one CSV file is allowed for SFT Reasoning.');
      return;
    }
    handleChange(newFiles);
  };


  return (
    <VStack spacing={4} width="full" align="center">
      <ReactFiles
        className="files-dropzone"
        onChange={handleFileChange}
        onError={(error) => console.error('File error:', error)}
        accepts={acceptedFileTypes}
        multiple={!isSFTReasoning}
        maxFileSize={1000 * 1024 * 1024}
        clickable={!isFileUploadDisabled}
        style={{
          width: '100%',
          maxWidth: '500px',
        }}
      >
        <Box
          border="3px dashed #E0E9FE"
          padding="20px"
          textAlign="center"
          cursor={isFileUploadDisabled ? 'not-allowed' : 'pointer'}
          boxSizing="border-box"
          height="200px"
          display="flex"
          flexDirection="column"
          justifyContent="center"
          alignItems="center"
          borderRadius="12px"
          opacity={isFileUploadDisabled ? 0.5 : 1}
        >
          <Text fontSize="2xl" fontWeight="semibold">
            Upload your files
          </Text>
          <Text fontSize="lg" fontWeight="light" marginTop="10px">
            {uploadBoxMessage}
          </Text>
        </Box>
      </ReactFiles>

      <Box width="100%" maxWidth="500px">
        {files.map((file, index) => (
          <Box
            key={index}
            display="flex"
            alignItems="center"
            justifyContent="space-between"
            border="1px solid lightgray"
            padding="8px"
            marginBottom="4px"
            borderRadius="md"
          >
            <Text isTruncated maxWidth="80%" title={file.name}>
              {file.name}
            </Text>
            <Button
              size="xs"
              colorScheme="red"
              onClick={() => handleFileRemove(file)}
            >
              Remove
            </Button>
          </Box>
        ))}
      </Box>

      <Select
        placeholder="Select workstream"
        value={workstream}
        onChange={handleWorkStreamChange}
        width="100%"
        maxWidth="500px"
      >
        {workstreams.map((ws) => (
          <option key={ws.id} value={ws.id}>
            {ws.name}
          </option>
        ))}
      </Select>

      {isSFTReasoning && (
        <Select
          placeholder="Select Client"
          value={client}
          onChange={(e) => setClient(e.target.value)}
          width="100%"
          maxWidth="500px"
        >
          <option value="penguin">Penguin</option>
          <option value="bytedance">Bytedance</option>
        </Select>
      )}

      <Input
        type="date"
        value={uploadDateState}
        onChange={(e) => {
          const newDate = e.target.value;
          setUploadDateState(newDate);
          setUploadDate(newDate);
        }}
        placeholder="Select Upload Date"
        width="100%"
        maxWidth="500px"
        min={isValidateDate ? minDateString : undefined} // Use `undefined` for invalid min date
        max={isValidateDate ? maxDateString : undefined} // Use `undefined` for invalid max date
      />

      <Button
        backgroundColor="black"
        color="white"
        _hover={{ backgroundColor: 'gray.700' }}
        onClick={handleUpload}
        width="100%"
        maxWidth="500px"
        disabled={
          !workstream ||
          !isValidFile ||
          files.length === 0 ||
          !uploadDateState ||
          (isSFTReasoning && (files.length !== 1 || !client))
        }
      >
        Upload
      </Button>
    </VStack>
  );
};

export default FileUpload;