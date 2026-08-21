// Ensambla el documento de la Semana 1 en Word a partir de los markdown de cada
// modulo, con formato APA 7.
//
// Es el trabajo del PM hecho codigo: unir las secciones, renumerar figuras y
// tablas de corrido, y producir el entregable. Hacerlo a mano significa repetir
// media hora de copiar, pegar y renumerar cada semana, y equivocarse una vez.
//
// Lo que hace y no es obvio:
//
// - Renumera figuras y tablas de forma continua entre archivos, y reescribe las
//   menciones del texto. Cada modulo numera desde 1 en su archivo; al unir, la
//   Figura 1 de metricas pasa a ser la 10 y toda mencion a "la Figura 1" en ese
//   archivo tiene que seguirla.
// - Reordena a la forma APA: en markdown la imagen va antes del pie y la tabla
//   antes de su titulo; APA pide numero y titulo ARRIBA en los dos casos.
// - Funde las referencias de los tres archivos, quita duplicados y ordena.
// - Descarta las notas internas de coordinacion, que no van en la entrega, y
//   convierte los bloques sin redactar en avisos visibles en gris.
//
// Uso:
//   npm run ensamblar --prefix scripts

const { Document, Packer, Paragraph, TableOfContents, AlignmentType, TextRun,
  LineRuleType } = require('docx');
const fs = require('fs');
const path = require('path');
const apa = require('./apa');

const RAIZ = path.resolve(__dirname, '..');
// La carpeta de origen es un parametro para poder construir una variante del
// entregable sin tocar la vigente. Sin esto, comparar dos redacciones obliga a
// sobrescribir la version buena, y a las horas de entregar eso no se hace.
const ENTREGA = path.join(RAIZ, 'docs', 'entregas', process.env.CARPETA_ENTREGA || 'semana-1');

// Que archivos entran, en que orden y con que titulo de capitulo. Cada entrega lo
// declara en su propio secciones.json, porque el orden es el del enunciado de esa
// semana y cambia de una a otra.
//
// Sin el manifiesto el guion servia para una sola entrega y habia que editarlo cada
// semana, que es justo la clase de paso manual que se olvida.
function manifiesto() {
  const ruta = path.join(ENTREGA, 'secciones.json');
  if (!fs.existsSync(ruta)) {
    throw new Error(
      `falta ${path.relative(RAIZ, ruta)}. Declara ahi que archivos entran, en que `
      + 'orden y con que titulo de capitulo. Ver docs/entregas/semana-1/secciones.json.',
    );
  }
  const leido = JSON.parse(fs.readFileSync(ruta, 'utf8'));
  for (const clave of ['introduccion', 'conclusion', 'capitulos']) {
    if (!(clave in leido)) throw new Error(`${path.relative(RAIZ, ruta)} no declara "${clave}"`);
  }
  return leido;
}

// Dos clases de bloque de cita que no son contenido, y se tratan distinto.
//
// Las notas de coordinacion entre nosotros se descartan en silencio: no van en la
// entrega y su presencia no significa que falte nada.
const NOTA_INTERNA = /Nota para el ensamblaje|Este archivo es un esqueleto/i;
// Los bloques sin redactar si se avisan y se emiten en gris, porque su presencia
// significa que el documento no esta listo.
// El limite de palabra en PENDIENTE evita que "independiente" o "codependiente"
// —terminos que aparecen de forma natural en el texto— marquen como incompleta
// una cita que si esta redactada.
const SIN_REDACTAR = /ESCRIB[IÍ] AC[AÁ]|\bPENDIENTE\b/i;

// ---------------------------------------------------------------------------
// Analisis del markdown

function tokenizar(texto) {
  const lineas = texto.split(/\r?\n/);
  const bloques = [];
  let i = 0;

  while (i < lineas.length) {
    const linea = lineas[i];

    if (!linea.trim()) { i += 1; continue; }
    if (/^---+$/.test(linea.trim())) { i += 1; continue; }

    const encabezado = linea.match(/^(#{1,4})\s+(.*)$/);
    if (encabezado) {
      bloques.push({ tipo: 'titulo', nivel: encabezado[1].length, texto: encabezado[2].trim() });
      i += 1; continue;
    }

    const imagen = linea.match(/^!\[[^\]]*\]\(([^)]+)\)/);
    if (imagen) {
      bloques.push({ tipo: 'imagen', ruta: imagen[1] });
      i += 1; continue;
    }

    const pie = linea.match(/^\*\*(Figura|Tabla)\s+(\d+)\.?\*\*\s*(.*)$/);
    if (pie) {
      let resto = pie[3];
      while (i + 1 < lineas.length && lineas[i + 1].trim()
             && !/^[#|>!]/.test(lineas[i + 1]) && !/^\*\*(Figura|Tabla)\s/.test(lineas[i + 1])) {
        i += 1; resto += ` ${lineas[i].trim()}`;
      }
      bloques.push({ tipo: 'pie', clase: pie[1], numero: Number(pie[2]), texto: resto.trim() });
      i += 1; continue;
    }

    if (linea.startsWith('|')) {
      const filas = [];
      while (i < lineas.length && lineas[i].startsWith('|')) {
        filas.push(lineas[i].split('|').slice(1, -1).map((c) => c.trim()));
        i += 1;
      }
      const cuerpo = filas.filter((f) => !f.every((c) => /^:?-+:?$/.test(c) || !c));
      bloques.push({ tipo: 'tabla', encabezados: cuerpo[0], filas: cuerpo.slice(1) });
      continue;
    }

    if (linea.startsWith('>')) {
      const cita = [];
      while (i < lineas.length && (lineas[i].startsWith('>') || (cita.length && !lineas[i].trim()))) {
        if (!lineas[i].trim()) { i += 1; break; }
        cita.push(lineas[i].replace(/^>\s?/, ''));
        i += 1;
      }
      bloques.push({ tipo: 'cita', texto: cita.join(' ').trim() });
      continue;
    }

    if (/^[-*]\s+/.test(linea)) {
      const puntos = [];
      while (i < lineas.length && /^[-*]\s+/.test(lineas[i])) {
        let punto = lineas[i].replace(/^[-*]\s+/, '');
        i += 1;
        while (i < lineas.length && /^\s{2,}\S/.test(lineas[i])) {
          punto += ` ${lineas[i].trim()}`; i += 1;
        }
        puntos.push(punto);
      }
      bloques.push({ tipo: 'lista', puntos });
      continue;
    }

    const parrafo = [linea.trim()];
    i += 1;
    while (i < lineas.length && lineas[i].trim() && !/^[#|>!-]/.test(lineas[i])
           && !/^\*\*(Figura|Tabla)\s/.test(lineas[i])) {
      parrafo.push(lineas[i].trim()); i += 1;
    }
    bloques.push({ tipo: 'parrafo', texto: parrafo.join(' ') });
  }
  return bloques;
}

/** Separa el cuerpo de la seccion de referencias. */
function partir(bloques) {
  const corte = bloques.findIndex(
    (b) => b.tipo === 'titulo' && /^referencias$/i.test(b.texto.trim()),
  );
  if (corte === -1) return { cuerpo: bloques, referencias: [] };
  return {
    cuerpo: bloques.slice(0, corte),
    referencias: bloques.slice(corte + 1)
      .filter((b) => b.tipo === 'parrafo' || b.tipo === 'lista')
      .flatMap((b) => (b.tipo === 'lista' ? b.puntos : [b.texto])),
  };
}

// ---------------------------------------------------------------------------
// Renumeracion continua

function renumerar(documentos) {
  let figura = 0;
  let tablaNum = 0;
  for (const doc of documentos) {
    doc.mapa = { Figura: {}, Tabla: {} };
    for (const bloque of doc.cuerpo) {
      if (bloque.tipo !== 'pie') continue;
      if (bloque.clase === 'Figura') doc.mapa.Figura[bloque.numero] = ++figura;
      else doc.mapa.Tabla[bloque.numero] = ++tablaNum;
    }
  }
  // Reescribe las menciones del texto para que sigan al pie renumerado.
  for (const doc of documentos) {
    const traducir = (texto) => texto.replace(
      /\b(Figura|Tabla)(s)?\s+(\d+)\b/g,
      (todo, clase, plural, numero) => {
        const nuevo = doc.mapa[clase][Number(numero)];
        return nuevo ? `${clase}${plural || ''} ${nuevo}` : todo;
      },
    );
    for (const bloque of doc.cuerpo) {
      if (bloque.tipo === 'parrafo' || bloque.tipo === 'cita') bloque.texto = traducir(bloque.texto);
      else if (bloque.tipo === 'lista') bloque.puntos = bloque.puntos.map(traducir);
      else if (bloque.tipo === 'pie') {
        bloque.texto = traducir(bloque.texto);
        bloque.global = doc.mapa[bloque.clase][bloque.numero];
      } else if (bloque.tipo === 'tabla') {
        bloque.encabezados = bloque.encabezados.map(traducir);
        bloque.filas = bloque.filas.map((f) => f.map(traducir));
      }
    }
  }
  return { figuras: figura, tablas: tablaNum };
}

// ---------------------------------------------------------------------------
// Emision

/** El pie del markdown trae titulo y fuente juntos; APA los separa. */
function partirPie(texto) {
  const corte = texto.search(/\b(Fuente|Elaboración propia|Nota)\b/);
  if (corte <= 0) return { titulo: texto, nota: null };
  return { titulo: texto.slice(0, corte).replace(/[.\s]+$/, ''), nota: texto.slice(corte).trim() };
}

function emitir(doc, carpeta, avisos) {
  const salida = [];
  let imagenPendiente = null;
  let tablaPendiente = null;

  for (const bloque of doc.cuerpo) {
    switch (bloque.tipo) {
      case 'titulo':
        // El titulo de nivel 1 de cada archivo se descarta: el documento emite el
        // suyo desde TITULOS y repetirlo partiria la jerarquia APA.
        //
        // Los niveles se conservan tal cual en vez de subirlos uno: si `##` se
        // emitiera como nivel 1, cada seccion quedaria centrada y en negrita igual
        // que el titulo del capitulo que la contiene, y el lector no tendria como
        // saber que "la seccion 3" se refiere a la de este capitulo y no a la
        // homonima de otro. APA 7 distingue nivel 1 centrado, nivel 2 al margen y
        // nivel 3 al margen en cursiva, y esa jerarquia es la que hay que mostrar.
        if (bloque.nivel > 1) salida.push(apa.titulo(Math.min(bloque.nivel, 3), bloque.texto));
        break;

      case 'imagen':
        imagenPendiente = path.resolve(carpeta, bloque.ruta);
        break;

      case 'tabla':
        tablaPendiente = bloque;
        break;

      case 'pie': {
        const { titulo, nota } = partirPie(bloque.texto);
        if (bloque.clase === 'Figura' && imagenPendiente) {
          salida.push(...apa.figura(bloque.global, titulo, imagenPendiente, nota));
          imagenPendiente = null;
        } else if (bloque.clase === 'Tabla' && tablaPendiente) {
          salida.push(...apa.tabla(
            bloque.global, titulo, tablaPendiente.encabezados, tablaPendiente.filas, nota,
          ));
          tablaPendiente = null;
        }
        break;
      }

      case 'cita':
        if (NOTA_INTERNA.test(bloque.texto)) break;
        if (SIN_REDACTAR.test(bloque.texto)) {
          avisos.push({ seccion: doc.nombre, texto: bloque.texto.slice(0, 78) });
          salida.push(apa.aviso(`[PENDIENTE DE REDACCION — ${bloque.texto.slice(0, 220)}]`));
        } else {
          salida.push(apa.citaEnBloque(bloque.texto));
        }
        break;

      case 'lista':
        for (const punto of bloque.puntos) {
          salida.push(apa.parrafo(`• ${punto}`, { sinSangria: true, indent: { left: apa.SANGRIA } }));
        }
        break;

      default:
        salida.push(apa.parrafo(bloque.texto));
    }
    // Una tabla sin pie se emite igual, para no perderla.
    if (tablaPendiente && bloque.tipo === 'tabla') continue;
  }

  if (tablaPendiente) {
    salida.push(...apa.tabla('—', 'Tabla sin pie en el original',
      tablaPendiente.encabezados, tablaPendiente.filas, null));
  }
  return salida;
}

function portada() {
  const centrado = (texto, negrita = false, gris = false) => new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { line: apa.DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
    children: [new TextRun({
      text: texto, font: apa.FUENTE, size: apa.TAM,
      bold: negrita, italics: gris, color: gris ? apa.GRIS : apa.NEGRO,
    })],
  });
  const vacio = () => centrado('');
  return [
    vacio(), vacio(), vacio(),
    centrado('Sistema de Pronóstico de Puntos de Inflexión en el Precio de', true),
    centrado('Litecoin (LTC) mediante Análisis Multivariante de Series Temporales', true),
    vacio(),
    centrado('Marco Teórico: Series de Tiempo y Criptoactivos'),
    vacio(), vacio(),
    centrado('Alejandro Zamora, Fabrizio Espinoza Arce, Isaac Morun'),
    centrado('y Jose Pablo Monestel'),
    vacio(),
    // APA 7 pide la afiliacion como "programa o departamento, institucion".
    centrado('Tecnologías de la Información y Comunicación Empresarial,'),
    centrado('Universidad Invenio'),
    centrado('Señales y Sistemas'),
    centrado('Prof. Roberto Calvo Arias'),
    centrado('18 de agosto de 2026'),
    new Paragraph({ children: [new apa.PageBreak()] }),
  ];
}

/**
 * Introduccion y conclusiones: no llevan figuras, tablas ni referencias, asi que
 * no pasan por `partir` ni por la renumeracion. Se descarta su titulo de nivel 1
 * porque quien llama decide con que encabezado entran.
 */
function seccionSuelta(nombre) {
  const ruta = path.join(ENTREGA, nombre);
  if (!fs.existsSync(ruta)) return [];
  const bloques = tokenizar(fs.readFileSync(ruta, 'utf8'));
  return bloques.filter((b) => !(b.tipo === 'titulo' && b.nivel === 1));
}

/**
 * La introduccion y las conclusiones no llevan figuras ni tablas, asi que no pasan
 * por la renumeracion. Pero SI pueden tener bloques sin redactar, y hasta ahora
 * este camino los descartaba en silencio: no aparecian en el documento ni en el
 * recuento, de modo que el guion anunciaba "sin bloques pendientes" con las
 * conclusiones todavia en esqueleto. Casi se entrega asi.
 */
function emitirSuelta(nombre, cuerpo, avisos) {
  for (const bloque of seccionSuelta(nombre)) {
    if (bloque.tipo === 'titulo') cuerpo.push(apa.titulo(Math.min(bloque.nivel, 3), bloque.texto));
    else if (bloque.tipo === 'parrafo') cuerpo.push(apa.parrafo(bloque.texto));
    else if (bloque.tipo === 'lista') {
      for (const p of bloque.puntos) {
        cuerpo.push(apa.parrafo(`• ${p}`, { sinSangria: true, indent: { left: apa.SANGRIA } }));
      }
    } else if (bloque.tipo === 'cita') {
      if (NOTA_INTERNA.test(bloque.texto)) continue;
      if (SIN_REDACTAR.test(bloque.texto)) {
        avisos.push({ seccion: nombre, texto: bloque.texto.slice(0, 78) });
        cuerpo.push(apa.aviso(`[PENDIENTE DE REDACCION — ${bloque.texto.slice(0, 220)}]`));
      } else {
        cuerpo.push(apa.citaEnBloque(bloque.texto));
      }
    }
  }
}

function main() {
  const avisos = [];
  const plan = manifiesto();
  const documentos = plan.capitulos.map(({ archivo: nombre }) => {
    const ruta = path.join(ENTREGA, nombre);
    if (!fs.existsSync(ruta)) throw new Error(`falta ${ruta}`);
    const partes = partir(tokenizar(fs.readFileSync(ruta, 'utf8')));
    return { nombre, ...partes };
  });

  const conteo = renumerar(documentos);

  const cuerpo = [];
  // El rotulo del indice se emite como parrafo centrado en negrita y no como
  // encabezado: con estilo Heading el propio indice se listaria a si mismo en
  // su primera entrada. Visualmente es identico a un titulo de nivel 1.
  cuerpo.push(apa.parrafo('**Tabla de Contenido**', {
    sinSangria: true, alineacion: AlignmentType.CENTER, keepNext: true,
  }));
  // 1-3 porque las secciones bajaron a nivel 2 y las subsecciones a nivel 3;
  // con el rango anterior la tabla de contenido habria perdido las subsecciones.
  cuerpo.push(new TableOfContents('Contenido', { hyperlink: true, headingStyleRange: '1-3' }));
  cuerpo.push(new Paragraph({ children: [new apa.PageBreak()] }));

  // APA 7: la primera pagina del cuerpo repite el titulo y la introduccion no
  // lleva encabezado propio.
  cuerpo.push(apa.titulo(1, 'Sistema de Pronóstico de Puntos de Inflexión en el Precio de Litecoin'));
  emitirSuelta(plan.introduccion, cuerpo, avisos);

  const titulos = Object.fromEntries(plan.capitulos.map((c) => [c.archivo, c.titulo]));
  for (const doc of documentos) {
    cuerpo.push(apa.titulo(1, titulos[doc.nombre]));
    cuerpo.push(...emitir(doc, ENTREGA, avisos));
  }

  // A diferencia de la introduccion, que en APA 7 va bajo el titulo del trabajo,
  // las conclusiones si llevan encabezado propio. Sin el, los cuatro parrafos
  // quedaban colgando de la ultima seccion de metricas.
  cuerpo.push(apa.titulo(1, 'Conclusiones'));
  emitirSuelta(plan.conclusion, cuerpo, avisos);

  // Referencias de los tres archivos, sin duplicados y ordenadas por apellido.
  const vistas = new Map();
  for (const doc of documentos) {
    for (const texto of doc.referencias) {
      const limpio = texto.replace(/\s+/g, ' ').trim();
      if (!limpio || limpio.length < 25) continue;
      const clave = limpio.replace(/[*_`]/g, '').slice(0, 60).toLowerCase();
      if (!vistas.has(clave)) vistas.set(clave, limpio);
    }
  }
  const referencias = [...vistas.values()].sort((a, b) =>
    a.replace(/[*_`]/g, '').localeCompare(b.replace(/[*_`]/g, ''), 'es'));

  cuerpo.push(new Paragraph({ children: [new apa.PageBreak()] }));
  cuerpo.push(apa.titulo(1, 'Referencias'));
  if (referencias.length) referencias.forEach((r) => cuerpo.push(apa.referencia(r)));
  else cuerpo.push(apa.aviso('[PENDIENTE — no se encontraron referencias en las secciones.]'));

  const documento = new Document({
    creator: 'Equipo Caso N.º 1',
    title: 'Marco Teórico — Series de Tiempo y Criptoactivos',
    description: 'Primera entrega del Caso N.º 1, Señales y Sistemas',
    features: { updateFields: true },
    styles: apa.estilosDocumento(),
    sections: [{
      properties: apa.propiedadesPagina(),
      headers: { default: apa.encabezadoPagina() },
      children: [...portada(), ...cuerpo],
    }],
  });

  const destino = process.argv[2]
    // El nombre sale del manifiesto, y si no lo declara, de la carpeta. Tenerlo
    // fijo hacia que la entrega de la Semana 2 se escribiera en un archivo llamado
    // "Semana 1", que es la clase de detalle que llega al profesor.
    || path.join(ENTREGA, `${plan.documento || path.basename(ENTREGA)}.docx`);

  Packer.toBuffer(documento).then((contenido) => {
    fs.writeFileSync(destino, contenido);
    console.log(`escrito: ${path.relative(RAIZ, destino)}`);
    console.log(`  ${Math.round(contenido.length / 1024)} KiB`);
    console.log(`  ${conteo.figuras} figuras y ${conteo.tablas} tablas, renumeradas de corrido`);
    console.log(`  ${referencias.length} referencias fundidas de ${documentos.length} secciones`);
    if (avisos.length) {
      console.log(`\n  ${avisos.length} bloque(s) SIN REDACTAR — el documento no esta listo:`);
      const porSeccion = {};
      avisos.forEach((a) => { porSeccion[a.seccion] = (porSeccion[a.seccion] || 0) + 1; });
      Object.entries(porSeccion).forEach(([s, n]) => console.log(`    ${s}: ${n}`));
      avisos.slice(0, 10).forEach((a) => console.log(`      · ${a.texto}`));
    } else {
      console.log('  sin bloques pendientes: el documento esta completo');
    }
    // El indice se escribe como campo TOC sin resultado cacheado, asi que sale
    // vacio hasta que Word lo calcule. Quien entregue tiene que hacer este paso
    // o el evaluador abre un indice en blanco.
    console.log('\n  antes de entregar: abrir en Word, seleccionar el indice y F9');
    console.log('  (el campo TOC no trae las paginas hasta que Word las calcula)');
  });
}

main();
