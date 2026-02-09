import { useState, useCallback } from 'react';
import { QuestionRepository } from '@infrastructure/repositories/QuestionRepository';
import { HttpClient } from '@infrastructure/http/HttpClient';
import { LocalStorageService } from '@infrastructure/services/LocalStorageService';
import {
  ExamQuestion,
  QuestionCriteriaOverride,
  StudentAnswer,
  CreateExamQuestionDTO,
  UpdateExamQuestionDTO,
  CreateQuestionCriteriaOverrideDTO,
  CreateStudentAnswerDTO,
  UpdateStudentAnswerDTO
} from '@domain/entities/Question';

// Dependency Injection
const storageService = new LocalStorageService();
const httpClient = new HttpClient(storageService);
const questionRepository = new QuestionRepository(httpClient);

export const useQuestions = () => {
  const [questions, setQuestions] = useState<ExamQuestion[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<ExamQuestion | null>(null);
  const [questionCriteriaOverrides, setQuestionCriteriaOverrides] = useState<QuestionCriteriaOverride[]>([]);
  const [studentAnswers, setStudentAnswers] = useState<StudentAnswer[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createQuestion = useCallback(async (data: CreateExamQuestionDTO): Promise<ExamQuestion> => {
    setIsLoading(true);
    setError(null);
    try {
      const question = await questionRepository.createQuestion(data);
      setQuestions(prev => [...prev, question]);
      return question;
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao criar questão';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateQuestion = useCallback(async (questionUuid: string, data: UpdateExamQuestionDTO): Promise<ExamQuestion> => {
    setIsLoading(true);
    setError(null);
    try {
      const updatedQuestion = await questionRepository.updateQuestion(questionUuid, data);
      setQuestions(prev => prev.map(q => q.uuid === questionUuid ? updatedQuestion : q));
      return updatedQuestion;
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao atualizar questão';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadQuestionsByExam = useCallback(async (examUuid: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await questionRepository.listQuestionsByExam(examUuid);
      setQuestions(data);
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao carregar questões';
      setError(errorMessage);
      console.error('Erro ao carregar questões:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteQuestion = useCallback(async (questionUuid: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      await questionRepository.deleteQuestion(questionUuid);
      setQuestions(prev => prev.filter(q => q.uuid !== questionUuid));
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao deletar questão';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteAllQuestionAnswers = useCallback(async (questionUuid: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      await questionRepository.deleteAllQuestionAnswers(questionUuid);
      setStudentAnswers(prev => prev.filter(a => a.question_uuid !== questionUuid));
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao deletar respostas';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createQuestionCriteriaOverride = useCallback(async (data: CreateQuestionCriteriaOverrideDTO): Promise<QuestionCriteriaOverride> => {
    setIsLoading(true);
    setError(null);
    try {
      const override = await questionRepository.createQuestionCriteriaOverride(data);
      setQuestionCriteriaOverrides(prev => [...prev, override]);
      return override;
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao criar critério customizado';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  const updateQuestionCriteriaOverride = useCallback(async (
    overrideUuid: string,
    data: Partial<CreateQuestionCriteriaOverrideDTO>
  ): Promise<QuestionCriteriaOverride> => {
    setIsLoading(true);
    setError(null);
    try {
      const override = await questionRepository.updateQuestionCriteriaOverride(overrideUuid, data);
      setQuestionCriteriaOverrides(prev => prev.map(o => o.uuid === overrideUuid ? override : o));
      return override;
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao atualizar critério customizado';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  const deleteQuestionCriteriaOverride = useCallback(async (overrideUuid: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      await questionRepository.deleteQuestionCriteriaOverride(overrideUuid);
      setQuestionCriteriaOverrides(prev => prev.filter(o => o.uuid !== overrideUuid));
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao remover critério customizado';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadQuestionCriteriaOverrides = useCallback(async (questionUuid: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await questionRepository.listQuestionCriteriaOverrides(questionUuid);
      setQuestionCriteriaOverrides(data);
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao carregar critérios customizados';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const resetQuestionCriteria = useCallback(async (questionUuid: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      await questionRepository.resetQuestionCriteria(questionUuid);
      setQuestionCriteriaOverrides(prev => prev.filter(o => o.question_uuid !== questionUuid));
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao resetar critérios';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createStudentAnswer = useCallback(async (data: CreateStudentAnswerDTO): Promise<StudentAnswer> => {
    setIsLoading(true);
    setError(null);
    try {
      const answer = await questionRepository.createStudentAnswer(data);
      setStudentAnswers(prev => [...prev, answer]);
      return answer;
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao criar resposta';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateStudentAnswer = useCallback(async (answerUuid: string, data: UpdateStudentAnswerDTO): Promise<StudentAnswer> => {
    setIsLoading(true);
    setError(null);
    try {
      const answer = await questionRepository.updateStudentAnswer(answerUuid, data);
      setStudentAnswers(prev => prev.map(a => a.uuid === answerUuid ? answer : a));
      return answer;
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao atualizar resposta';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteStudentAnswer = useCallback(async (answerUuid: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      await questionRepository.deleteStudentAnswer(answerUuid);
      setStudentAnswers(prev => prev.filter(a => a.uuid !== answerUuid));
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao deletar resposta';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadStudentAnswersByQuestion = useCallback(async (questionUuid: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await questionRepository.listStudentAnswersByQuestion(questionUuid);
      setStudentAnswers(data);
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao carregar respostas';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    questions,
    currentQuestion,
    questionCriteriaOverrides,
    studentAnswers,
    isLoading,
    error,
    createQuestion,
    updateQuestion,
    loadQuestionsByExam,
    deleteQuestion,
    deleteAllQuestionAnswers,
    createQuestionCriteriaOverride,
    loadQuestionCriteriaOverrides,
    resetQuestionCriteria,
    updateQuestionCriteriaOverride,
    deleteQuestionCriteriaOverride,
    createStudentAnswer,
    updateStudentAnswer,
    deleteStudentAnswer,
    loadStudentAnswersByQuestion,
  };
};
