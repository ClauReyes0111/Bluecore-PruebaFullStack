import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';
import { CreditApplicationApiService } from '../../../core/credit-application-api.service';
import { ApiError, CreditApplication } from '../../../core/models';
import { DecisionDialogComponent } from './decision-dialog.component';

const pending: CreditApplication = {
  id: 'abc',
  applicant_document: '8-430-70',
  amount: 15000,
  term_months: 24,
  status: 'PENDING',
  decision_comment: null,
  decided_at: null,
  created_at: '2026-10-15T00:00:00Z',
  updated_at: '2026-10-15T00:00:00Z',
};

describe('DecisionDialogComponent', () => {
  let fixture: ComponentFixture<DecisionDialogComponent>;
  let root: HTMLElement;
  let api: { changeStatus: ReturnType<typeof vi.fn> };
  let pendingRequest: Subject<CreditApplication>;

  beforeEach(async () => {
    // jsdom no implementa showModal ni close en <dialog>.
    HTMLDialogElement.prototype.showModal ??= function () {};
    HTMLDialogElement.prototype.close ??= function () {};

    pendingRequest = new Subject<CreditApplication>();
    api = { changeStatus: vi.fn().mockReturnValue(pendingRequest) };
    await TestBed.configureTestingModule({
      imports: [DecisionDialogComponent],
      providers: [{ provide: CreditApplicationApiService, useValue: api }],
    }).compileComponents();
    fixture = TestBed.createComponent(DecisionDialogComponent);
    fixture.componentRef.setInput('application', pending);
    fixture.componentRef.setInput('decision', 'APPROVED');
    fixture.detectChanges();
    root = fixture.nativeElement as HTMLElement;
  });

  function confirmButton(): HTMLButtonElement {
    return root.querySelector('button[data-testid="confirm"]') as HTMLButtonElement;
  }

  function typeComment(text: string): void {
    const textarea = root.querySelector('textarea') as HTMLTextAreaElement;
    textarea.value = text;
    textarea.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  }

  it('deshabilita el botón con un comentario de 4 caracteres', () => {
    typeComment('abcd');
    expect(confirmButton().disabled).toBe(true);
    expect(root.textContent).toContain('El comentario debe tener entre 5 y 500 caracteres.');
  });

  it('envía una sola petición con dos clics seguidos y deja el botón deshabilitado', () => {
    typeComment('Cumple los requisitos');
    confirmButton().click();
    confirmButton().click();
    fixture.detectChanges();

    expect(api.changeStatus).toHaveBeenCalledTimes(1);
    expect(api.changeStatus).toHaveBeenCalledWith('abc', {
      status: 'APPROVED',
      comment: 'Cumple los requisitos',
    });
    expect(confirmButton().disabled).toBe(true);
  });

  it('muestra el detalle del 409 y emite conflict', () => {
    const conflict = vi.fn();
    fixture.componentInstance.conflict.subscribe(conflict);
    typeComment('Cumple los requisitos');
    confirmButton().click();

    const error: ApiError = {
      status: 409,
      type: 'conflict',
      title: 'Conflicto',
      detail: 'La solicitud ya fue aprobada y su decisión es final.',
      fieldErrors: {},
    };
    pendingRequest.error(error);
    fixture.detectChanges();

    expect(root.textContent).toContain('La solicitud ya fue aprobada y su decisión es final.');
    expect(conflict).toHaveBeenCalledTimes(1);
  });

  it('emite decided con la solicitud actualizada', () => {
    const decided = vi.fn();
    fixture.componentInstance.decided.subscribe(decided);
    typeComment('Cumple los requisitos');
    confirmButton().click();
    pendingRequest.next({ ...pending, status: 'APPROVED' });

    expect(decided).toHaveBeenCalledWith({ ...pending, status: 'APPROVED' });
  });
});
