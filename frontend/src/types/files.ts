export interface FileInfo {
  s3key: string;
  file_url: string;
  workstream: string;
  id: number;
  file_stats: { stats_data: StatsData } | null;
}

export interface StatsData {
  totalConversations: number;
  totalUserTurns: number;
  ideal_sft: number;
  rlhf: number;
  categoryGroups: { [key: string]: number };
}
export interface UsersInfo {
  name: string;
  email: string;
  profile_pic_url: string;
  id: number;
  role_id:any,
  is_active:boolean,
}

export interface RoleInfo {
  name: string;
  role_id: string;
  permissions: string;
  id: number;
}