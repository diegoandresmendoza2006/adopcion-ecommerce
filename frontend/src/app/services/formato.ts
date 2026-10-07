// El backend guarda la edad en MESES (campo edad_meses)
export function edadTexto(meses: number | null | undefined): string {
  if (meses === null || meses === undefined) return 'N/A';
  if (meses < 12) return `${meses} ${meses === 1 ? 'mes' : 'meses'}`;
  const anios = Math.floor(meses / 12);
  return `${anios} ${anios === 1 ? 'año' : 'años'}`;
}

export function estaDisponible(m: any): boolean {
  return (m?.estado_adopcion || '').toLowerCase() === 'disponible';
}