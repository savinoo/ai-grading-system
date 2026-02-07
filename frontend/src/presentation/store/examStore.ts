import { create } from 'zustand';
import { Exam } from '../../domain/entities/Exam';
import { ExamCriteria, GradingCriteria } from '../../domain/entities/Criteria';

interface ExamState {
  exams: Exam[];
  currentExam: Exam | null;
  examCriteria: ExamCriteria[];
  gradingCriteria: GradingCriteria[];
  isLoading: boolean;
  error: string | null;

  // Setters
  setExams: (exams: Exam[]) => void;
  setCurrentExam: (exam: Exam | null) => void;
  setExamCriteria: (criteria: ExamCriteria[]) => void;
  setGradingCriteria: (criteria: GradingCriteria[]) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;

  // Actions
  addExam: (exam: Exam) => void;
  updateExam: (examUuid: string, updatedExam: Partial<Exam>) => void;
  removeExam: (examUuid: string) => void;
  
  addExamCriteria: (criteria: ExamCriteria) => void;
  updateExamCriteria: (criteriaUuid: string, updatedCriteria: Partial<ExamCriteria>) => void;
  removeExamCriteria: (criteriaUuid: string) => void;
  
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  exams: [],
  currentExam: null,
  examCriteria: [],
  gradingCriteria: [],
  isLoading: false,
  error: null,
};

export const useExamStore = create<ExamState>((set) => ({
  ...initialState,

  setExams: (exams) => set({ exams }),

  setCurrentExam: (exam) => set({ currentExam: exam }),

  setExamCriteria: (criteria) => set({ examCriteria: criteria }),

  setGradingCriteria: (criteria) => set({ gradingCriteria: criteria }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  addExam: (exam) =>
    set((state) => ({ exams: [...state.exams, exam] })),

  updateExam: (examUuid, updatedExam) =>
    set((state) => ({
      exams: state.exams.map((exam) =>
        exam.uuid === examUuid ? { ...exam, ...updatedExam } : exam
      ),
      currentExam:
        state.currentExam?.uuid === examUuid
          ? { ...state.currentExam, ...updatedExam }
          : state.currentExam,
    })),

  removeExam: (examUuid) =>
    set((state) => ({
      exams: state.exams.filter((exam) => exam.uuid !== examUuid),
      currentExam:
        state.currentExam?.uuid === examUuid ? null : state.currentExam,
    })),

  addExamCriteria: (criteria) =>
    set((state) => ({ examCriteria: [...state.examCriteria, criteria] })),

  updateExamCriteria: (criteriaUuid, updatedCriteria) =>
    set((state) => ({
      examCriteria: state.examCriteria.map((criteria) =>
        criteria.uuid === criteriaUuid
          ? { ...criteria, ...updatedCriteria }
          : criteria
      ),
    })),

  removeExamCriteria: (criteriaUuid) =>
    set((state) => ({
      examCriteria: state.examCriteria.filter(
        (criteria) => criteria.uuid !== criteriaUuid
      ),
    })),

  clearError: () => set({ error: null }),

  reset: () => set(initialState),
}));
