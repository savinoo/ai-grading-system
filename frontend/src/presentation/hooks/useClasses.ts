import { useCallback } from 'react';
import { useClassStore } from '@presentation/store/classStore';
import { useAuthStore } from '@presentation/store/authStore';
import { CreateClassUseCase } from '@application/use-cases/classes/CreateClassUseCase';
import { GetTeacherClassesUseCase } from '@application/use-cases/classes/GetTeacherClassesUseCase';
import { GetClassDetailsUseCase } from '@application/use-cases/classes/GetClassDetailsUseCase';
import { AddStudentsToClassUseCase } from '@application/use-cases/classes/AddStudentsToClassUseCase';
import { RemoveStudentFromClassUseCase } from '@application/use-cases/classes/RemoveStudentFromClassUseCase';
import { DeactivateClassUseCase } from '@application/use-cases/classes/DeactivateClassUseCase';
import { ClassRepository } from '@infrastructure/repositories/ClassRepository';
import { HttpClient } from '@infrastructure/http/HttpClient';
import { LocalStorageService } from '@infrastructure/services/LocalStorageService';
import { CreateClassDTO, AddStudentsDTO } from '@domain/entities/Class';

// Dependency Injection
const storageService = new LocalStorageService();
const httpClient = new HttpClient(storageService);
const classRepository = new ClassRepository(httpClient);

const createClassUseCase = new CreateClassUseCase(classRepository);
const getTeacherClassesUseCase = new GetTeacherClassesUseCase(classRepository);
const getClassDetailsUseCase = new GetClassDetailsUseCase(classRepository);
const addStudentsToClassUseCase = new AddStudentsToClassUseCase(classRepository);
const removeStudentFromClassUseCase = new RemoveStudentFromClassUseCase(classRepository);
const deactivateClassUseCase = new DeactivateClassUseCase(classRepository);

export const useClasses = () => {
  const { classes, currentClass, isLoading, error, setClasses, setCurrentClass, setLoading, setError, addClass, removeClass, clearError } = useClassStore();
  const { user } = useAuthStore();

  const createClass = useCallback(async (data: CreateClassDTO) => {
    try {
      setLoading(true);
      setError(null);
      
      const newClass = await createClassUseCase.execute(data);
      addClass(newClass);
      return newClass;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Erro ao criar turma';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [addClass, setLoading, setError]);

  const loadTeacherClasses = useCallback(async () => {
    if (!user?.uuid) {
      setError('Usuário não autenticado');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await getTeacherClassesUseCase.execute(user.uuid);
      setClasses(response.classes);
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Erro ao carregar turmas';
      setError(errorMessage);
      console.error('Erro ao carregar turmas:', err);
    } finally {
      setLoading(false);
    }
  }, [user, setClasses, setLoading, setError]);

  const loadClassDetails = useCallback(async (classUuid: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const classData = await getClassDetailsUseCase.execute(classUuid);
      setCurrentClass(classData);
      return classData;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Erro ao carregar detalhes da turma';
      setError(errorMessage);
      console.error('Erro ao carregar detalhes da turma:', err);
    } finally {
      setLoading(false);
    }
  }, [setCurrentClass, setLoading, setError]);

  const addStudents = useCallback(async (classUuid: string, data: AddStudentsDTO) => {
    try {
      setLoading(true);
      setError(null);
      
      await addStudentsToClassUseCase.execute(classUuid, data);
      
      // Recarrega os detalhes da turma para atualizar a lista de alunos
      await loadClassDetails(classUuid);
    } catch (err: any) {
      // Tratamento específico para erro de validação
      if (err.response?.status === 422) {
        const validationErrors = err.response?.data?.detail;
        if (Array.isArray(validationErrors) && validationErrors.length > 0) {
          const firstError = validationErrors[0];
          if (firstError.loc?.includes('email')) {
            const errorMessage = `Email inválido: ${firstError.input}. Use um formato válido como exemplo@dominio.com`;
            setError(errorMessage);
            throw new Error(errorMessage);
          }
        }
      }
      const errorMessage = err.response?.data?.message || 'Erro ao adicionar alunos';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [loadClassDetails, setLoading, setError]);

  const removeStudent = useCallback(async (classUuid: string, studentUuid: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await removeStudentFromClassUseCase.execute(classUuid, studentUuid);
      
      // Atualiza a turma atual removendo o aluno
      if (currentClass && currentClass.uuid === classUuid) {
        const updatedClass = {
          ...currentClass,
          students: currentClass.students.filter(s => s.uuid !== studentUuid),
          total_students: currentClass.total_students - 1
        };
        setCurrentClass(updatedClass);
      }
      
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Erro ao remover aluno';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [currentClass, setCurrentClass, setLoading, setError]);

  const deactivateClass = useCallback(async (classUuid: string) => {
    try {
      setLoading(true);
      setError(null);
      
      await deactivateClassUseCase.execute(classUuid);
      removeClass(classUuid);
      
      // Se a turma desativada for a atual, limpa o estado
      if (currentClass?.uuid === classUuid) {
        setCurrentClass(null);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Erro ao desativar turma';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [currentClass, removeClass, setCurrentClass, setLoading, setError]);

  return {
    classes,
    currentClass,
    isLoading,
    error,
    createClass,
    loadTeacherClasses,
    loadClassDetails,
    addStudents,
    removeStudent,
    deactivateClass,
    clearError,
    setCurrentClass,
  };
};
