import { Injectable, signal } from '@angular/core';

// Servicio raíz: el mensaje sobrevive a la navegación entre pantallas.
@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly current = signal<string | null>(null);
  readonly message = this.current.asReadonly();

  show(text: string): void {
    this.current.set(text);
  }

  clear(): void {
    this.current.set(null);
  }
}
