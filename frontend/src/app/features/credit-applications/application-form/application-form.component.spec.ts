import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { CreditApplicationApiService } from '../../../core/credit-application-api.service';
import { ApiError, CreditApplication } from '../../../core/models';
import { NotificationService } from '../../../core/notification.service';
import { ApplicationFormComponent } from './application-form.component';

const created: CreditApplication = {
  id: '1',
  applicant_document: '8-430-70',
  amount: 15000,
  term_months: 24,
  status: 'PENDING',
  decision_comment: null,
  decided_at: null,
  created_at: '2026-10-15T00:00:00Z',
  updated_at: '2026-10-15T00:00:00Z',
};

describe('ApplicationFormComponent', () => {
  let fixture: ComponentFixture<ApplicationFormComponent>;
  let component: ApplicationFormComponent;
  let api: { create: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    api = { create: vi.fn().mockReturnValue(of(created)) };
    await TestBed.configureTestingModule({
      imports: [ApplicationFormComponent],
      providers: [provideRouter([]), { provide: CreditApplicationApiService, useValue: api }],
    }).compileComponents();
    fixture = TestBed.createComponent(ApplicationFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  function fill(document: string, amount: number | null, term: number | null): void {
    component.form.setValue({
      applicant_document: document,
      amount: amount as number,
      term_months: term as number,
    });
  }

  function submit(): void {
    (fixture.nativeElement as HTMLElement).querySelector('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
  }

  it('marca el monto 499.99 como inválido', () => {
    component.form.controls.amount.setValue(499.99);
    expect(component.form.controls.amount.invalid).toBe(true);
  });

  it('es válido con cédula 8-430-70, monto 15000 y plazo 24', () => {
    fill('8-430-70', 15000, 24);
    expect(component.form.valid).toBe(true);
  });

  it('rechaza más de 2 decimales, plazo fuera de rango y cédula mal formada', () => {
    fill('XX-1', 1000.123, 61);
    expect(component.form.controls.amount.hasError('decimals')).toBe(true);
    expect(component.form.controls.term_months.invalid).toBe(true);
    expect(component.form.controls.applicant_document.invalid).toBe(true);
  });

  it('acepta cédulas con espacios y minúsculas', () => {
    fill(' pe-1-2 ', 500, 6);
    expect(component.form.valid).toBe(true);
  });

  it('envía la cédula normalizada, notifica y navega al listado', () => {
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fill(' 8-430-70 ', 15000, 24);
    submit();

    expect(api.create).toHaveBeenCalledWith({
      applicant_document: '8-430-70',
      amount: 15000,
      term_months: 24,
    });
    expect(TestBed.inject(NotificationService).message()).toBe('Solicitud creada correctamente.');
    expect(navigate).toHaveBeenCalledWith(['/solicitudes']);
  });

  it('no envía si el formulario es inválido y muestra los errores', () => {
    submit();
    expect(api.create).not.toHaveBeenCalled();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Este campo es obligatorio.');
  });

  it('muestra en el DOM el error de campo devuelto por el servidor', () => {
    const apiError: ApiError = {
      status: 422,
      type: 'validation_error',
      title: 'Datos inválidos',
      detail: 'La solicitud contiene datos inválidos.',
      fieldErrors: {
        applicant_document: 'La cédula no tiene un formato válido. Ejemplo: 8-430-70.',
      },
    };
    api.create.mockReturnValue(throwError(() => apiError));
    fill('8-430-70', 15000, 24);
    submit();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'La cédula no tiene un formato válido. Ejemplo: 8-430-70.',
    );
  });

  it('muestra una alerta con el detalle cuando no hay errores de campo', () => {
    api.create.mockReturnValue(
      throwError(() => ({
        status: 0,
        type: 'network_error',
        title: 'Sin conexión',
        detail: 'No se pudo conectar con el servidor.',
        fieldErrors: {},
      })),
    );
    fill('8-430-70', 15000, 24);
    submit();

    const alert = (fixture.nativeElement as HTMLElement).querySelector('[role="alert"].alert');
    expect(alert?.textContent).toContain('No se pudo conectar con el servidor.');
  });
});
