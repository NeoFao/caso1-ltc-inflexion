import { useEffect, useState } from "react";

import Grafico from "./Grafico";
import {
  type Configuracion,
  type Respuesta,
  obtenerConfiguracion,
  obtenerHistorico,
  obtenerSintetico,
} from "./api";

type Modo = "sintetico" | "historico" | "tiempo-real";

const MODOS: { id: Modo; etiqueta: string; descripcion: string }[] = [
  {
    id: "sintetico",
    etiqueta: "Sintético",
    descripcion: "Serie construida con giros conocidos. La única prueba donde la verdad no está en discusión.",
  },
  {
    id: "historico",
    etiqueta: "Histórico",
    descripcion: "Rango del panel real, con las etiquetas verdaderas junto a las predichas.",
  },
  {
    id: "tiempo-real",
    etiqueta: "Tiempo real",
    descripcion: "Últimas velas descargadas en vivo, sin etiqueta conocida todavía.",
  },
];

export default function App() {
  const [modo, setModo] = useState<Modo>("sintetico");
  const [configuracion, setConfiguracion] = useState<Configuracion | null>(null);
  const [datos, setDatos] = useState<Respuesta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    obtenerConfiguracion().then(setConfiguracion).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (modo === "tiempo-real") {
      setDatos(null);
      return;
    }
    setCargando(true);
    setError(null);
    const peticion = modo === "sintetico" ? obtenerSintetico(300) : obtenerHistorico("LTC");
    peticion
      .then(setDatos)
      .catch((e) => setError(String(e)))
      .finally(() => setCargando(false));
  }, [modo]);

  const modoActual = MODOS.find((m) => m.id === modo)!;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <p className="text-xs font-semibold tracking-[0.2em] text-[#345d9d]">
            CASO N.º 1 · SEÑALES Y SISTEMAS
          </p>
          <h1 className="mt-1 text-2xl font-bold text-[#1b2a4a]">
            Puntos de inflexión en el precio de Litecoin
          </h1>
          {configuracion && (
            <p className="mt-2 text-sm text-slate-500">
              Ventana w={configuracion.w} · horizonte h={configuracion.h} · velas de{" "}
              {configuracion.granularidad} · anticipación efectiva{" "}
              {configuracion.latencia_real} velas
              {configuracion.provisional && (
                <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                  parámetros provisionales
                </span>
              )}
            </p>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-6">
        <nav className="flex gap-2">
          {MODOS.map((m) => (
            <button
              key={m.id}
              onClick={() => setModo(m.id)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                modo === m.id
                  ? "bg-[#1b2a4a] text-white"
                  : "bg-white text-slate-600 hover:bg-slate-100"
              }`}
            >
              {m.etiqueta}
            </button>
          ))}
        </nav>
        <p className="mt-3 text-sm text-slate-500">{modoActual.descripcion}</p>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
            <p className="mt-2 text-red-600">
              ¿Está corriendo el backend? <code>uv run uvicorn src.api.main:app --port 8000</code>
            </p>
          </div>
        )}

        <section className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          {modo === "tiempo-real" ? (
            <p className="py-24 text-center text-sm text-slate-400">
              Pendiente (RF-U3). Depende de definir qué se considera tiempo real: consulta 3 al
              profesor.
            </p>
          ) : cargando ? (
            <p className="py-24 text-center text-sm text-slate-400">Cargando…</p>
          ) : datos ? (
            <Grafico puntos={datos.serie} />
          ) : null}
        </section>

        {datos && (
          <section className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Metrica titulo="F1 macro" valor={datos.metricas.f1_macro} />
            <Metrica titulo="Precisión direccional" valor={datos.metricas.precision_direccional} />
            <Metrica titulo="Exactitud" valor={datos.metricas.exactitud} />
            <Metrica titulo="Observaciones" valor={datos.metricas.n} entero />
          </section>
        )}

        <p className="mt-6 text-xs text-slate-400">
          Las métricas provienen de <code>contracts/metrics.py</code>. Esta aplicación no calcula
          ninguna: si lo hiciera, tarde o temprano darían distinto que el informe.
        </p>
      </main>
    </div>
  );
}

function Metrica({ titulo, valor, entero }: { titulo: string; valor: number; entero?: boolean }) {
  const texto = Number.isNaN(valor)
    ? "—"
    : entero
      ? valor.toLocaleString("es-CR")
      : valor.toFixed(3);
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{titulo}</p>
      <p className="mt-1 text-2xl font-bold text-[#1b2a4a]">{texto}</p>
    </div>
  );
}
