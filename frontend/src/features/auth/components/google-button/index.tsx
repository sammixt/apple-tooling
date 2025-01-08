import {
  Image,
  Button,
  ButtonProps,
  useColorModeValue,
} from '@chakra-ui/react';
import GoogleImg from './assets/google.svg';

export type GoogleButtonProps = Omit<ButtonProps, 'leftIcon'>;

export function GoogleButton(props: GoogleButtonProps) {
  return (
    <Button
      border={useColorModeValue('1px solid #E4E4E7', 0)}
      bg={useColorModeValue('white', '#202124')}
      {...props}
      leftIcon={<Image src={GoogleImg} boxSize={7} />}
    />
  );
}
