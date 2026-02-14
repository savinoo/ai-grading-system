/**
 * Utilitários para tratamento de erros da API
 */

/**
 * Extrai a mensagem de erro do response da API
 * 
 * O backend pode retornar em diferentes formatos:
 * - Uma string simples em `detail`
 * - Um objeto { error, code, context } em `detail` (erros de validação)
 * - Um array de erros de validação do FastAPI/Pydantic
 * 
 * @param err Erro capturado no catch
 * @param fallbackMessage Mensagem padrão caso não consiga extrair a mensagem
 * @returns Mensagem de erro formatada
 */
export const extractErrorMessage = (err: any, fallbackMessage: string): string => {
  const errorDetail = err.response?.data?.detail;
  
  // Caso 1: detail é um objeto com propriedade error (nossos erros customizados)
  if (typeof errorDetail === 'object' && !Array.isArray(errorDetail) && errorDetail?.error) {
    return errorDetail.error;
  }
  
  // Caso 2: detail é uma string simples
  if (typeof errorDetail === 'string') {
    return errorDetail;
  }
  
  // Caso 3: detail é um array de erros de validação do FastAPI/Pydantic
  if (Array.isArray(errorDetail) && errorDetail.length > 0) {
    // Formatar erros de validação do Pydantic
    const firstError = errorDetail[0];
    if (firstError.msg) {
      return `${firstError.loc?.join('.') || 'Campo'}: ${firstError.msg}`;
    }
  }
  
  // Fallback
  return fallbackMessage;
};

/**
 * Extrai todos os detalhes do erro incluindo código e contexto
 * 
 * @param err Erro capturado no catch
 * @returns Objeto com message, code e context
 */
export const extractErrorDetails = (err: any): {
  message: string;
  code?: string;
  context?: any;
} => {
  const errorDetail = err.response?.data?.detail;
  
  if (typeof errorDetail === 'object' && !Array.isArray(errorDetail)) {
    return {
      message: errorDetail.error || 'Erro desconhecido',
      code: errorDetail.code,
      context: errorDetail.context,
    };
  }
  
  if (typeof errorDetail === 'string') {
    return {
      message: errorDetail,
    };
  }
  
  return {
    message: 'Erro desconhecido',
  };
};
