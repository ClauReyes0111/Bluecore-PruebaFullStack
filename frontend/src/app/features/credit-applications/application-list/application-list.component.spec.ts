import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { CreditApplicationApiService } from '../../../core/credit-application-api.service';
import { CreditApplication, CreditApplicationPage } from '../../../core/models';
import { NotificationService } from '../../../core/notification.service';
import { ApplicationListComponent } from './application-list.component';

function application(id: string, status: CreditApplication['status']): CreditApplication {
  return {
    id,
    applicant_document: '8-430-70',
    amount: 15000,
    term_months: 24,
    status,
    decision_comment: null,
    decided_at: null,
    created_at: '2026-10-15T12:00:00Z',
    updated_at: '2026-10-15T12:00:00Z',
  };
}

const page: CreditApplicationPage = {
  items: [application('1', 'PENDING'), application('2', 'APPROVED')],
  total: 2,
  limit: 20,
  offset: 0,
};

describe('ApplicationListComponent', () => {
  let fixture: ComponentFixture<ApplicationListComponent>;
  let root: HTMLElement;
  let api: { list: ReturnType<typeof vi.fn> };

  async function setup(result: CreditApplicationPage, message?: string): Promise<void> {
    HTMLDialogElement.prototype.showModal ??= function () {};
    api = { list: vi.fn().mockReturnValue(of(result)) };
    await TestBed.configureTestingModule({
      imports: [ApplicationListComponent],
      providers: [provideRouter([]), { provide: CreditApplicationApiService, useValue: api }],
    }).compileComponents();
    if (message) TestBed.inject(NotificationService).show(message);
    fixture = TestBed.createComponent(ApplicationListComponent);
    fixture.detectChanges();
    root = fixture.nativeElement as HTMLElement;
  }

  function buttonTexts(row: Element): string[] {
    return Array.from(row.querySelectorAll('button')).map((b) => b.textContent!.trim());
  }

  it('muestra Aprobar y Rechazar solo en la fila PENDING', async () => {
    await setup(page);
    const rows = root.querySelectorAll('tbody tr');
    expect(rows.length).toBe(2);
    expect(buttonTexts(rows[0])).toEqual(['Aprobar', 'Rechazar']);
    expect(buttonTexts(rows[1])).toEqual([]);
  });

  it('formatea el monto como $15,000.00 y el plazo en meses', async () => {
    await setup(page);
    expect(root.textContent).toContain('$15,000.00');
    expect(root.textContent).toContain('24 meses');
  });

  it('al filtrar por Aprobadas consulta list("APPROVED", 20, 0)', async () => {
    await setup(page);
    const button = Array.from(root.querySelectorAll('button')).find(
      (b) => b.textContent!.trim() === 'Aprobadas',
    )!;
    button.click();
    fixture.detectChanges();

    expect(api.list).toHaveBeenLastCalledWith('APPROVED', 20, 0);
    expect(button.getAttribute('aria-pressed')).toBe('true');
  });

  it('muestra el estado vacío', async () => {
    await setup({ items: [], total: 0, limit: 20, offset: 0 });
    expect(root.textContent).toContain('No hay solicitudes para este filtro.');
  });

  it('vuelve a la última página válida cuando la actual queda vacía', async () => {
    const firstPage: CreditApplicationPage = {
      items: [application('1', 'PENDING')],
      total: 21,
      limit: 20,
      offset: 0,
    };
    await setup(firstPage);
    const emptyLastPage: CreditApplicationPage = { items: [], total: 20, limit: 20, offset: 20 };
    const lastValidPage: CreditApplicationPage = {
      items: [application('7', 'PENDING'), application('8', 'PENDING')],
      total: 20,
      limit: 20,
      offset: 0,
    };
    api.list.mockReturnValueOnce(of(emptyLastPage)).mockReturnValueOnce(of(lastValidPage));

    const next = Array.from(root.querySelectorAll('button')).find((b) =>
      b.textContent!.includes('Siguiente'),
    )!;
    next.click();
    fixture.detectChanges();

    expect(api.list).toHaveBeenNthCalledWith(2, null, 20, 20);
    expect(api.list).toHaveBeenNthCalledWith(3, null, 20, 0);
    expect(root.querySelectorAll('tbody tr').length).toBe(2);
    expect(root.textContent).not.toContain('No hay solicitudes para este filtro.');
    expect(root.querySelector('nav.pagination')).not.toBeNull();
  });

  it('muestra la notificación pendiente y la limpia', async () => {
    await setup(page, 'Solicitud creada correctamente.');
    expect(root.textContent).toContain('Solicitud creada correctamente.');
    expect(TestBed.inject(NotificationService).message()).toBeNull();
  });
});
