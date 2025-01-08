import { Box, Image, Text, VStack } from '@chakra-ui/react';
import { useCallback } from 'react';
import { GoogleButton } from '../google-button';
import TuringLogo from './assets/TuringLogo.png';

export interface LoginFormProps {
  onLogin: () => void;
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const onClick = useCallback(() => onLogin(), [onLogin]);

  return (
    <VStack
      direction="column"
      alignItems="center"
      justifyContent="center"
      w="full"
      h="full"
      minHeight="100vh"
      px={{ base: 4, sm: 6, md: 8 }} // Padding for responsive design
    >
           <Image src={TuringLogo} />

      <Text
        fontWeight="extrabold"
        fontSize={{ base: '2xl', sm: '3xl', md: '4xl' }} // Responsive text size
        textAlign="center"
      >
        Welcome to Penguin S3 Dashboard
      </Text>
      <Text
        mt={1}
        fontSize={{ base: 'sm', md: 'md' }} // Smaller text size for small screens
        textAlign="center"
      >
        Please login to continue
      </Text>
      <Box mt={5}>
        <GoogleButton onClick={onClick}>
          Sign in with Google
        </GoogleButton>
      </Box>
    </VStack>
  );
}
