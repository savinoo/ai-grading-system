# Arquitetura do Projeto - Corretum AI Frontend

## 📐 Clean Architecture

Este projeto foi estruturado seguindo os princípios de **Clean Architecture** (Arquitetura Limpa) de Robert C. Martin, organizando o código em camadas com responsabilidades bem definidas.

### Camadas da Aplicação

```
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER              │
│  (Components, Pages, Hooks, Routes)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        APPLICATION LAYER                │
│         (Use Cases, DTOs)               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          DOMAIN LAYER                   │
│  (Entities, Repository Interfaces)      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      INFRASTRUCTURE LAYER               │
│  (API, Repositories, External Services) │
└─────────────────────────────────────────┘
```

## 🎯 Princípios SOLID Aplicados

### 1. Single Responsibility Principle (SRP)
Cada classe/módulo tem uma única responsabilidade:

- **LoginUseCase**: Responsável apenas pela lógica de login
- **AuthRepository**: Responsável apenas pela comunicação com a API de autenticação
- **LocalStorageService**: Responsável apenas pelo armazenamento local

### 2. Open/Closed Principle (OCP)
Código aberto para extensão, fechado para modificação:

```typescript
// ❌ Antes (acoplado)
class LoginForm {
  async login(email: string, password: string) {
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    // ...
  }
}

// ✅ Depois (extensível)
interface IAuthRepository {
  login(credentials: LoginCredentials): Promise<AuthResult>;
}

class LoginUseCase {
  constructor(private authRepository: IAuthRepository) {}
  // Pode usar qualquer implementação de IAuthRepository
}
```

### 3. Liskov Substitution Principle (LSP)
Implementações podem substituir suas abstrações:

```typescript
// Qualquer implementação de IStorageService pode ser usada
const storage: IStorageService = new LocalStorageService();
// ou
const storage: IStorageService = new SessionStorageService();
// ou
const storage: IStorageService = new InMemoryStorageService();
```

### 4. Interface Segregation Principle (ISP)
Interfaces específicas ao invés de genéricas:

```typescript
// ❌ Interface genérica demais
interface IRepository {
  create(...);
  read(...);
  update(...);
  delete(...);
  login(...);
  logout(...);
}

// ✅ Interfaces segregadas
interface IAuthRepository {
  login(...);
  logout(...);
  refreshToken(...);
}

interface IStorageService {
  setItem(...);
  getItem(...);
  removeItem(...);
}
```

### 5. Dependency Inversion Principle (DIP)
Dependência de abstrações, não de implementações:

```typescript
// ❌ Dependência de implementação
class LoginUseCase {
  private authRepository = new AuthRepository(); // Acoplamento direto
}

// ✅ Dependência de abstração
class LoginUseCase {
  constructor(private authRepository: IAuthRepository) {} // Injeção de dependência
}
```

## 🏗️ Estrutura de Diretórios

```
src/
├── domain/                      # Camada de Domínio (regras de negócio)
│   ├── entities/               # Entidades de negócio
│   │   ├── User.ts            # Entidade de usuário
│   │   └── Auth.ts            # Value objects de autenticação
│   ├── repositories/          # Interfaces de repositórios (contratos)
│   │   └── IAuthRepository.ts
│   └── services/              # Interfaces de serviços
│       └── IStorageService.ts
│
├── application/                # Camada de Aplicação (casos de uso)
│   └── use-cases/
│       └── auth/
│           ├── LoginUseCase.ts           # Caso de uso: fazer login
│           ├── LogoutUseCase.ts          # Caso de uso: fazer logout
│           └── GetCurrentUserUseCase.ts  # Caso de uso: obter usuário atual
│
├── infrastructure/             # Camada de Infraestrutura (implementações)
│   ├── http/
│   │   └── HttpClient.ts      # Cliente HTTP (Axios)
│   ├── repositories/
│   │   └── AuthRepository.ts  # Implementação do IAuthRepository
│   └── services/
│       └── LocalStorageService.ts # Implementação do IStorageService
│
├── presentation/               # Camada de Apresentação (UI)
│   ├── components/
│   │   ├── ui/               # Componentes reutilizáveis
│   │   │   ├── Button.tsx
│   │   │   └── Input.tsx
│   │   ├── layout/           # Componentes de layout
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── AuthLayout.tsx
│   │   └── auth/
│   │       └── PrivateRoute.tsx
│   ├── pages/
│   │   ├── auth/
│   │   │   └── LoginPage.tsx
│   │   └── dashboard/
│   │       └── DashboardPage.tsx
│   ├── hooks/
│   │   └── useAuth.ts        # Hook customizado para autenticação
│   ├── store/
│   │   └── authStore.ts      # Estado global (Zustand)
│   └── routes/
│       └── index.tsx         # Configuração de rotas
│
└── shared/                    # Código compartilhado
    ├── constants/
    └── utils/
```

## 🔄 Fluxo de Dados

### Exemplo: Fluxo de Login

```
1. USER ACTION (Presentation)
   LoginPage.tsx
   └─> handleSubmit()
       │
2. HOOK (Presentation)
   useAuth.ts
   └─> login(email, password)
       │
3. USE CASE (Application)
   LoginUseCase.ts
   └─> execute(credentials)
       ├─> validateCredentials()
       └─> authRepository.login()
           │
4. REPOSITORY (Infrastructure)
   AuthRepository.ts
   └─> httpClient.post('/auth/login')
       ├─> Faz requisição HTTP
       ├─> Salva token no storage
       └─> Retorna User + Token
           │
5. STATE UPDATE (Presentation)
   authStore.ts
   └─> setUser(user)
       │
6. UI UPDATE (Presentation)
   LoginPage.tsx
   └─> Navigate to /dashboard
```

## 🎨 Padrões de Design Utilizados

### 1. Repository Pattern
Abstrai o acesso aos dados:

```typescript
// Interface define o contrato
interface IAuthRepository {
  login(credentials: LoginCredentials): Promise<AuthResult>;
}

// Implementação pode ser trocada sem afetar o resto do código
class AuthRepository implements IAuthRepository {
  async login(credentials: LoginCredentials): Promise<AuthResult> {
    // Implementação específica
  }
}
```

### 2. Dependency Injection
Injeção de dependências através do construtor:

```typescript
class LoginUseCase {
  constructor(private authRepository: IAuthRepository) {}
}

// Uso
const authRepository = new AuthRepository(httpClient, storageService);
const loginUseCase = new LoginUseCase(authRepository);
```

### 3. Singleton (para serviços)
Uma única instância de serviços compartilhados:

```typescript
// useAuth.ts
const storageService = new LocalStorageService(); // Singleton
const httpClient = new HttpClient(storageService); // Singleton
const authRepository = new AuthRepository(httpClient, storageService);
```

### 4. Observer Pattern (com Zustand)
Estado observável que notifica mudanças:

```typescript
const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }), // Notifica observers
}));
```

## 📝 Boas Práticas Implementadas

### 1. Separação de Responsabilidades
- **Componentes**: Apenas renderização e interação do usuário
- **Hooks**: Lógica de estado e efeitos
- **Use Cases**: Lógica de negócio pura
- **Repositories**: Comunicação com APIs
- **Services**: Serviços de infraestrutura

### 2. Inversão de Controle
```typescript
// Componente não sabe como o login funciona internamente
const { login } = useAuth();

// Hook não sabe como os dados são buscados
const loginUseCase = new LoginUseCase(authRepository);

// Use Case não sabe de onde vêm os dados
constructor(private authRepository: IAuthRepository)
```

### 3. Testabilidade
Graças à injeção de dependências, é fácil criar mocks:

```typescript
// Mock para testes
class MockAuthRepository implements IAuthRepository {
  async login() {
    return { user: mockUser, token: mockToken };
  }
}

// Uso em teste
const loginUseCase = new LoginUseCase(new MockAuthRepository());
```

### 4. Type Safety
TypeScript em todas as camadas garante type safety:

```typescript
// Tipos bem definidos
interface LoginCredentials {
  email: string;
  password: string;
}

interface User {
  id: string;
  email: string;
  // ...
}
```

## 🔐 Segurança

### 1. Tokens armazenados de forma segura
```typescript
// Tokens salvos apenas no localStorage
storageService.setItem('accessToken', token);
storageService.setItem('refreshToken', refreshToken);
```

### 2. Interceptors para autenticação
```typescript
// Adiciona token automaticamente em todas as requisições
this.client.interceptors.request.use((config) => {
  const token = this.storageService.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 3. Proteção de Rotas
```typescript
// Rotas privadas só acessíveis com autenticação
<Route element={<PrivateRoute />}>
  <Route path="/dashboard" element={<DashboardPage />} />
</Route>
```

## 🚀 Benefícios da Arquitetura

1. **Manutenibilidade**: Código organizado e fácil de encontrar
2. **Testabilidade**: Fácil criar testes unitários e de integração
3. **Escalabilidade**: Adicionar features sem quebrar código existente
4. **Reusabilidade**: Componentes e lógica podem ser reutilizados
5. **Flexibilidade**: Fácil trocar implementações (ex: mudar de API)
6. **Separação de Concerns**: Cada parte tem sua responsabilidade clara

## 📚 Próximos Passos

- Implementar testes unitários para Use Cases
- Adicionar testes de integração para Repositories
- Implementar error boundaries
- Adicionar logging centralizado
- Implementar cache de requisições
- Adicionar tratamento de erros mais robusto
