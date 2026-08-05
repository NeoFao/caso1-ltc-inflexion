// Cliente de datos. Es el unico archivo que sabe de donde vienen los numeros.
//
// Dos origenes, en este orden:
//   1. El backend de FastAPI, si esta levantado (desarrollo y exposicion en vivo).
//   2. Un snapshot estatico congelado por scripts/exportar_estatico.py.
//
// El respaldo no es un atajo: es RF-U5, que exige que la aplicacion arranque y
// sea usable sin conexion mostrando la antiguedad del dato. Ademas es lo que
// permite publicarla en GitHub Pages, que solo sirve archivos estaticos, y lo
// que evita depender del wifi del aula el dia de la presentacion.
//
// Los dos origenes los produce el mismo codigo Python con los mismos contratos.
// Aqui no se calcula nada (RF-U6).

export const CLASE = {
  MAXIMO: 1,
  MINIMO: 2,
  CONTINUIDAD: 3,
} as const;

export type Origen = "backend" | "snapshot";

export interface Punto {
  fecha: string;
  cierre: number;
  etiqueta: number | null;
  predicha: number | null;
}

export interface Metricas {
  n: number;
  f1_macro: number;
  precision_direccional: number;
  exactitud: number;
  [clave: string]: number;
}

export interface Configuracion {
  activos: string[];
  granularidad: string;
  w: number;
  h: number;
  latencia_real: number;
  provisional: boolean;
  panel_disponible: boolean;
  modelo?: string;
  generado_utc?: string;
  panel?: {
    filas_totales: number;
    desde: string;
    hasta: string;
    velas_exportadas_por_activo: number;
  };
}

export interface Respuesta {
  fuente: string;
  activo?: string;
  modelo?: string;
  generado_utc?: string;
  serie: Punto[];
  metricas: Metricas;
}

export interface ConOrigen<T> {
  datos: T;
  origen: Origen;
}

const BASE = import.meta.env.BASE_URL;

// Donde vive el backend. En desarrollo queda vacio y se usa /api, que el proxy
// de Vite redirige a localhost:8000. En el build de Pages se inyecta la URL
// absoluta del Space de Hugging Face mediante la variable de repositorio
// API_BASE, para no tener que tocar codigo cuando cambie de sitio.
const API = import.meta.env.VITE_API_BASE?.replace(/\/$/, "") ?? "";
const TIEMPO_LIMITE_BACKEND = 1500;

async function traer<T>(url: string, limiteMs?: number): Promise<T> {
  const control = limiteMs ? AbortSignal.timeout(limiteMs) : undefined;
  const respuesta = await fetch(url, { signal: control });
  if (!respuesta.ok) throw new Error(`${respuesta.status} en ${url}`);
  return respuesta.json() as Promise<T>;
}

/**
 * Intenta el backend y, si no responde pronto, cae al snapshot.
 *
 * El limite de tiempo es corto a proposito: si el backend no esta levantado, el
 * navegador tarda en fallar por su cuenta y la pagina se veria colgada. Mejor
 * mostrar datos congelados en un segundo y medio que una pantalla en blanco.
 */
async function conRespaldo<T>(rutaBackend: string, rutaSnapshot: string): Promise<ConOrigen<T>> {
  try {
    return { datos: await traer<T>(`${API}${rutaBackend}`, TIEMPO_LIMITE_BACKEND), origen: "backend" };
  } catch {
    return { datos: await traer<T>(`${BASE}datos/${rutaSnapshot}`), origen: "snapshot" };
  }
}

export const obtenerConfiguracion = () =>
  conRespaldo<Configuracion>("/api/config", "config.json");

export const obtenerSintetico = (n = 300, semilla = 0, ruido = 0) =>
  conRespaldo<Respuesta>(
    `/api/sintetico?n=${n}&semilla=${semilla}&ruido=${ruido}`,
    "sintetico.json",
  );

export const obtenerHistorico = (activo = "LTC") =>
  conRespaldo<Respuesta>(`/api/historico?activo=${activo}`, `historico-${activo}.json`);

/** Antiguedad legible de un snapshot, para no presentar datos viejos como frescos. */
export function antiguedad(iso?: string): string | null {
  if (!iso) return null;
  const dias = Math.floor((Date.now() - Date.parse(iso)) / 86_400_000);
  if (dias <= 0) return "hoy";
  if (dias === 1) return "ayer";
  return `hace ${dias} días`;
}
