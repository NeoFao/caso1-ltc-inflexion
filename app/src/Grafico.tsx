import { createChart, type IChartApi, type ISeriesApi, type UTCTimestamp } from "lightweight-charts";
import { useEffect, useRef } from "react";

import { CLASE, type Punto } from "./api";

const NAVY = "#1b2a4a";
const MAXIMO = "#c0392b";
const MINIMO = "#1e8449";
const GRIS = "#5a6675";
const REJILLA = "#e3e8ef";

interface Props {
  puntos: Punto[];
  mostrarPredichas?: boolean;
}

/**
 * Serie de precio con los giros marcados encima.
 *
 * Los reales van como marcadores rellenos debajo/encima de la vela y los
 * predichos con una flecha. Superponerlos en el mismo eje es lo que hace visible
 * de un vistazo donde el modelo acierta y donde inventa; en una matriz de
 * confusion esa informacion existe pero no se ve.
 */
export default function Grafico({ puntos, mostrarPredichas = true }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const grafico = useRef<IChartApi | null>(null);
  const serie = useRef<ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    if (!contenedor.current) return;

    grafico.current = createChart(contenedor.current, {
      layout: { background: { color: "#ffffff" }, textColor: GRIS, fontSize: 12 },
      grid: { vertLines: { color: REJILLA }, horzLines: { color: REJILLA } },
      rightPriceScale: { borderColor: REJILLA },
      timeScale: { borderColor: REJILLA, timeVisible: false },
      crosshair: { mode: 1 },
      autoSize: true,
    });
    serie.current = grafico.current.addLineSeries({ color: NAVY, lineWidth: 2 });

    return () => {
      grafico.current?.remove();
      grafico.current = null;
      serie.current = null;
    };
  }, []);

  useEffect(() => {
    if (!serie.current || puntos.length === 0) return;

    serie.current.setData(
      puntos.map((p) => ({
        time: (Date.parse(p.fecha) / 1000) as UTCTimestamp,
        value: p.cierre,
      })),
    );

    const marcadores = puntos.flatMap((p) => {
      const salida = [];
      if (p.etiqueta === CLASE.MAXIMO || p.etiqueta === CLASE.MINIMO) {
        const esMaximo = p.etiqueta === CLASE.MAXIMO;
        salida.push({
          time: (Date.parse(p.fecha) / 1000) as UTCTimestamp,
          position: esMaximo ? ("aboveBar" as const) : ("belowBar" as const),
          color: esMaximo ? MAXIMO : MINIMO,
          shape: "circle" as const,
          text: esMaximo ? "max" : "min",
        });
      }
      if (
        mostrarPredichas &&
        (p.predicha === CLASE.MAXIMO || p.predicha === CLASE.MINIMO)
      ) {
        const esMaximo = p.predicha === CLASE.MAXIMO;
        salida.push({
          time: (Date.parse(p.fecha) / 1000) as UTCTimestamp,
          position: esMaximo ? ("aboveBar" as const) : ("belowBar" as const),
          color: esMaximo ? MAXIMO : MINIMO,
          shape: esMaximo ? ("arrowDown" as const) : ("arrowUp" as const),
        });
      }
      return salida;
    });

    serie.current.setMarkers(marcadores);
    grafico.current?.timeScale().fitContent();
  }, [puntos, mostrarPredichas]);

  return <div ref={contenedor} className="h-[420px] w-full" />;
}
