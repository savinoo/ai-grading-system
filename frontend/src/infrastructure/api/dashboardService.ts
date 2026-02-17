import apiClient from '@infrastructure/http/apiClient';
import { DashboardStats } from '@domain/models/DashboardStats';

export const dashboardService = {
  getDashboardStats: async (teacherUuid: string, limitRecentExams: number = 10): Promise<DashboardStats> => {
    return await apiClient.get<DashboardStats>(
      `/dashboard/stats/${teacherUuid}`,
      {
        params: { limit_recent_exams: limitRecentExams },
      }
    );
  },
};

export default dashboardService;
