import { Mascota } from '../models/modelos';

// El backend guarda la edad en MESES (campo edad_meses)
export function edadTexto(meses: number | null | undefined): string {
  if (meses === null || meses === undefined) return 'N/A';
  if (meses < 12) return `${meses} ${meses === 1 ? 'mes' : 'meses'}`;
  const anios = Math.floor(meses / 12);
  return `${anios} ${anios === 1 ? 'año' : 'años'}`;
}

export function estaDisponible(m: Pick<Mascota, 'estado_adopcion'> | null | undefined): boolean {
  return (m?.estado_adopcion || '').toLowerCase() === 'disponible';
}

// "Sí" / "No" / "—" para mostrar datos del formulario de adopción
export function siNo(valor: boolean | null | undefined): string {
  return valor === null || valor === undefined ? '—' : valor ? 'Sí' : 'No';
}

// Edad a partir de la fecha de nacimiento (AAAA-MM-DD)
export function edadDesdeNacimiento(fecha: string | null | undefined): number | null {
  if (!fecha) return null;
  const nac = new Date(fecha + 'T00:00:00');
  if (isNaN(nac.getTime())) return null;
  const hoy = new Date();
  let edad = hoy.getFullYear() - nac.getFullYear();
  if (hoy.getMonth() < nac.getMonth() || (hoy.getMonth() === nac.getMonth() && hoy.getDate() < nac.getDate())) edad--;
  return edad;
}
