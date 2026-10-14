// Forma estándar de paginación de util.paginations.LargePagination (ver docs/modernizacion/API.md).
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
