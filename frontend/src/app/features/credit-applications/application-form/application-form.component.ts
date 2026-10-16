import { Component, inject, signal } from '@angular/core';
import { AbstractControl, NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CreditApplicationApiService } from '../../../core/credit-application-api.service';
import { ApiError } from '../../../core/models';
import { NotificationService } from '../../../core/notification.service';
import {
  documentValidator,
  integerValidator,
  maxTwoDecimalsValidator,
  normalizeDocument,
} from './application-form.validators';

// Textos idénticos a los del backend.
const MESSAGES: Record<string, string> = {
  required: 'Este campo es obligatorio.',
  document: 'La cédula no tiene un formato válido. Ejemplo: 8-430-70.',
  integer: 'Debe ser un número entero.',
  decimals: 'El monto admite como máximo 2 decimales.',
};
const RANGE_MESSAGES: Record<string, string> = {
  amount: 'El monto debe estar entre $500.00 y $50,000.00.',
  term_months: 'El plazo debe estar entre 6 y 60 meses.',
};
// Orden de prioridad cuando un control tiene varios errores.
const ERROR_ORDER = ['server', 'required', 'document', 'integer', 'decimals', 'min', 'max'];

@Component({
  selector: 'app-application-form',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './application-form.component.html',
  styleUrl: './application-form.component.css',
})
export class ApplicationFormComponent {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(CreditApplicationApiService);
  private readonly notification = inject(NotificationService);
  private readonly router = inject(Router);

  readonly form = this.fb.group({
    applicant_document: this.fb.control('', [Validators.required, documentValidator]),
    amount: this.fb.control<number | null>(null, [
      Validators.required,
      Validators.min(500),
      Validators.max(50000),
      maxTwoDecimalsValidator,
    ]),
    term_months: this.fb.control<number | null>(null, [
      Validators.required,
      integerValidator,
      Validators.min(6),
      Validators.max(60),
    ]),
  });

  protected readonly saving = signal(false);
  protected readonly formError = signal<string | null>(null);

  protected errorMessage(name: 'applicant_document' | 'amount' | 'term_months'): string | null {
    const control: AbstractControl = this.form.controls[name];
    if (!control.touched || !control.errors) return null;
    const key = ERROR_ORDER.find((k) => k in control.errors!);
    if (key === undefined) return null;
    if (key === 'server') return control.errors['server'] as string;
    if (key === 'min' || key === 'max') return RANGE_MESSAGES[name] ?? null;
    return MESSAGES[key] ?? null;
  }

  protected submit(): void {
    this.formError.set(null);
    this.form.markAllAsTouched();
    if (this.form.invalid || this.saving()) return;

    const { applicant_document, amount, term_months } = this.form.getRawValue();
    this.saving.set(true);
    this.api
      .create({
        applicant_document: normalizeDocument(applicant_document),
        amount: amount as number,
        term_months: term_months as number,
      })
      .subscribe({
        next: () => {
          this.notification.show('Solicitud creada correctamente.');
          void this.router.navigate(['/solicitudes']);
        },
        error: (error: ApiError) => {
          this.saving.set(false);
          this.showServerError(error);
        },
      });
  }

  private showServerError(error: ApiError): void {
    let matched = 0;
    for (const [field, message] of Object.entries(error.fieldErrors)) {
      const control = this.form.get(field);
      if (control) {
        control.setErrors({ server: message });
        control.markAsTouched();
        matched++;
      }
    }
    if (matched === 0) this.formError.set(error.detail);
  }
}
