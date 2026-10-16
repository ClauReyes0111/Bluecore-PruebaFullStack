import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'solicitudes' },
  {
    path: 'solicitudes',
    loadComponent: () =>
      import('./features/credit-applications/application-list/application-list.component').then(
        (m) => m.ApplicationListComponent,
      ),
  },
  {
    path: 'solicitudes/nueva',
    loadComponent: () =>
      import('./features/credit-applications/application-form/application-form.component').then(
        (m) => m.ApplicationFormComponent,
      ),
  },
  { path: '**', redirectTo: 'solicitudes' },
];
