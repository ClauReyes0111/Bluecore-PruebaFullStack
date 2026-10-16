import { CurrencyPipe, DatePipe } from '@angular/common';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { CreditApplicationApiService } from '../../../core/credit-application-api.service';
import {
  ApiError,
  ApplicationStatus,
  CreditApplication,
  CreditApplicationPage,
} from '../../../core/models';
import { NotificationService } from '../../../core/notification.service';
import { StatusBadgeComponent } from '../../../shared/status-badge/status-badge.component';
import { DecisionDialogComponent } from '../decision-dialog/decision-dialog.component';

const PAGE_SIZE = 20;

const FILTERS: { label: string; value: ApplicationStatus | null }[] = [
  { label: 'Todas', value: null },
  { label: 'Pendientes', value: 'PENDING' },
  { label: 'Aprobadas', value: 'APPROVED' },
  { label: 'Rechazadas', value: 'REJECTED' },
];

interface PendingDecision {
  application: CreditApplication;
  decision: 'APPROVED' | 'REJECTED';
}

@Component({
  selector: 'app-application-list',
  imports: [CurrencyPipe, DatePipe, RouterLink, StatusBadgeComponent, DecisionDialogComponent],
  templateUrl: './application-list.component.html',
  styleUrl: './application-list.component.css',
})
export class ApplicationListComponent implements OnInit {
  private readonly api = inject(CreditApplicationApiService);
  private readonly notification = inject(NotificationService);
  private request: Subscription | null = null;

  protected readonly filters = FILTERS;
  protected readonly status = signal<ApplicationStatus | null>(null);
  protected readonly offset = signal(0);
  protected readonly page = signal<CreditApplicationPage | null>(null);
  protected readonly loading = signal(false);
  protected readonly loadError = signal<string | null>(null);
  protected readonly message = signal<string | null>(null);
  protected readonly deciding = signal<PendingDecision | null>(null);

  protected readonly rangeStart = computed(() => (this.page()?.total ? this.offset() + 1 : 0));
  protected readonly rangeEnd = computed(() =>
    Math.min(this.offset() + PAGE_SIZE, this.page()?.total ?? 0),
  );
  protected readonly hasPrevious = computed(() => this.offset() > 0);
  protected readonly hasNext = computed(() => this.offset() + PAGE_SIZE < (this.page()?.total ?? 0));

  constructor() {
    inject(DestroyRef).onDestroy(() => this.request?.unsubscribe());
  }

  ngOnInit(): void {
    // El mensaje se muestra una vez: se copia al estado local y se limpia del servicio.
    this.message.set(this.notification.message());
    this.notification.clear();
    this.load();
  }

  protected setFilter(value: ApplicationStatus | null): void {
    this.status.set(value);
    this.offset.set(0);
    this.load();
  }

  protected goTo(offset: number): void {
    this.offset.set(Math.max(0, offset));
    this.load();
  }

  protected load(): void {
    this.request?.unsubscribe();
    this.loading.set(true);
    this.loadError.set(null);
    this.request = this.api.list(this.status(), PAGE_SIZE, this.offset()).subscribe({
      next: (page) => {
        // Si al decidir el último elemento la página queda vacía, se vuelve a la última válida
        if (page.items.length === 0 && this.offset() > 0 && page.total > 0) {
          this.offset.set(Math.floor((page.total - 1) / PAGE_SIZE) * PAGE_SIZE);
          this.load();
          return;
        }
        this.page.set(page);
        this.loading.set(false);
      },
      error: (error: ApiError) => {
        this.loading.set(false);
        this.loadError.set(error.detail);
      },
    });
  }

  protected openDecision(application: CreditApplication, decision: 'APPROVED' | 'REJECTED'): void {
    this.deciding.set({ application, decision });
  }

  protected closeDialog(): void {
    this.deciding.set(null);
  }

  protected onDecided(decision: 'APPROVED' | 'REJECTED'): void {
    this.closeDialog();
    this.message.set(
      decision === 'APPROVED'
        ? 'Solicitud aprobada correctamente.'
        : 'Solicitud rechazada correctamente.',
    );
    this.load();
  }
}
