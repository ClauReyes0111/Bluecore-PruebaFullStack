import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiError } from './models';
import { errorInterceptor } from './error.interceptor';

describe('errorInterceptor', () => {
  let http: HttpClient;
  let controller: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([errorInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    controller = TestBed.inject(HttpTestingController);
  });

  afterEach(() => controller.verify());

  it('convierte un error de red en un ApiError de conexión', () => {
    let error: ApiError | undefined;
    http.get('/x').subscribe({ error: (e: ApiError) => (error = e) });
    controller.expectOne('/x').error(new ProgressEvent('error'));

    expect(error?.status).toBe(0);
    expect(error?.title).toBe('Sin conexión');
    expect(error?.detail).toBe('No se pudo conectar con el servidor.');
    expect(error?.fieldErrors).toEqual({});
  });

  it('convierte Problem Details 422 en ApiError con fieldErrors', () => {
    let error: ApiError | undefined;
    http.get('/x').subscribe({ error: (e: ApiError) => (error = e) });
    controller.expectOne('/x').flush(
      {
        type: 'validation_error',
        title: 'Datos inválidos',
        status: 422,
        detail: 'La solicitud contiene datos inválidos.',
        errors: [
          { field: 'amount', message: 'El monto debe estar entre $500.00 y $50,000.00.' },
        ],
      },
      { status: 422, statusText: 'Unprocessable Entity' },
    );

    expect(error?.status).toBe(422);
    expect(error?.type).toBe('validation_error');
    expect(error?.title).toBe('Datos inválidos');
    expect(error?.fieldErrors['amount']).toBe('El monto debe estar entre $500.00 y $50,000.00.');
  });

  it('usa un mensaje genérico cuando el cuerpo no es Problem Details', () => {
    let error: ApiError | undefined;
    http.get('/x').subscribe({ error: (e: ApiError) => (error = e) });
    controller.expectOne('/x').flush('boom', { status: 500, statusText: 'Server Error' });

    expect(error?.status).toBe(500);
    expect(error?.title).toBe('Error');
    expect(error?.detail).toBe('Ocurrió un error inesperado.');
    expect(error?.fieldErrors).toEqual({});
  });

  it('trata un 504 del proxy sin Problem Details como falta de conexión', () => {
    let error: ApiError | undefined;
    http.get('/x').subscribe({ error: (e: ApiError) => (error = e) });
    controller
      .expectOne('/x')
      .flush('Gateway Timeout', { status: 504, statusText: 'Gateway Timeout' });

    expect(error?.status).toBe(504);
    expect(error?.title).toBe('Sin conexión');
    expect(error?.detail).toBe('No se pudo conectar con el servidor.');
  });

  it('conserva el Problem Details de un 503 del backend', () => {
    let error: ApiError | undefined;
    http.get('/x').subscribe({ error: (e: ApiError) => (error = e) });
    controller.expectOne('/x').flush(
      { type: 'service_unavailable', title: 'Servicio no disponible', detail: 'Base de datos no disponible.' },
      { status: 503, statusText: 'Service Unavailable' },
    );

    expect(error?.status).toBe(503);
    expect(error?.type).toBe('service_unavailable');
    expect(error?.detail).toBe('Base de datos no disponible.');
  });
});
