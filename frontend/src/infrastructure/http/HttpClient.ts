import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { IStorageService } from '@domain/services/IStorageService';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class HttpClient {
  private client: AxiosInstance;
  private storageService: IStorageService;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: unknown) => void;
    reject: (reason?: unknown) => void;
  }> = [];

  constructor(storageService: IStorageService) {
    this.storageService = storageService;
    
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Importante para enviar cookies (refresh_token)
    });

    this.setupInterceptors();
  }

  private processQueue(error: Error | null = null): void {
    this.failedQueue.forEach((promise) => {
      if (error) {
        promise.reject(error);
      } else {
        promise.resolve();
      }
    });
    this.failedQueue = [];
  }

  private setupInterceptors(): void {
    // Request interceptor - adiciona token nas requisições
    this.client.interceptors.request.use(
      (config) => {
        const token = this.storageService.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - trata erros e refresh automático
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Se for erro 401 e não for a rota de login ou refresh
        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          !originalRequest.url?.includes('/auth/login') &&
          !originalRequest.url?.includes('/auth/refresh')
        ) {
          if (this.isRefreshing) {
            // Se já está fazendo refresh, adiciona na fila
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            })
              .then(() => {
                return this.client(originalRequest);
              })
              .catch((err) => {
                return Promise.reject(err);
              });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            // Tenta fazer refresh do token
            const response = await this.client.post('/auth/refresh');
            const { access_token } = response.data;
            
            this.storageService.setItem('access_token', access_token);
            
            // Atualiza o token na requisição original
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }
            
            this.processQueue();
            this.isRefreshing = false;
            
            return this.client(originalRequest);
          } catch (refreshError) {
            this.processQueue(refreshError as Error);
            this.isRefreshing = false;
            
            // Remove tokens e redireciona para login
            this.storageService.removeItem('access_token');
            this.storageService.removeItem('user');
            window.location.href = '/login';
            
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  getClient(): AxiosInstance {
    return this.client;
  }

  async get<T>(url: string): Promise<T> {
    const response = await this.client.get<T>(url);
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }
}
