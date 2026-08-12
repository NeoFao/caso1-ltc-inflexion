// Genera la base del documento de la Semana 1 en Word, con formato APA 7.
//
// La rubrica evalua "cumplimiento del formato APA" sin indicar edicion; APA 7 es
// la vigente desde 2019. Todo lo de este archivo sale del Publication Manual 7.a
// ed.: Times New Roman 12, doble espacio, margenes de una pulgada, sangria de
// primera linea de media pulgada, numero de pagina arriba a la derecha, niveles
// de titulo, tablas sin lineas verticales y referencias con sangria francesa.
//
// Monocromo a proposito. Lo unico que no es negro son los marcadores de texto
// pendiente, en gris, para que se vean y se borren. Si queda uno, se nota.
//
// Uso:
//   npm install --prefix scripts
//   npm run semana1 --prefix scripts

const {
  Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType, HeadingLevel,
  Table, TableRow, TableCell, WidthType, BorderStyle, TabStopType,
  Header, PageNumber, PageBreak, TableOfContents, LineRuleType,
} = require('docx');
const fs = require('fs');
const path = require('path');

const RAIZ = path.resolve(__dirname, '..');
const EVIDENCIAS = path.join(RAIZ, 'docs', 'evidencias');
const medido = JSON.parse(fs.readFileSync(path.join(EVIDENCIAS, 'marco-teorico.json'), 'utf8'));

const FUENTE = 'Times New Roman';
const TAM = 24;              // 12 pt en medios puntos
const DOBLE = 480;           // 240 = simple, 480 = doble
const SANGRIA = 720;         // media pulgada
const NEGRO = '000000';
const GRIS = '595959';       // solo para lo pendiente
const ANCHO_UTIL = 9360;     // 12240 (carta) - 2 * 1440 (margenes)
const ANCHO_IMAGEN = 600;    // px a 96 dpi ~ 6.25 pulgadas

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

/** "2020-08-11" -> "11 de agosto de 2020". En prosa castellana el ISO desentona. */
const fechaLarga = (iso) => {
  const [anio, mes, dia] = iso.slice(0, 10).split('-');
  return `${Number(dia)} de ${MESES[Number(mes) - 1]} de ${anio}`;
};

const nf = (valor, decimales = 3) =>
  Number(valor).toLocaleString('es-CR', {
    minimumFractionDigits: decimales, maximumFractionDigits: decimales,
  });

// --- bloques de texto -------------------------------------------------------

/** Parrafo de cuerpo: doble espacio y sangria de primera linea, como pide APA. */
const p = (texto, opciones = {}) => new Paragraph({
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
  indent: opciones.sinSangria ? undefined : { firstLine: SANGRIA },
  alignment: opciones.alineacion,
  children: [new TextRun({
    text: texto, font: FUENTE, size: TAM, color: NEGRO,
    bold: opciones.negrita, italics: opciones.cursiva,
  })],
});

/** Marcador de contenido pendiente. En gris para que sea imposible dejarlo. */
const pendiente = (instruccion) => new Paragraph({
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
  indent: { firstLine: SANGRIA },
  children: [new TextRun({
    text: `[PENDIENTE DE REDACCION — ${instruccion} Borrar este parrafo al completarlo.]`,
    font: FUENTE, size: TAM, color: GRIS, italics: true,
  })],
});

// Niveles de titulo APA 7. El 1 va centrado y en negrita; el 2 al margen
// izquierdo y en negrita; el 3 al margen izquierdo, negrita y cursiva.
const titulo1 = (texto) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  alignment: AlignmentType.CENTER,
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 0, after: 0 },
  children: [new TextRun({ text: texto, font: FUENTE, size: TAM, bold: true, color: NEGRO })],
});

const titulo2 = (texto) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 0, after: 0 },
  children: [new TextRun({ text: texto, font: FUENTE, size: TAM, bold: true, color: NEGRO })],
});

const titulo3 = (texto) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 0, after: 0 },
  children: [new TextRun({
    text: texto, font: FUENTE, size: TAM, bold: true, italics: true, color: NEGRO,
  })],
});

// --- figuras ----------------------------------------------------------------

function dimensiones(archivo) {
  const buffer = fs.readFileSync(archivo);
  return { ancho: buffer.readUInt32BE(16), alto: buffer.readUInt32BE(20), buffer };
}

/**
 * Figura en formato APA 7: numero en negrita, titulo en cursiva debajo, la
 * imagen, y una nota que empieza con "Nota." en cursiva.
 */
function figura(numero, tituloFigura, archivo, nota) {
  const { ancho, alto, buffer } = dimensiones(path.join(EVIDENCIAS, archivo));
  const escalado = Math.round(ANCHO_IMAGEN * (alto / ancho));
  return [
    // keepNext evita que el numero y el titulo queden al final de una pagina con
    // la imagen en la siguiente, que es como salio en la primera version.
    new Paragraph({
      keepNext: true,
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 240, after: 0 },
      children: [new TextRun({
        text: `Figura ${numero}`, font: FUENTE, size: TAM, bold: true, color: NEGRO,
      })],
    }),
    new Paragraph({
      keepNext: true,
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 120 },
      children: [new TextRun({
        text: tituloFigura, font: FUENTE, size: TAM, italics: true, color: NEGRO,
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 120 },
      children: [new ImageRun({
        data: buffer, type: 'png',
        transformation: { width: ANCHO_IMAGEN, height: escalado },
      })],
    }),
    new Paragraph({
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 240 },
      children: [
        new TextRun({ text: 'Nota.', font: FUENTE, size: TAM, italics: true, color: NEGRO }),
        new TextRun({ text: ` ${nota}`, font: FUENTE, size: TAM, color: NEGRO }),
      ],
    }),
  ];
}

// --- tablas -----------------------------------------------------------------

const celda = (texto, opciones = {}) => new TableCell({
  width: { size: opciones.ancho, type: WidthType.DXA },
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  borders: {
    top: opciones.bordeArriba
      ? { style: BorderStyle.SINGLE, size: 6, color: NEGRO }
      : { style: BorderStyle.NONE },
    bottom: opciones.bordeAbajo
      ? { style: BorderStyle.SINGLE, size: 6, color: NEGRO }
      : { style: BorderStyle.NONE },
    left: { style: BorderStyle.NONE },
    right: { style: BorderStyle.NONE },
  },
  children: [new Paragraph({
    spacing: { line: 240, lineRule: LineRuleType.AUTO, after: 0 },
    alignment: opciones.alineacion,
    children: [new TextRun({
      text: texto, font: FUENTE, size: TAM, color: NEGRO, italics: opciones.cursiva,
    })],
  })],
});

/**
 * Tabla en formato APA 7: sin lineas verticales, sin sombreados, y solo tres
 * lineas horizontales — encima del encabezado, debajo del encabezado y al final.
 */
function tabla(numero, tituloTabla, encabezados, filas, anchos, nota) {
  const total = anchos.reduce((a, b) => a + b, 0);
  const escalados = anchos.map((a) => Math.round((a / total) * ANCHO_UTIL));

  const elementos = [
    new Paragraph({
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 240, after: 0 },
      children: [new TextRun({
        text: `Tabla ${numero}`, font: FUENTE, size: TAM, bold: true, color: NEGRO,
      })],
    }),
    new Paragraph({
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 60 },
      children: [new TextRun({
        text: tituloTabla, font: FUENTE, size: TAM, italics: true, color: NEGRO,
      })],
    }),
    new Table({
      columnWidths: escalados,
      width: { size: ANCHO_UTIL, type: WidthType.DXA },
      // APA 7 no admite lineas verticales ni lineas entre filas. Hay que anularlas
      // a nivel de tabla: los bordes de celda no bastan porque la tabla dibuja los
      // suyos por encima.
      borders: {
        top: { style: BorderStyle.NONE },
        bottom: { style: BorderStyle.NONE },
        left: { style: BorderStyle.NONE },
        right: { style: BorderStyle.NONE },
        insideHorizontal: { style: BorderStyle.NONE },
        insideVertical: { style: BorderStyle.NONE },
      },
      rows: [
        new TableRow({
          tableHeader: true,
          children: encabezados.map((texto, i) => celda(texto, {
            ancho: escalados[i], bordeArriba: true, bordeAbajo: true,
            alineacion: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
          })),
        }),
        ...filas.map((fila, indice) => new TableRow({
          children: fila.map((texto, i) => celda(String(texto), {
            ancho: escalados[i],
            bordeAbajo: indice === filas.length - 1,
            alineacion: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
          })),
        })),
      ],
    }),
  ];

  if (nota) {
    elementos.push(new Paragraph({
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 60, after: 240 },
      children: [
        new TextRun({ text: 'Nota.', font: FUENTE, size: TAM, italics: true, color: NEGRO }),
        new TextRun({ text: ` ${nota}`, font: FUENTE, size: TAM, color: NEGRO }),
      ],
    }));
  }
  return elementos;
}

// --- portada APA 7 para trabajo de estudiante -------------------------------

function portada() {
  const centrado = (texto, negrita = false) => new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
    children: [new TextRun({
      text: texto, font: FUENTE, size: TAM, bold: negrita, color: NEGRO,
    })],
  });
  const vacio = () => centrado('');

  return [
    // APA 7 coloca el titulo tres o cuatro lineas debajo del margen superior.
    vacio(), vacio(), vacio(),
    centrado('Sistema de Pronóstico de Puntos de Inflexión en el Precio de', true),
    centrado('Litecoin (LTC) mediante Análisis Multivariante de Series Temporales', true),
    vacio(),
    centrado('Marco Teórico: Series de Tiempo y Criptoactivos'),
    vacio(), vacio(),
    centrado('Alejandro Zamora, Fabrizio Espinoza Arce, Isaac Morun'),
    centrado('y Jose Pablo Monestel'),
    vacio(),
    // La afiliacion institucional no se inventa: APA 7 pide departamento y
    // universidad, y ese dato lo completa el equipo.
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
      children: [new TextRun({
        text: '[COMPLETAR — Escuela o Departamento, Universidad]',
        font: FUENTE, size: TAM, color: GRIS, italics: true,
      })],
    }),
    centrado('Señales y Sistemas'),
    centrado('Prof. Roberto Calvo Arias'),
    centrado('18 de agosto de 2026'),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// --- cuerpo -----------------------------------------------------------------

const cuerpo = [];
const agregar = (...elementos) => elementos.flat().forEach((e) => cuerpo.push(e));

// Tabla de contenido
agregar(
  titulo1('Tabla de Contenido'),
  new TableOfContents('Contenido', { hyperlink: true, headingStyleRange: '1-2' }),
  new Paragraph({ children: [new PageBreak()] }),
);

// APA 7: la primera pagina del cuerpo repite el titulo y no lleva encabezado
// "Introduccion"; el titulo cumple esa funcion.
agregar(
  titulo1('Sistema de Pronóstico de Puntos de Inflexión en el Precio de Litecoin'),
  p('El presente documento constituye el marco teórico del Caso N.º 1, correspondiente a la primera entrega del proyecto. Su propósito es establecer los fundamentos conceptuales sobre series de tiempo y criptoactivos que sustentan el desarrollo posterior de un modelo de aprendizaje automático supervisado para el pronóstico de puntos de inflexión en el precio de Litecoin.'),
  pendiente('Ampliar la introducción: contexto del problema, objetivo del documento y estructura de las secciones que siguen. Entre dos y tres párrafos.'),
);

// --- Metodo de obtencion de datos
agregar(
  titulo1('Datos Utilizados'),
  p(`Los conceptos expuestos en este marco teórico se ilustran con datos reales de las seis criptomonedas contempladas en el proyecto. La información procede de la interfaz pública de programación de Binance y comprende ${medido.serie.n.toLocaleString('es-CR')} observaciones diarias del precio de cierre, entre el ${fechaLarga(medido.serie.desde)} y el ${fechaLarga(medido.serie.hasta)}.`),
  p('La ventana común a las seis series se encuentra limitada por Solana, cuya cotización se inicia en la fecha indicada. Los períodos anteriores se descartan, dado que un modelo multivariante no puede aprender de observaciones incompletas. Debe señalarse que los precios corresponden a un único mercado y no a un promedio ponderado de la industria.'),
  p('Adicionalmente, y siguiendo la indicación del profesor, varios conceptos se ilustran mediante series construidas de manera sintética, en las cuales la volatilidad y la correlación se fijan de antemano. Estas series permiten verificar que los métodos empleados detectan aquello que declaran detectar, antes de aplicarlos sobre datos en los que la respuesta correcta se desconoce. Las series construidas se identifican explícitamente como tales en cada figura.'),
);

// ===================== SERIES DE TIEMPO =====================
agregar(titulo1('Marco Teórico: Series de Tiempo'));

agregar(
  titulo2('Definición de Serie Temporal'),
  pendiente('Definir serie temporal, señalar que el orden de las observaciones es parte de la información y que las observaciones no son independientes entre sí. Vincular con la Figura 1.'),
  figura(1, 'Precio de cierre diario de Litecoin',
    'mt-01-serie-temporal.png',
    `Serie de ${medido.serie.n.toLocaleString('es-CR')} observaciones diarias del precio de cierre de LTC entre el ${fechaLarga(medido.serie.desde)} y el ${fechaLarga(medido.serie.hasta)}. Elaboración propia a partir de datos de Binance.`),
);

agregar(
  titulo2('Componentes de una Serie Temporal'),
  pendiente('Explicar tendencia, estacionalidad, ciclo y componente irregular. Analizar el dato medido: la estacionalidad semanal representa apenas el 0,426 % de la variación total, lo cual es coherente con un mercado que opera de forma ininterrumpida y carece de efecto de fin de semana.'),
  figura(2, 'Descomposición aditiva de la serie de Litecoin',
    'mt-02-componentes.png',
    `Descomposición en tendencia, estacionalidad de período semanal y residuo. El componente estacional representa el ${nf(medido.componentes.peso_estacional_relativo_pct)} % de la desviación total de la serie. Elaboración propia.`),
);

agregar(
  titulo2('Estacionariedad'),
  pendiente('Definir estacionariedad en sentido débil: media, varianza y autocovarianza constantes en el tiempo. Explicar la prueba de Dickey-Fuller aumentada y su hipótesis nula. Advertencia de redacción: no rechazar la hipótesis nula no demuestra que la serie carezca de estacionariedad, sino que no existe evidencia suficiente en contra.'),
  tabla(1, 'Resultados de la prueba de Dickey-Fuller aumentada',
    ['Criptomoneda', 'p-valor en nivel', 'p-valor en retornos', 'Rechaza en nivel'],
    Object.keys(medido.estacionariedad.nivel).map((activo) => [
      activo,
      nf(medido.estacionariedad.nivel[activo].p_valor),
      medido.estacionariedad.retornos[activo].p_valor < 0.001
        ? '< 0,001' : nf(medido.estacionariedad.retornos[activo].p_valor),
      medido.estacionariedad.nivel[activo].rechaza ? 'Sí' : 'No',
    ]),
    [30, 24, 24, 22],
    'La hipótesis nula de la prueba establece la presencia de una raíz unitaria, es decir, ausencia de estacionariedad. Ninguna de las seis series rechaza dicha hipótesis en nivel; las seis la rechazan al trabajar sobre retornos. Elaboración propia.'),
  figura(3, 'Comparación de p-valores en nivel y en retornos',
    'mt-03-estacionariedad.png',
    'La escala vertical es logarítmica, dado que los p-valores obtenidos sobre retornos se encuentran varios órdenes de magnitud por debajo del umbral de significancia. La línea discontinua señala el umbral de 0,05. Elaboración propia.'),
  pendiente('Comentar el caso de Ethereum, cuyo p-valor en nivel es 0,059 y se sitúa apenas por encima del umbral. Señalar que se trata de un resultado limítrofe y que ello ilustra la dependencia de la prueba respecto del período observado.'),
);

agregar(
  titulo2('No Estacionariedad'),
  pendiente('Explicar por qué los precios en nivel no son estacionarios: presentan tendencia y su varianza crece con el nivel. Exponer las consecuencias para el modelado y justificar la transformación a retornos. Concluir con la decisión que de ello se deriva: las características del modelo se construyen sobre retornos y no sobre precios en nivel.'),
);

agregar(
  titulo2('Heterocedasticidad'),
  pendiente('Definir homocedasticidad y heterocedasticidad. Utilizar la Figura 4 para mostrar el contraste sobre series de respuesta conocida y explicar por qué esta propiedad invalida los supuestos de los modelos ARIMA.'),
  figura(4, 'Contraste entre volatilidad constante y volatilidad por tramos',
    'mt-05-heterocedasticidad.png',
    `Ambas series fueron construidas por los autores y no corresponden a datos de mercado. En la serie superior la volatilidad se fijó constante y el cociente entre tramos resultó de ${nf(medido.heterocedasticidad_construida.cociente_sin_regimenes, 2)}; en la inferior se multiplicó por cinco en tramos alternos y dicho cociente ascendió a ${nf(medido.heterocedasticidad_construida.cociente_con_regimenes, 2)}. Elaboración propia.`),
);

agregar(
  titulo2('Volatilidad'),
  pendiente('Definir la volatilidad y su estimación mediante desviación estándar móvil de los retornos. Desarrollar el argumento sobre el cociente medido, que constituye evidencia directa de heterocedasticidad en datos reales.'),
  figura(5, 'Precio de cierre de Litecoin y su volatilidad móvil',
    'mt-04-volatilidad.png',
    `Volatilidad estimada mediante desviación estándar móvil de los retornos sobre una ventana de ${medido.volatilidad.ventana} observaciones. La volatilidad del tramo más agitado equivale a ${nf(medido.volatilidad.cociente_agitado_tranquilo, 1)} veces la del tramo más estable. Elaboración propia.`),
);

agregar(
  titulo2('Autocorrelación'),
  pendiente('Definir la función de autocorrelación. Analizar los dos hallazgos de la Figura 6: en nivel la autocorrelación es prácticamente unitaria y decae con lentitud, lo cual confirma la ausencia de estacionariedad; en retornos resulta próxima a cero. Desarrollar la implicación: la ausencia de autocorrelación lineal significativa en los retornos constituye un argumento medido a favor del empleo de modelos no lineales y multivariantes.'),
  figura(6, 'Función de autocorrelación de Litecoin en nivel y en retornos',
    'mt-06-autocorrelacion.png',
    `La autocorrelación en el primer rezago alcanza ${nf(medido.autocorrelacion.acf_nivel_rezago_1)} sobre precios en nivel y ${nf(medido.autocorrelacion.acf_retornos_rezago_1)} sobre retornos. Únicamente ${medido.autocorrelacion.cuantos_significativos} rezagos de los retornos exceden la banda de confianza del 95 %. Elaboración propia.`),
);

agregar(
  titulo2('Correlación Cruzada'),
  pendiente('Definir la correlación cruzada y distinguirla de la autocorrelación. Desarrollar el contraste entre el cálculo sobre niveles y sobre retornos, que constituye el punto de análisis principal de esta sección. Concluir señalando que las correlaciones observadas justifican el planteamiento multivariante del problema.'),
  tabla(2, 'Correlación entre pares de criptomonedas según la variable empleada',
    ['Comparación', 'Sobre precios en nivel', 'Sobre retornos'],
    [
      ['LTC – BTC', nf(medido.correlacion.inestabilidad_en_nivel.LTC_BTC_nivel),
        nf(medido.correlacion.inestabilidad_en_nivel.LTC_BTC_retornos)],
      ['LTC – ADA', nf(medido.correlacion.inestabilidad_en_nivel.LTC_ADA_nivel),
        nf(medido.correlacion.inestabilidad_en_nivel.LTC_ADA_retornos)],
      ['Rango de todos los pares',
        `${nf(medido.correlacion.inestabilidad_en_nivel.rango_nivel[0])} – ${nf(medido.correlacion.inestabilidad_en_nivel.rango_nivel[1])}`,
        `${nf(medido.correlacion.inestabilidad_en_nivel.rango_retornos[0])} – ${nf(medido.correlacion.inestabilidad_en_nivel.rango_retornos[1])}`],
    ],
    [34, 33, 33],
    'El cálculo sobre precios en nivel produce un ordenamiento económicamente implausible, al atribuir a Litecoin una relación casi nula con Bitcoin y una relación fuerte con Cardano. Sobre retornos el rango se reduce a la mitad y el ordenamiento resulta coherente con la estructura del mercado. Elaboración propia.'),
  figura(7, 'Matrices de correlación de series construidas y de datos reales',
    'mt-07-correlacion.png',
    `Los dos primeros paneles corresponden a series construidas por los autores, generadas con correlación objetivo de 0,10 y 0,90; las correlaciones medidas resultaron de ${nf(medido.correlacion.control_construido_baja)} y ${nf(medido.correlacion.control_construido_alta)}, respectivamente. El tercer panel corresponde a los retornos reales de las seis criptomonedas. Elaboración propia.`),
);

// ===================== CRIPTOACTIVOS =====================
agregar(titulo1('Marco Teórico: Criptoactivos y sus Características'));

[
  ['Definición de Criptoactivo',
    'Definir el concepto de criptoactivo, distinguirlo de un activo financiero tradicional y explicar el papel del registro distribuido.'],
  ['Características Principales',
    'Exponer descentralización, disponibilidad continua, divisibilidad y transparencia del registro. Vincular la operación ininterrumpida del mercado con la ausencia de estacionalidad semanal documentada en la sección anterior.'],
  ['Principales Tipos',
    'Clasificar los criptoactivos y ubicar las seis criptomonedas del estudio dentro de dicha clasificación.'],
  ['Mercado Cripto',
    'Describir la estructura del mercado, el papel de los mercados centralizados, la capitalización y la liquidez.'],
  ['Factores que Afectan el Precio',
    'Exponer los factores de oferta y demanda, los eventos de reducción de emisión, el entorno regulatorio, el sentimiento y el contagio entre activos.'],
].forEach(([encabezado, instruccion]) => agregar(titulo2(encabezado), pendiente(instruccion)));

agregar(
  titulo2('Correlación y Dependencia entre Activos'),
  pendiente('Desarrollar la interpretación económica de las correlaciones presentadas en la Tabla 2 y la Figura 7. Explicar por qué resulta esperable que Ethereum y Bitcoin presenten la mayor correlación con Litecoin, y analizar las implicaciones de un mercado con correlaciones elevadas en términos de diversificación y contagio.'),
  tabla(3, 'Correlación de los retornos de las criptomonedas de apoyo con Litecoin',
    ['Criptomoneda', 'Correlación con LTC'],
    [
      [medido.correlacion.mayor_con_ltc.activo, nf(medido.correlacion.mayor_con_ltc.valor)],
      [medido.correlacion.menor_con_ltc.activo, nf(medido.correlacion.menor_con_ltc.valor)],
    ],
    [50, 50],
    'Se presentan los valores extremos. La matriz completa figura en la Figura 7. Elaboración propia.'),
);

agregar(
  titulo2('Definición de Punto de Inflexión'),
  pendiente('Establecer que un máximo local no existe en términos absolutos, sino en relación con una ventana de observación. Incluir la propiedad aritmética demostrable: dos máximos no pueden situarse a menos de w+1 observaciones de distancia, de lo cual se deriva que a lo sumo una de cada w+1 observaciones puede clasificarse como máximo.'),
  figura(8, 'Serie construida con puntos de inflexión conocidos',
    'mt-08a-giros-construidos.png',
    `Serie construida por los autores. Los puntos marcados corresponden exactamente a los vértices establecidos durante su generación. El detector identificó ${medido.puntos_inflexion.construida_giros_detectados} de ${medido.puntos_inflexion.construida_giros_puestos} vértices, sin falsos positivos. Elaboración propia.`),
);

agregar(
  titulo2('Encontrar Puntos de Inflexión'),
  pendiente('Contrastar dos enfoques: el análisis de estructura de mercado mediante máximos y mínimos sucesivos, y el criterio automático de ventana empleado en este proyecto. Señalar la limitación inherente: determinar si una observación constituye un máximo exige observar las w posteriores, de modo que la etiqueta se conoce con retraso.'),
  figura(9, 'Puntos de inflexión detectados en la serie real de Litecoin',
    'mt-08b-giros-ltc.png',
    `Últimas 250 observaciones de la serie de LTC, con los puntos de inflexión identificados mediante el criterio de ventana con w = ${medido.puntos_inflexion.w}. Elaboración propia.`),
);

agregar(
  titulo2('Métricas de Evaluación para Puntos de Inflexión'),
  pendiente('Explicar por qué el desbalance de clases es estructural y no accidental, y por qué invalida la exactitud como medida de calidad.'),
  figura(10, 'Distribución de las clases en la serie de Litecoin',
    'mt-09a-balance-clases.png',
    `Distribución obtenida con w = ${medido.puntos_inflexion.w} sobre observaciones diarias. Elaboración propia.`),
  pendiente('Desarrollar el argumento central de esta sección a partir de la Tabla 4: un modelo que no detecta ningún punto de inflexión alcanza una exactitud del 86,9 %. Explicar cómo el F1 macro y la precisión direccional revelan dicha limitación.'),
  tabla(4, 'Desempeño del modelo de referencia trivial',
    ['Métrica', 'Valor obtenido'],
    [
      ['Exactitud', nf(medido.metricas.baseline_trivial.exactitud)],
      ['F1 macro', nf(medido.metricas.baseline_trivial.f1_macro)],
      ['Precisión direccional', nf(medido.metricas.baseline_trivial.precision_direccional)],
      ['Observaciones evaluadas', medido.metricas.baseline_trivial.n.toLocaleString('es-CR')],
    ],
    [55, 45],
    `El modelo de referencia trivial responde siempre la clase de continuidad y, por construcción, no detecta ningún punto de inflexión. Valores obtenidos con w = ${medido.puntos_inflexion.w} sobre observaciones diarias. Elaboración propia.`),
  figura(11, 'Matriz de confusión del modelo de referencia trivial',
    'mt-09b-confusion-baseline.png',
    'La totalidad de las predicciones se concentra en la clase de continuidad, de modo que ningún máximo ni mínimo resulta identificado. Elaboración propia.'),
  pendiente('Definir y justificar cada métrica empleada: F1 por clase, F1 macro frente a F1 ponderado, precisión direccional y matriz de confusión. Declarar explícitamente que la definición de precisión direccional adoptada es propia, dado que el enunciado no precisa su interpretación en un problema de clasificación multiclase.'),
);

// --- Referencias -------------------------------------------------------------
agregar(
  new Paragraph({ children: [new PageBreak()] }),
  titulo1('Referencias'),
  new Paragraph({
    spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
    indent: { left: SANGRIA, hanging: SANGRIA },
    children: [new TextRun({
      text: '[PENDIENTE DE REDACCION — Incorporar las referencias en formato APA 7, ordenadas alfabéticamente y con sangría francesa de media pulgada. Se requiere al menos una fuente académica por concepto principal. El formato de este párrafo ya corresponde al exigido: basta con reemplazar el texto.]',
      font: FUENTE, size: TAM, color: GRIS, italics: true,
    })],
  }),
);

// --- documento ---------------------------------------------------------------

const documento = new Document({
  creator: 'Equipo Caso N.º 1',
  title: 'Marco Teórico — Series de Tiempo y Criptoactivos',
  description: 'Primera entrega del Caso N.º 1, Señales y Sistemas',
  features: { updateFields: true },
  styles: {
    default: {
      document: {
        run: { font: FUENTE, size: TAM, color: NEGRO },
        paragraph: { spacing: { line: DOBLE, lineRule: LineRuleType.AUTO } },
      },
      // Los niveles se declaran para que la tabla de contenido los recoja; el
      // formato visual se aplica en cada parrafo.
      heading1: {
        run: { font: FUENTE, size: TAM, bold: true, color: NEGRO },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { line: DOBLE, before: 0, after: 0 } },
      },
      heading2: {
        run: { font: FUENTE, size: TAM, bold: true, color: NEGRO },
        paragraph: { spacing: { line: DOBLE, before: 0, after: 0 } },
      },
      heading3: {
        run: { font: FUENTE, size: TAM, bold: true, italics: true, color: NEGRO },
        paragraph: { spacing: { line: DOBLE, before: 0, after: 0 } },
      },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 720, footer: 720 },
      },
    },
    // APA 7 para trabajos de estudiante: numero de pagina arriba a la derecha en
    // todas las paginas, incluida la portada. Sin encabezado de titulo abreviado.
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          spacing: { after: 0 },
          children: [new TextRun({
            children: [PageNumber.CURRENT], font: FUENTE, size: TAM, color: NEGRO,
          })],
        })],
      }),
    },
    children: [...portada(), ...cuerpo],
  }],
});

const destino = process.argv[2]
  || path.join(RAIZ, 'docs', 'entregas', 'semana-1', 'Marco teorico - Semana 1 (base).docx');

Packer.toBuffer(documento).then((buffer) => {
  fs.writeFileSync(destino, buffer);
  const pendientes = cuerpo.filter((e) => JSON.stringify(e).includes('PENDIENTE')).length;
  console.log(`escrito: ${path.relative(RAIZ, destino)}`);
  console.log(`  ${Math.round(buffer.length / 1024)} KiB · ${pendientes} bloques pendientes de redaccion`);
});
