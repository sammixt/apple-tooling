import { useState } from "react";
import {
  VStack,
  HStack,
  Button,
  Input,
  Text,
  Spinner,
  Select,
  useToast,
} from "@chakra-ui/react";
import axios from "axios";
import { config } from "../../services/config";
import { useAppSelector } from "../../hooks/store";
import { getProfile } from "../../features/auth/store";
// eslint-disable-next-line @nx/enforce-module-boundaries
import { usePostUploadFileMutation } from "src/pages/Upload/store";

interface CollabLinkUploadProps {
  setTabIndex: React.Dispatch<React.SetStateAction<number>>;
  refetch: unknown;
}

const CollabLinkUpload = (props: CollabLinkUploadProps) => {
  const [postUploadFile] = usePostUploadFileMutation();

  const { setTabIndex, refetch } = props;

  const profile = useAppSelector(getProfile);
  const [links, setLinks] = useState<string[]>([""]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadDate, setUploadDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split("T")[0]; // Default to today's date
  });
  const [uploadType, setUploadType] = useState<string>("");
  const toast = useToast();

  const minDate = new Date();
  minDate.setDate(minDate.getDate() - 7); // Set min date to 7 days ago
  const minDateString = minDate.toISOString().split("T")[0];

  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + 7); // Set max date to 7 days in the future
  const maxDateString = maxDate.toISOString().split("T")[0];

  const handleLinkChange = (index: number, value: string) => {
    const updatedLinks = [...links];
    updatedLinks[index] = value;
    setLinks(updatedLinks);
  };

  const handleAddLink = () => {
    // if (links.length < 10) {
    setLinks((prev) => [...prev, ""]);
    // } else {
    //   toast({
    //     status: "warning",
    //     title: "Limit Reached",
    //     description: "You can only add up to 10 links.",
    //     isClosable: true,
    //   });
    // }
  };

  const handleRemoveLink = (index: number) => {
    if (links.length > 1) {
      setLinks((prev) => prev.filter((_, i) => i !== index));
    }
  };

  const isValidLink = (link: string) =>
    /^https:\/\/colab\.research\.google\.com\/drive\/[a-zA-Z0-9_-]+$/.test(link);

  const areLinksValid = links.every((link) => isValidLink(link));

  const handleUploadLinks = async () => {
    setIsSubmitting(true);
    
    try {
      // const response = await axios.post(
      //   `${config.apiUrl}/processor/colab/?type=${uploadType}&user_email=${profile?.email}&user_name=${profile?.name}&delivery_date=${uploadDate}`,
      //     links,
      // );
      const url = `/colab/?type=${uploadType}&user_email=${profile?.email}&user_name=${profile?.name}&delivery_date=${uploadDate}`

      const response = await postUploadFile({
        body: {
          uploadDate,
        },
        url
      }).unwrap();
      toast({
        status: "success",
        title: "Links Uploaded",
        position: "top",
        duration: 5000,
        description: response.data?.message || "Links sent successfully.",
        isClosable: true,
      });
      setLinks([""]);
      setTabIndex(0);
      refetch()
    } catch (error: any) {
      toast({
        status: "error",
        title: "Collab Links Upload Failed",
        position: "top",
        duration: 5000,
        description: error.response?.data?.message || "An error occurred.",
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <VStack spacing={4} width="full" align="center">
      <Text fontSize="lg" fontWeight="bold">
        Enter Collaboration Links
      </Text>

      {links.map((link, index) => (
        <HStack key={`link-${index}`} width="full" maxWidth="500px">
          <Input
            placeholder="Enter collaboration link"
            value={link}
            onChange={(e) => handleLinkChange(index, e.target.value)}
            borderColor={isValidLink(link) ? "green.400" : "red.400"}
          />
          <Button
            aria-label="Remove link"
            colorScheme="red"
            onClick={() => handleRemoveLink(index)}
          >
            -
          </Button>
        </HStack>
      ))}

      <Button
        colorScheme="blue"
        onClick={handleAddLink}
        isDisabled={isSubmitting}
      >
        + Add Link
      </Button>

      <Input
        type="date"
        value={uploadDate}
        onChange={(e) => setUploadDate(e.target.value)}
        placeholder="Select Upload Date"
        width="full"
        maxWidth="500px"
        min={minDateString}
        max={maxDateString}
      />

      <Select
        placeholder="Select Upload Type"
        value={uploadType}
        onChange={(e) => setUploadType(e.target.value)}
        width="full"
        maxWidth="500px"
      >
        <option value="Agent">Reasoning-Agent</option>
        <option value="Coding">Reasoning-Code</option>
        <option value="General">Reasoning-General</option>
      </Select>

      <Button
        backgroundColor="black"
        color="white"
        _hover={{ backgroundColor: "gray.700" }}
        width="full"
        maxWidth="500px"
        onClick={handleUploadLinks}
        isDisabled={!areLinksValid || !uploadType || isSubmitting}
        leftIcon={isSubmitting ? <Spinner size="sm" /> : undefined}
      >
        {isSubmitting ? "Uploading..." : "Upload / Send Links"}
      </Button>
    </VStack>
  );
};

export default CollabLinkUpload;
