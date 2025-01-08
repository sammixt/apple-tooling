import { useCallback } from 'react';
import { Box, Button, Center, Image, Text } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import NotFoundImage from './assets/not-found.svg';
export interface NotFoundProps {
    homeUrl?: string;
    homeText?: string;
    pageTitle?: string;
    pageDescription?: string;
}
export function NotFound({
    homeUrl = '/',
    homeText = 'Go back home',
    pageTitle = 'Page not found',
    pageDescription = 'The page you are looking for does not exist.',
}: NotFoundProps) {
    const navigate = useNavigate();
    const goHome = useCallback(() => navigate(homeUrl), [homeUrl, navigate]);
    return (
        <Center h="100vh" w="100vw" flexDirection="column">
            <Image src={NotFoundImage} width={500} />
            <Text fontSize="2xl" fontWeight={500} mt={5}>
                {pageTitle}
            </Text>
            <Text fontSize="md" fontWeight={400} mt={2}>
                {pageDescription}
            </Text>
            <Box mt={5}>
                <Button onClick={goHome}>{homeText}</Button>
            </Box>
        </Center>
    );
}
export default NotFound;