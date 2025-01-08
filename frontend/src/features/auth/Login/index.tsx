import { useGoogleLogin as useNativeGoogleLogin } from '@react-oauth/google';
import { useLocation, useNavigate } from 'react-router-dom';
import { LoginForm } from '../components/login-form';
import { getProfile, setProfile, setToken } from '../store';
import { useAppDispatch, useAppSelector } from '../../../hooks/store';
import axios from 'axios';
import {  NEWDASHBOARD } from '../../../app/path';
import { config } from '../../../services/config';
import { useState, useEffect } from 'react';
import { createToast } from '../../../../src/app/rtkq-error.middleware'
import { useToast } from '@chakra-ui/react';
import { useGoogleAuthMutation } from './store';


export function Login() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const code = new URLSearchParams(useLocation().search).get('code');
  const [isCodeProcessed, setIsCodeProcessed] = useState(false);
  const error = new URLSearchParams(useLocation().search).get('error');
  const toast = useToast();
  const [getGoogleAuth] = useGoogleAuthMutation();

  // const onLogin = useNativeGoogleLogin({
  //   hosted_domain: 'turing.com',
  //   onSuccess: async (response) => {
  //     const { access_token } = response;

  //     // Store token in redux
  //     dispatch(setToken(`Bearer ${access_token}`));

  //     if (callbackURL) {
  //       // Redirect to the callback URL
  //       if (origin) {
  //         callbackURL += `?&origin=${encodeURI(window.location.origin)}`;
  //       }
  //       window.location.href = callbackURL;
  //       return;
  //     }

  //     // Fetch profile details
  //     const res = await axios.get(
  //       `${config.googleRedirectUrl}?access_token=${access_token}`,
  //       {
  //         headers: {
  //           Authorization: `Bearer ${access_token}`,
  //           Accept: 'application/json',
  //         },
  //       }
  //     );
  //     dispatch(setProfile(res.data));

  //     // Navigate to home page
  //     navigate(DASHBOARD);
  //   },
  //   onError: async (error) => {
  //     console.log('error msg', error, error.error_description, error.error_uri);
  //   },
  // });

  // Process the code only once when it is available in the URL
  useEffect(() => {
    async function fetchData() {
      // You can await here
      if(error){
        
        toast({
          title: 'Login Failed',
          description: error,
          status: 'error',
          duration: 3000,
          isClosable: true,
          position:'top'
        });
        return ;
      }
      if (code && !isCodeProcessed) {
        const url = `${config.apiUrl}/auth/google/callback?code=${code}`
        setIsCodeProcessed(true); // Mark the code as processed
        getGoogleAuth({
          url
        }).unwrap()
          .then((res) => {
            dispatch(setToken(res.access_token));
            dispatch(setProfile(res)); // Save user profile
            localStorage.setItem('userPermissions', JSON.stringify(res.role.permissions)); // Store permissions in localStorage
            navigate(NEWDASHBOARD); // Navigate to the dashboard after successful login
          })
          .catch((err) => {
            console.error('Google Auth Error:', err);
            createToast("UnAuthorized", err.response?.data?.detail ?? "You're not authorized. Contact Admin!")
          });
      }
    }
    fetchData();
   
  }, [code, isCodeProcessed, dispatch, navigate]);

  const onLogin = async () => {
    const res = await getGoogleAuth({
      url:`${config.apiUrl}/auth/google`
    }).unwrap()

   window.location.href = res.auth_url;
  }
  return <LoginForm onLogin={onLogin} />;
}

export { Login as Component };
