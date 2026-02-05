import { create } from 'zustand';
import { Class, ClassWithStudents } from '../../domain/entities/Class';

interface ClassState {
  classes: Class[];
  currentClass: ClassWithStudents | null;
  isLoading: boolean;
  error: string | null;
  setClasses: (classes: Class[]) => void;
  setCurrentClass: (classData: ClassWithStudents | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  addClass: (classData: Class) => void;
  removeClass: (classUuid: string) => void;
  clearError: () => void;
}

export const useClassStore = create<ClassState>((set) => ({
  classes: [],
  currentClass: null,
  isLoading: false,
  error: null,

  setClasses: (classes) => set({ classes }),

  setCurrentClass: (classData) => set({ currentClass: classData }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  addClass: (classData) =>
    set((state) => ({ classes: [...state.classes, classData] })),

  removeClass: (classUuid) =>
    set((state) => ({
      classes: state.classes.filter((c) => c.uuid !== classUuid),
    })),

  clearError: () => set({ error: null }),
}));
