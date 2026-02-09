import { useState, useCallback } from 'react';
import { Student } from '@domain/entities/Student';
import { ClassRepository } from '@infrastructure/repositories/ClassRepository';
import { HttpClient } from '@infrastructure/http/HttpClient';
import { LocalStorageService } from '@infrastructure/services/LocalStorageService';
import { GetClassDetailsUseCase } from '@application/use-cases/classes/GetClassDetailsUseCase';

// Dependency Injection
const storageService = new LocalStorageService();
const httpClient = new HttpClient(storageService);
const classRepository = new ClassRepository(httpClient);
const getClassDetailsUseCase = new GetClassDetailsUseCase(classRepository);

export const useStudents = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStudentsByClass = useCallback(async (classUuid: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const classData = await getClassDetailsUseCase.execute(classUuid);
      
      // Extrair alunos dos dados da classe
      if (classData.students && Array.isArray(classData.students)) {
        setStudents(classData.students);
      } else {
        setStudents([]);
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao carregar alunos';
      setError(errorMessage);
      setStudents([]);
      console.error('Erro ao carregar alunos da turma:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    students,
    isLoading,
    error,
    loadStudentsByClass,
  };
};
