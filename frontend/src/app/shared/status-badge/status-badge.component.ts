import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { ApplicationStatus } from '../../core/models';

const LABELS: Record<ApplicationStatus, string> = {
  PENDING: 'Pendiente',
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
};

@Component({
  selector: 'app-status-badge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  styleUrl: './status-badge.component.css',
  template: `<span [class]="cssClass()">{{ label() }}</span>`,
})
export class StatusBadgeComponent {
  readonly status = input.required<ApplicationStatus>();
  protected readonly label = computed(() => LABELS[this.status()]);
  protected readonly cssClass = computed(() => `badge badge--${this.status().toLowerCase()}`);
}
