// Pequeñas ayudas de interfaz compartidas por varias pantallas.

// Sube al inicio de la página y pone el cursor en el primer campo del formulario.
// Se usa al pulsar "Editar", para que el formulario salga de primero.
export function irAlFormulario(idPrimerCampo: string): void {
  if (typeof window === 'undefined') return;
  window.scrollTo({ top: 0, behavior: 'smooth' });
  setTimeout(() => document.getElementById(idPrimerCampo)?.focus({ preventScroll: true }), 200);
}

// Pone primero en la lista el registro que se acaba de editar (para encontrarlo fácil).
export function editadoPrimero<T extends { id: number }>(lista: T[], idEditado: number | null): T[] {
  if (idEditado === null) return lista;
  const i = lista.findIndex(x => x.id === idEditado);
  if (i <= 0) return lista;
  return [lista[i], ...lista.slice(0, i), ...lista.slice(i + 1)];
}
