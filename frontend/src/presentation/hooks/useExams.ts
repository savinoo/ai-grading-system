import { useCallback } from 'react';
import { useExamStore } from '@presentation/store/examStore';
import { useAuthStore } from '@presentation/store/authStore';

// Use Cases - Exams
import { CreateExamUseCase } from '@application/use-cases/exams/CreateExamUseCase';
import { GetTeacherExamsUseCase } from '@application/use-cases/exams/GetTeacherExamsUseCase';
import { GetExamByUuidUseCase } from '@application/use-cases/exams/GetExamByUuidUseCase';
import { UpdateExamUseCase } from '@application/use-cases/exams/UpdateExamUseCase';

// Use Cases - Criteria
import { ListGradingCriteriaUseCase } from '@application/use-cases/criteria/ListGradingCriteriaUseCase';
import { CreateExamCriteriaUseCase } from '@application/use-cases/criteria/CreateExamCriteriaUseCase';
import { ListExamCriteriaUseCase } from '@application/use-cases/criteria/ListExamCriteriaUseCase';
import { UpdateExamCriteriaUseCase } from '@application/use-cases/criteria/UpdateExamCriteriaUseCase';
import { DeleteExamCriteriaUseCase } from '@application/use-cases/criteria/DeleteExamCriteriaUseCase';

// Repositories
import { ExamRepository } from '@infrastructure/repositories/ExamRepository';
import { CriteriaRepository } from '@infrastructure/repositories/CriteriaRepository';
import { HttpClient } from '@infrastructure/http/HttpClient';
import { LocalStorageService } from '@infrastructure/services/LocalStorageService';

// DTOs
import { CreateExamDTO, UpdateExamDTO } from '@domain/entities/Exam';
import { CreateExamCriteriaDTO, UpdateExamCriteriaDTO } from '@domain/entities/Criteria';

// Dependency Injection
const storageService = new LocalStorageService();
const httpClient = new HttpClient(storageService);
const examRepository = new ExamRepository(httpClient);
const criteriaRepository = new CriteriaRepository(httpClient);

// Exam Use Cases
const createExamUseCase = new CreateExamUseCase(examRepository);
const getTeacherExamsUseCase = new GetTeacherExamsUseCase(examRepository);
const getExamByUuidUseCase = new GetExamByUuidUseCase(examRepository);
const updateExamUseCase = new UpdateExamUseCase(examRepository);

// Criteria Use Cases
const listGradingCriteriaUseCase = new ListGradingCriteriaUseCase(criteriaRepository);
const createExamCriteriaUseCase = new CreateExamCriteriaUseCase(criteriaRepository);
const listExamCriteriaUseCase = new ListExamCriteriaUseCase(criteriaRepository);
const updateExamCriteriaUseCase = new UpdateExamCriteriaUseCase(criteriaRepository);
const deleteExamCriteriaUseCase = new DeleteExamCriteriaUseCase(criteriaRepository);

export const useExams = () => {
  const {
    exams,
    currentExam,
    examCriteria,
    gradingCriteria,
    isLoading,
    error,
    setExams,
    setCurrentExam,
    setExamCriteria,
    setGradingCriteria,
    setLoading,
    setError,
    addExam,
    updateExam,
    addExamCriteria,
    updateExamCriteria,
    removeExamCriteria,
    clearError,
  } = useExamStore();
  
  const { user } = useAuthStore();

  // ==================== EXAM OPERATIONS ====================

  const createExam = useCallback(async (data: CreateExamDTO) => {
    try {
      setLoading(true);
      setError(null);
      
      const newExam = await createExamUseCase.execute(data);
      addExam(newExam);
      return newExam;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao criar prova';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [addExam, setLoading, setError]);

  const loadTeacherExams = useCallback(async () => {
    if (!user?.uuid) {
      setError('Usuário não autenticado');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await getTeacherExamsUseCase.execute(user.uuid);
      setExams(response.exams);
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao carregar provas';
      setError(errorMessage);
      console.error('Erro ao carregar provas:', err);
    } finally {
      setLoading(false);
    }
  }, [user, setExams, setLoading, setError]);

  const loadExamDetails = useCallback(async (examUuid: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const exam = await getExamByUuidUseCase.execute(examUuid);
      setCurrentExam(exam);
      return exam;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao carregar detalhes da prova';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setCurrentExam, setLoading, setError]);

  const updateExamData = useCallback(async (examUuid: string, data: UpdateExamDTO) => {
    try {
      setLoading(true);
      setError(null);
      
      const updatedExam = await updateExamUseCase.execute(examUuid, data);
      updateExam(examUuid, updatedExam);
      
      if (currentExam?.uuid === examUuid) {
        setCurrentExam(updatedExam);
      }
      
      return updatedExam;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao atualizar prova';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [currentExam, updateExam, setCurrentExam, setLoading, setError]);

  // ==================== GRADING CRITERIA OPERATIONS ====================

  const loadGradingCriteria = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const criteria = await listGradingCriteriaUseCase.execute({ active_only: true });
      setGradingCriteria(criteria);
      return criteria;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao carregar critérios de avaliação';
      setError(errorMessage);
      console.error('Erro ao carregar critérios:', err);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setGradingCriteria, setLoading, setError]);

  // ==================== EXAM CRITERIA OPERATIONS ====================

  const loadExamCriteria = useCallback(async (examUuid: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const criteria = await listExamCriteriaUseCase.execute(examUuid, { active_only: true });
      
      // Enriquecer critérios com informações do GradingCriteria
      const gradState = useExamStore.getState().gradingCriteria;
      const enrichedCriteria = criteria.map(examCriteria => {
        const gradingCriteria = gradState.find(
          gc => gc.uuid === examCriteria.criteria_uuid
        );
        
        return {
          ...examCriteria,
          grading_criteria_uuid: gradingCriteria?.uuid,
          grading_criteria_name: gradingCriteria?.name || 'Critério não encontrado',
          grading_criteria_description: gradingCriteria?.description || '',
        };
      });
      
      setExamCriteria(enrichedCriteria);
      return enrichedCriteria;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao carregar critérios da prova';
      setError(errorMessage);
      console.error('Erro ao carregar critérios da prova:', err);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setExamCriteria, setLoading, setError]);

  const createCriteria = useCallback(async (data: CreateExamCriteriaDTO) => {
    try {
      setLoading(true);
      setError(null);
      
      const newCriteria = await createExamCriteriaUseCase.execute(data);
      
      // Enriquecer o critério criado com informações do GradingCriteria
      const gradState = useExamStore.getState().gradingCriteria;
      const gradingCriteria = gradState.find(
        gc => gc.uuid === newCriteria.criteria_uuid
      );
      
      const enrichedCriteria = {
        ...newCriteria,
        grading_criteria_uuid: gradingCriteria?.uuid,
        grading_criteria_name: gradingCriteria?.name || 'Critério não encontrado',
        grading_criteria_description: gradingCriteria?.description || '',
      };
      
      addExamCriteria(enrichedCriteria);
      return enrichedCriteria;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao adicionar critério';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [addExamCriteria, setLoading, setError]);

  const updateCriteria = useCallback(async (criteriaUuid: string, data: UpdateExamCriteriaDTO) => {
    try {
      setLoading(true);
      setError(null);
      
      const updatedCriteria = await updateExamCriteriaUseCase.execute(criteriaUuid, data);
      updateExamCriteria(criteriaUuid, updatedCriteria);
      return updatedCriteria;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao atualizar critério';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [updateExamCriteria, setLoading, setError]);

  const deleteCriteria = useCallback(async (criteriaUuid: string) => {
    try {
      setLoading(true);
      setError(null);
      
      await deleteExamCriteriaUseCase.execute(criteriaUuid);
      removeExamCriteria(criteriaUuid);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao remover critério';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [removeExamCriteria, setLoading, setError]);

  return {
    // State
    exams,
    currentExam,
    examCriteria,
    gradingCriteria,
    isLoading,
    error,
    
    // Exam Operations
    createExam,
    loadTeacherExams,
    loadExamDetails,
    updateExamData,
    
    // Grading Criteria Operations
    loadGradingCriteria,
    
    // Exam Criteria Operations
    loadExamCriteria,
    createCriteria,
    updateCriteria,
    deleteCriteria,
    
    // Utilities
    clearError,
  };
};
