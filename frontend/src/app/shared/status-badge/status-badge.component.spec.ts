import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ApplicationStatus } from '../../core/models';
import { StatusBadgeComponent } from './status-badge.component';

describe('StatusBadgeComponent', () => {
  function render(status: ApplicationStatus): HTMLElement {
    const fixture: ComponentFixture<StatusBadgeComponent> =
      TestBed.createComponent(StatusBadgeComponent);
    fixture.componentRef.setInput('status', status);
    fixture.detectChanges();
    return fixture.nativeElement.querySelector('.badge') as HTMLElement;
  }

  it.each([
    ['APPROVED', 'Aprobada', 'badge--approved'],
    ['PENDING', 'Pendiente', 'badge--pending'],
    ['REJECTED', 'Rechazada', 'badge--rejected'],
  ] as [ApplicationStatus, string, string][])('%s muestra %s', (status, text, cssClass) => {
    const badge = render(status);
    expect(badge.textContent?.trim()).toBe(text);
    expect(badge.classList).toContain(cssClass);
  });
});
