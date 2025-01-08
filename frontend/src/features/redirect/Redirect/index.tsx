import { Heading, VStack, Skeleton } from '@chakra-ui/react';
import { Navigate } from 'react-router-dom';
import { NEWDASHBOARD } from '../../../app/path';

export function Redirect() {
  return (
    <Skeleton>
      <VStack>
        <Heading>Redirecting...</Heading>
        <Navigate to={NEWDASHBOARD} replace />
      </VStack>
    </Skeleton>
  );
}

export { Redirect as Component };
