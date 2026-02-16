import { HttpClient } from './HttpClient';
import { LocalStorageService } from '@infrastructure/services/LocalStorageService';

// Cria uma instância única do HttpClient configurada com LocalStorageService
const storageService = new LocalStorageService();
const apiClient = new HttpClient(storageService);

export default apiClient;
