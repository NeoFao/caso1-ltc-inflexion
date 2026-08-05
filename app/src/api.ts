// Cliente del backend. Es el unico archivo que sabe que existe una API.
//
// Los tipos reflejan lo que devuelve src/api/main.py. Si el backend cambia su
// forma, TypeScript rompe aqui y no en cinco componentes distintos.

export const CLASE = {
  MAXIMO: 1,
  MINIMO: 2,
  CONTINUIDAD: 3,
} as const;

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
}

export interface Respuesta {
  fuente: string;
  activo?: string;
  serie: Punto[];
  metricas: Metricas;
}

async function pedir<T>(ruta: string): Promise<T> {
  const respuesta = await fetch(ruta);
  if (!respuesta.ok) {
    const detalle = await respuesta.text();
    throw new Error(`${respuesta.status} en ${ruta}: ${detalle}`);
  }
  return respuesta.json() as Promise<T>;
}

export const obtenerConfiguracion = () => pedir<Configuracion>("/api/config");

export const obtenerSintetico = (n = 300, semilla = 0, ruido = 0) =>
  pedir<Respuesta>(`/api/sintetico?n=${n}&semilla=${semilla}&ruido=${ruido}`);

export const obtenerHistorico = (activo = "LTC", desde?: string, hasta?: string) => {
  const parametros = new URLSearchParams({ activo });
  if (desde) parametros.set("desde", desde);
  if (hasta) parametros.set("hasta", hasta);
  return pedir<Respuesta>(`/api/historico?${parametros}`);
};
