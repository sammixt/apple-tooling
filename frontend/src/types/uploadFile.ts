import { IdName } from './requests';

export interface UploadedFiles {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  user_email: string;
  user_name: string;
  workstream_pre: IdName;
}

export interface ErrorType {
  error_type: string;
  count: number;
}
