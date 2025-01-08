import { createSlice } from '@reduxjs/toolkit';
import { persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';

import type { RootState } from '../../app/store';

export interface AuthState {
  token: string | null;
  clientName: string | null;
  profile: Member | null;
}

const initialState: AuthState = {
  token: null,
  clientName: null,
  profile: null,
};

export interface Member {
  id: string;
  name: string;
  email: string;
  picture: string;
}

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setToken(state, action) {
      state.token = action.payload;
    },
    clearDetails(state) {
      state.token = null;
      state.profile = null;
    },
    setClientName(state, action) {
      state.clientName = action.payload;
    },
    setProfile(state, action) {
      state.profile = { ...action.payload };
    },
  },
});

export const { setToken, clearDetails, setClientName, setProfile } =
  authSlice.actions;
export const { reducerPath } = authSlice;

export const getAuthToken = (state: RootState) => state.auth.token;
export const getClientName = (state: RootState) => state.auth.clientName;
export const getProfile = (state: RootState) => state.auth.profile;

export default persistReducer(
  {
    key: authSlice.reducerPath,
    storage,
  },
  authSlice.reducer
);
