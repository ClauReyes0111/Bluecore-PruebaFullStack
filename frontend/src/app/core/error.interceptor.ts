import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
import { ApiError } from './models';

interface ProblemBody {
  type: string;
  title: string;
  detail: string;
  errors?: { field: string; message: string }[];
}

// Un cuerpo se considera Problem Details solo si trae los tres campos de texto.
function isProblem(body: unknown): body is ProblemBody {
  if (typeof body !== 'object' || body === null) return false;
  const b = body as Record<string, unknown>;
  return (
    typeof b['type'] === 'string' &&
    typeof b['title'] === 'string' &&
    typeof b['detail'] === 'string'
  );
}

function toApiError(error: HttpErrorResponse): ApiError {
  if (error.status === 0) {
    return {
      status: 0,
      type: 'network_error',
      title: 'Sin conexión',
      detail: 'No se pudo conectar con el servidor.',
      fieldErrors: {},
    };
  }
  if (isProblem(error.error)) {
    const fieldErrors: Record<string, string> = {};
    for (const item of error.error.errors ?? []) {
      fieldErrors[item.field] = item.message;
    }
    const { type, title, detail } = error.error;
    return { status: error.status, type, title, detail, fieldErrors };
  }
  return {
    status: error.status,
    type: 'unknown_error',
    title: 'Error',
    detail: 'Ocurrió un error inesperado.',
    fieldErrors: {},
  };
}

export const errorInterceptor: HttpInterceptorFn = (req, next) =>
  next(req).pipe(catchError((error: HttpErrorResponse) => throwError(() => toApiError(error))));
