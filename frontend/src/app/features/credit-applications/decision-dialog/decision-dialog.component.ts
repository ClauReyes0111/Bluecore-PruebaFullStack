import { CurrencyPipe } from '@angular/common';
import {
  Component,
  ElementRef,
  afterNextRender,
  computed,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { CreditApplicationApiService } from '../../../core/credit-application-api.service';
import { ApiError, CreditApplication } from '../../../core/models';

const MIN_LENGTH = 5;
const MAX_LENGTH = 500;

@Component({
  selector: 'app-decision-dialog',
  imports: [CurrencyPipe],
  templateUrl: './decision-dialog.component.html',
  styleUrl: './decision-dialog.component.css',
})
export class DecisionDialogComponent {
  private readonly api = inject(CreditApplicationApiService);
  private readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('dialog');

  readonly application = input.required<CreditApplication>();
  readonly decision = input.required<'APPROVED' | 'REJECTED'>();
  readonly decided = output<CreditApplication>();
  readonly conflict = output<void>();
  readonly cancelled = output<void>();

  protected readonly comment = signal('');
  protected readonly saving = signal(false);
  protected readonly serverError = signal<string | null>(null);
  protected readonly touched = signal(false);

  protected readonly trimmedLength = computed(() => this.comment().trim().length);
  protected readonly commentValid = computed(
    () => this.trimmedLength() >= MIN_LENGTH && this.trimmedLength() <= MAX_LENGTH,
  );
  protected readonly isApproval = computed(() => this.decision() === 'APPROVED');
  protected readonly maxLength = MAX_LENGTH;

  constructor() {
    afterNextRender(() => this.dialog().nativeElement.showModal());
  }

  protected onComment(event: Event): void {
    this.comment.set((event.target as HTMLTextAreaElement).value);
    this.touched.set(true);
  }

  protected cancel(): void {
    if (!this.saving()) this.cancelled.emit();
  }

  protected onNativeCancel(event: Event): void {
    // Esc: el cierre lo decide el padre al quitar el diálogo.
    event.preventDefault();
    this.cancel();
  }

  protected submit(): void {
    if (this.saving() || !this.commentValid()) return;
    this.saving.set(true);
    this.serverError.set(null);
    this.api
      .changeStatus(this.application().id, {
        status: this.decision(),
        comment: this.comment().trim(),
      })
      .subscribe({
        next: (updated) => this.decided.emit(updated),
        error: (error: ApiError) => {
          this.saving.set(false);
          this.serverError.set(error.detail);
          if (error.status === 409) this.conflict.emit();
        },
      });
  }
}
