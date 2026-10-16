import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

// Misma expresión que el backend, aplicada sobre el valor normalizado.
const DOCUMENT_PATTERN = /^(?:(?:[1-9]|1[0-3])(?:AV|PI)?|E|N|PE)-[0-9]{1,4}-[0-9]{1,6}$/;

export function normalizeDocument(value: string): string {
  return value.replace(/\s+/g, '').toUpperCase();
}

export const documentValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const value = control.value as string;
  if (!value || !value.trim()) return null; // de eso se ocupa Validators.required
  return DOCUMENT_PATTERN.test(normalizeDocument(value)) ? null : { document: true };
};

export const maxTwoDecimalsValidator: ValidatorFn = (
  control: AbstractControl,
): ValidationErrors | null => {
  const value = control.value as number | null;
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  const decimals = String(value).split('.')[1];
  return decimals !== undefined && decimals.length > 2 ? { decimals: true } : null;
};

export const integerValidator: ValidatorFn = (
  control: AbstractControl,
): ValidationErrors | null => {
  const value = control.value as number | null;
  if (value === null || value === undefined) return null;
  return Number.isInteger(value) ? null : { integer: true };
};
