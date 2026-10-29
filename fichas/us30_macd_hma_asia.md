# FICHA · US30 compra limit en HMA(30) + 1 ATR tras el cruce a la baja del MACD(10,50), solo en sesión asiática (M30)
Regla: Compro US30 en velas de 30 min cuando, al cierre de una vela dentro de la sesión asiática, la línea principal del MACD(10,50,9) cruza por debajo de su señal: dejo una orden limit de compra en el nivel hma(30) + 1 × ATR(14), con el nivel congelado y válida 15 velas (una nueva activación la reemplaza; la activación inversa la cancela). Salgo cuando el precio toca el stop vigente: el stop inicial a 2 × ATR(30) del precio de entrada, que se sustituye por el trailing de 2,5 × ATR(30) bajo el cierre, actualizado al cierre de cada vela, o a las 48 velas, lo que ocurra primero. Stop: 2 × ATR(30). Horario: lunes a viernes 01:00–23:59 hora del servidor del bróker (hora de Nueva York + 7 h; inicio incluido, fin excluido). Riesgo: 1 % del capital inicial (100.000) por operación.
Por qué funcionaría: tras el cruce a la baja del MACD, en la rueda asiática (de menor volumen) los empujes bajistas tienden a agotarse y el precio vuelve hacia su media; comprar en el nivel de HMA + 1 ATR busca capturar ese retorno con una salida corta (trailing y tope de 48 velas). (propuesta, confírmala)

## Hipótesis completa del trader (textual)
Copiada sin cambios el 2026-10-29 (el texto pegado empezaba en «NTRADA»; se corrigió esa letra). Es la fuente de verdad de esta ficha, junto con las definiciones exactas que el trader pegó después (debajo del bloque). El activo (US30) y la temporalidad (M30) los dijo el trader en el mensaje, no dentro del bloque.

```
ENTRADA LONG:
  Armado:
  1. [TRIGGER] cross_below(macd(10,50).main,macd(10,50,9).signal)
  2. [filtro] in_session(asia)
  Orden: LIMIT en hma(30)+1atr (atr = ATR(14)), nivel congelado al armarse; vigencia 15 velas, luego se cancela. Mientras el trigger siga verdadero no se modifica; una nueva activación reemplaza nivel y vencimiento (y, con atr_ref: signal, fotografía otro ATR). La activación inversa la cancela
ATR          : SMA móvil del True Range
               el «atr» de un offset ±k atr es siempre ATR(14), aunque las salidas midan con otro período (acá ATR(30))
CAPITAL INICIAL: 100000 unidades monetarias de la cuenta
SIZING       : 1% de riesgo sobre capital inicial; lotaje = riesgo / distancia al SL, redondeado hacia ABAJO al paso de lote del símbolo y acotado a su lote mínimo y máximo
SALIDAS      : SL inicial 2 × ATR(30); trailing 2.5 × ATR(30) actualizado al cierre de cada barra; cierre forzado a las 48 velas
REENTRADA    : una activación nueva en la vela de salida puede generar otra entrada desde la siguiente vela disponible; las órdenes stop/limit deben alcanzar su nivel. No hay reentrada normal en la misma vela
MERCADO      : sesiones en hora del servidor del bróker; inicio incluido, fin excluido
               lunes a viernes: 01:00–23:59
               Los días y horarios no declarados quedan cerrados, incluidos sábados y domingos si no tienen sesiones
VELAS        : el calendario NO recorta la serie: las velas se agregan con todas las M1 del archivo, incluidas las horas cerradas, y los indicadores se calculan sobre esa serie completa, que es la misma que construye el terminal
               Sólo se forman velas con M1 disponibles: una hora incompleta conserva su marca HH:00 y no se rellenan minutos ausentes
               Vencimientos, salidas por tiempo y cualquier contador en barras recorren esa serie entera, estén sus velas dentro o fuera de sesión
               El calendario autoriza acciones por el minuto real de cada una, no por la marca de la vela que la contiene: una vela que empieza cerrada y abre a mitad no queda bloqueada entera
               execution.trading_window es otra cosa: expresa cuándo la estrategia decide operar dentro de un mercado ya abierto
EJECUCIÓN    : si una vela contiene a la vez SL y TP, se recorren sus M1 en orden; si ambos niveles caen en el mismo minuto o faltan M1, gana el SL (execution.intrabar_resolution: m1; sl_tp_same_bar: sl_first); la salida por tiempo sostiene N barras completas DESPUÉS de la barra del fill y cierra en la apertura siguiente (execution.time_exit_mode: after_full_bars); reproduce motores que recién observan el fill intrabar al comenzar la vela posterior
AL PORTAR    : Nivel de la pendiente: tras cerrar la vela de señal, calcular el nivel con los datos hasta ese cierre INCLUSIVE y congelarlo al armar la orden. Se coloca en la apertura siguiente y no se recalcula mientras vive
               Trailing: primera actualización al cierre de la vela de ENTRADA, sin exigir avance previo; la distancia usa el ATR(30) de la vela que acaba de cerrar, no el congelado al armar. Adentro de la vela rige el nivel anterior: el stop nuevo vale recién desde la apertura siguiente
               Bid/Ask: los indicadores se calculan sobre Bid. Un long entra al Ask y liquida al Bid; un short entra al Bid y liquida al Ask, que es como disparan un buy stop y un sell stop en MT5. El trailing se ancla en el cierre del lado que liquida
BRÓKER       : Colocación: la orden se pide una sola vez, en el primer tick de la vela siguiente a la señal. Si la cotización ya está en el nivel o pasada de él no hay pendiente válida que colocar: se entra a mercado en ese tick
               Fill: al nivel. Si la vela —o el mercado, al reabrir— abre ya pasada del nivel, a esa apertura, que es lo que cobra un bróker real. El SL y el TP se calculan con el precio REAL de entrada, no con el nivel: después de un fill con gap hay que recalcularlos
               Vencimiento: orden GTC, sin expiración del bróker. La orden vive 15 velas de la serie completa —las de horas cerradas también cuentan— desde la de colocación, incluida, y se borra en el primer tick de la vela siguiente. Si el bróker rechaza el borrado por mercado cerrado, reintentarlo en CADA TICK hasta que entre, no en la vela siguiente. El fill va primero: si esa vela —o el mercado, al reabrir— abre ya en el nivel o pasada de él, la orden se llena antes de poder borrarla, y el backtest también la llena
               Reemplazo: una activación nueva cancela la orden y coloca otra —el lotaje cambia con el ATR—; no es una modificación del precio. El borrado se CONFIRMA antes de colocar la nueva: si el bróker no lo confirma, la anterior sigue viva con su nivel, su vencimiento y su ATR, y la nueva no se coloca. Si el bróker rechaza la nueva por stops level, la anterior ya no está
               Mercado cerrado: colocar, reemplazar y cancelar se piden una sola vez. Si el bróker rechaza por mercado cerrado NO se reintenta ni se traslada a la reapertura: la señal se pierde, el reemplazo deja la orden anterior como estaba y la cancelación por activación inversa la deja viva hasta vencer
               Stops level: 150 puntos. La pendiente pedida a menos de esa distancia de la cotización se rechaza y no se reintenta; la entrada cuyo SL o TP queda más cerca se descarta. Se compara en puntos enteros
               Modificación del stop: el backtest da por hecho que el stop nuevo rige desde que se calcula y que un toque sólo cuenta con el mercado abierto. Hasta que la modificación se confirma, el stop VIGENTE en el bróker es el anterior, y el EA lleva las dos cosas por separado: pide el nivel una vez calculado y, si el bróker lo rechaza —mercado cerrado, stops level—, lo RECUERDA como objetivo y lo reintenta en cada tick, sin recalcularlo, sin aflojarlo con el cálculo de la vela siguiente y releyendo la posición para confirmar el stop aplicado. Si la cotización cruza el objetivo antes de la confirmación, cierra a mercado, al precio de ese tick, no al nivel: un objetivo recordado no es un stop aceptado, y sólo protege mientras el EA corre y está conectado
               Reintentos: lo que se reintenta en cada tick —el borrado de una vencida, el stop nuevo del trailing— consulta antes la tabla de sesiones del símbolo, y con la sesión cerrada no se envía. Las operaciones no cambian, porque el bróker lo iba a rechazar, y deja de recibir una solicitud por tick durante todo el cierre
```

Definiciones del trader (textual, pegadas el 2026-10-29 después de la hipótesis):

```
Definiciones exactas:
  atr: ATR(n) SMA: TR = max(H−L, |H−C_prev|, |L−C_prev|), primera barra H−L; ATR_i = promedio simple de los últimos n TR, disponible desde n−1.
  hma: HMA(n) sobre Close = LWMA(2·LWMA(n/2) − LWMA(n), raíz(n)), con n/2 y raíz(n) truncados a entero. Sobre una serie lineal devuelve el valor de la barra actual.
  in_session: in_session(s): la hora de pared de la barra cae en [desde, hasta) de la sesión s, leída en la zona de esa sesión. Las horas de cada sesión usada van arriba.
  macd: MACD(fast,slow,signal): main = EMA(Close,fast) − EMA(Close,slow), fast < slow; signal = EMA(main,signal); histogram = main − signal. Cada EMA usa semilla SMA y alpha 2/(n+1). Main es válida desde slow−1; signal e histogram desde slow+signal−2.
  sesión asia: de 09:00 a 15:00 Asia/Tokyo (el fin no entra)
```

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: director · escritor-hipotesis (manual seguido por el director)
Qué se hizo: regla revisada campo a campo. ✅ disparo cross_below(macd(10,50).main, macd(10,50,9).signal) · ✅ filtro in_session(asia) · ✅ orden limit en hma(30) + 1 × ATR(14), nivel congelado, vigencia 15 velas, reemplazo por activación nueva · ✅ activación inversa cancela la orden · ✅ stop inicial 2 × ATR(30) · ✅ trailing 2,5 × ATR(30) al cierre · ✅ cierre forzado a las 48 velas · ✅ sizing 1 % de 100.000 con lote hacia abajo · ✅ horario lunes a viernes 01:00–23:59, stops level 150 puntos · ✅ «sesión asiática»: el trader dijo 09:00 a 15:00 hora de Tokio · ⚠️ «activación inversa»: el texto no dice cuál es (solo hay compras) · ⚠️ una orden limit de COMPRA debe estar por debajo del precio, y hma(30) + 1 ATR puede quedar por encima.
Resultado: hipótesis completa y medible; solo compras («ENTRADA LONG»). Encaja con MI_PLAN.md en mercado (US30), plataforma y vela de 30 minutos; la frecuencia se mide en la fase 04. Como en las otras fichas, la regla no cierra el viernes: la manda el texto del trader (el tope de 48 velas, 24 horas de mercado, limita el tiempo abierto).
Supuestos: (1) Activo US30 y velas M30: dato del trader. (2) MACD, ATR y HMA: las definiciones exactas del trader (EMA con semilla SMA y alpha 2/(n+1); ATR = SMA del rango verdadero, primera barra H−L; HMA con n/2 y raíz(n) truncados), sobre el cierre Bid; cross_below = la línea principal pasa de estar por encima (o igual) a estar por debajo de la señal entre dos cierres. (3) Sesión asiática = de 09:00 a 15:00 hora de Asia/Tokyo, el fin no entra (definición del trader); se lee la hora de pared de la barra (su hora de apertura) pasada a la zona de Tokio. Tokio no cambia de hora: son 00:00 a 06:00 UTC, que en hora del servidor (Nueva York + 7 h, que sigue el cambio de hora de EE. UU.) son 02:00 a 08:00 en invierno y 03:00 a 09:00 en verano. (4) HMA(30) sobre el cierre Bid con la definición exacta del trader (LWMA(2·LWMA(15) − LWMA(30), 5)). (5) Activación = la vela cuyo cierre deja cross_below pasando de falso a verdadero con el filtro de sesión cumplido. (6) «Activación inversa» = el cruce al alza del MACD (cross_above); cancela la orden viva. (7) Limit de compra: si el nivel está por debajo del Ask, la orden espera y se llena cuando el Ask baja al nivel; si el nivel ya está en el Ask o por encima, no hay pendiente válida y se compra a mercado en la apertura siguiente (lo dice el texto en BRÓKER). (8) Cierre a las 48 velas: se cuentan desde la vela de entrada y se sale en la apertura siguiente a la vela 48. (9) Tamaño del símbolo, spread, swap y horario de US30: datos de la fase 04 (se piden al trader cuando se llegue). (10) Solo compras.
Veredicto: APRUEBA (con los supuestos 6 y 7 por confirmar)
Siguiente paso: fase 02 (AED) con datos/US30.csv pasado a M30, solo con el primer 70 %.

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: director · aed (código: codigo/us30_macd_hma_asia_aed.py)
Qué se hizo: datos/US30.csv (M1, hora del servidor) recortado a partir de 2011-01-01 por el trader (2009 y 2010 tienen muy pocos datos: el archivo completo daba NO APTA) y pasado a velas M30. Datos: datos/us30_30m_mt5.csv · APTA CON AVISOS (faltan el 3,6 % de las velas, sin rellenar) · informe en resultados/us30_30m_mt5_calidad.md; el M1 (datos/us30_1m_mt5.csv) da NO APTA por el 6,6 % de minutos faltantes (umbral 5 %), igual que pasó con US100: se usará con ese aviso para resolver el orden del stop en la fase 04. AED solo con el primer 70 % de las velas (129.993 velas, 2011-01-03 a 2021-12-29); el 30 % final queda reservado para la fase 04. Sin pre-registro. Se midió el retorno, en unidades de ATR(30) de la vela de señal, a 1, 5 y 20 velas desde el fill de la orden limit en hma(30) + 1 × ATR(14), colocada en la apertura siguiente a la señal, viva 15 velas y cancelada por el cruce al alza del MACD, contra la línea base y dos controles.
Resultado: la regla (1.043 activaciones, 1.042 llenadas) da +0,03 ATR a +1 vela, +0,06 a +5 y +0,27 a +20 (mediana +0,27; el 54,8 % sube). Línea base, cualquier vela: +0,01, +0,03 y +0,10 a +20 (mediana +0,26; 54,1 % sube); solo velas de sesión asiática: +0,16 a +20 (mediana +0,26; 54,9 % sube). Control 1, orden armada en cada vela de sesión asiática y sin MACD (31.943 llenadas): +0,17 a +20 (mediana +0,28; 55,0 % sube). Control 2, cruce del MACD a cualquier hora (4.685 llenadas): +0,15 a +20 (mediana +0,28; 54,1 % sube). Por año (86 a 108 casos): supera a la línea base en 9 de 11 años y al control 1 en 6 de 11; pierde 2016 (−0,05); 2018 a 2021 sostienen la media. HALLAZGO: en 1.042 de 1.043 casos la orden no espera: hma(30) + 1 ATR queda por encima del precio, una limit de compra ahí no es una pendiente válida, y se compra a mercado en la apertura siguiente (caso M, como dice el texto en BRÓKER). En la práctica la regla es «comprar a mercado tras el cruce a la baja del MACD en la sesión asiática». La ventaja está solo en la media (+0,27 contra +0,10 y +0,16); la mediana y la proporción de casos que suben son iguales a las de la línea base y a las de los controles. Frecuencia: unas 97 activaciones al año, más que las 6 al mes (72 al año) de MI_PLAN.md.
Supuestos: sin pre-registro; línea base = cualquier vela con el mismo ATR(30); definiciones exactas del trader para MACD, ATR y HMA; sesión asiática = 09:00 a 15:00 de Asia/Tokyo sobre la hora de apertura de la vela; activación inversa = cross_above del MACD; stops level 150 puntos con punto 0,01 (supuesto: precios con 2 decimales; solo afecta a las órdenes que esperan, que casi no hay); sin costes, spread, swap ni stop (eso es de la fase 04); la muestra incluye la subida del índice de 2011 a 2021.
Veredicto: APRUEBA con reserva débil (supera a la línea base en la media y en 9 de 11 años, pero no en mediana ni en proporción de casos que suben, y no supera claramente al control de sesión asiática: 6 de 11 años; solo es AED sin costes, la fase 04 es el filtro real)
Siguiente paso: fase 03 (reglas) con el agente reglas, sin tocar ningún parámetro.

## Fase 03 · Reglas · MOTOR
Agente / skill: reglas (manual seguido por el director)
Qué se hizo: se tomó la estructura del pseudocódigo aprobado de las fichas US100 (7 pasos, orden de salidas fijo, vigencia contada desde la vela de colocación) y se cambió solo lo propio de esta regla: disparo cross_below del MACD con filtro de sesión asiática, orden LIMIT de compra en hma(30) + 1 × ATR(14), activación inversa que cancela, stop inicial de 2 × ATR(30), trailing de 2,5 × ATR(30) y cierre forzado a las 48 velas. No se cambió ningún parámetro del trader.
Resultado: pseudocódigo de 7 pasos con 28 supuestos decididos (abajo). Los tres casos de la limit (compra a mercado si el Ask ya está en el nivel o más abajo, rechazo por stops level, espera) y qué pasa si no se cumple nada.
Supuestos: los 28 de la lista de abajo; los que más pesan son el 5 (la orden limit casi nunca espera: hma(30) + 1 ATR queda por encima del precio y se compra a mercado, como dice el texto), el 8 (el ATR(30) del stop inicial y del lote sale de la vela de señal), el 10 (el cierre a las 48 velas) y el 24 al 26 (datos del símbolo US30 que el trader no dio: se usan los de US100 hasta que los confirme).
Veredicto: APRUEBA (pseudocódigo sin huecos; las especificaciones de US30 son supuestos por confirmar)
Siguiente paso: fase 04 con costes sobre datos/us30_1m_mt5.csv (M1) y las velas M30 (70 % dentro de muestra, 30 % fuera), sin tocar parámetros.

> NOTA. La hipótesis no cierra posiciones el viernes: solo el stop o las 48 velas (24 horas de mercado) las cierran. MI_PLAN.md dice que el trader no deja operaciones abiertas el fin de semana. La regla manda tal como el trader la escribió; no se agregó ningún cierre.

### Pseudocódigo · US30 MACD(10,50) cruza a la baja en sesión asiática + limit en HMA(30) + 1 ATR (M30, solo compras)

```
DATOS: US30, velas de 30 minutos, solo compras. Horas = las del servidor del bróker
  (hora de Nueva York + 7 h). Horario operable (dato del trader): lunes a viernes
  01:00–23:59, inicio incluido, fin excluido.
  Precios: los indicadores se calculan sobre Bid. COMPRA se hace al Ask; SALGO se hace al Bid.
  Ask = Bid + spread de la vela (la columna spread del CSV, en puntos de 0,01 unidades).
  PUNTO = 0,01 unidades de índice. STOPS_LEVEL = 150 puntos = 1,5 unidades (dato del trader).
  Velas: se arman con TODAS las M1 del archivo (también las de horas cerradas) y los indicadores
  usan esa serie completa. Solo existen velas con M1; no se rellenan minutos.
  MERCADO ABIERTO en un minuto = lunes a viernes, de 01:00 (incluido) a 23:59 (excluido).
  Cada acción (colocar, borrar, tocar un stop, cerrar por tiempo) vale según el minuto real en que ocurre.
  Capital inicial = 100.000 USD. RIESGO = 1 % del capital inicial = 1.000.
  VALOR_UNIDAD = 1 USD por lote por cada unidad de índice (supuesto). Paso de lote 0,01,
  mínimo 0,01, máximo 300 (supuesto).
  COSTES (modelo; el cálculo y la prueba son de la fase 04):
    - Spread: el de la última columna del CSV en cada vela, en puntos de 0,01. Si falta, la mediana.
    - Comisión = 0. Deslizamiento = 0.
    - Swap (solo compras): -6,9 % anual, base 365 días, sobre el valor nocional, una vez por cada
      noche de lunes a viernes al pasar el rollover de las 00:00 del servidor (supuesto: el de US100).
  Una sola operación a la vez. Al empezar: sin operación, sin ORDEN VIVA, sin SEÑAL.

  Definiciones (al cierre de cada vela, sobre Bid; las del trader):
    ATR(n) = media simple de los últimos n rangos verdaderos (rango verdadero = el mayor entre
             máximo-mínimo, |máximo-cierre anterior| y |mínimo-cierre anterior|; el de la primera
             vela es máximo-mínimo). Disponible desde la vela n.
    HMA(30) = LWMA( 2 x LWMA(cierre,15) - LWMA(cierre,30), 5 ), con LWMA = media ponderada con
              pesos 1..n (el mayor para la vela más reciente).
    EMA(n): semilla = media simple de los n primeros valores; después r = r + (x - r) x 2/(n+1).
    MACD_PRINCIPAL = EMA(cierre,10) - EMA(cierre,50), válida desde la vela 50.
    MACD_SEÑAL = EMA(MACD_PRINCIPAL, 9), válida desde la vela 58.
    CRUCE_BAJA = MACD_PRINCIPAL < MACD_SEÑAL ahora y MACD_PRINCIPAL >= MACD_SEÑAL en la vela anterior.
    CRUCE_ALZA = MACD_PRINCIPAL > MACD_SEÑAL ahora y MACD_PRINCIPAL <= MACD_SEÑAL en la vela anterior.
    ASIA = la hora de apertura de la vela, pasada a la zona Asia/Tokyo, está entre 09:00 (incluido)
           y 15:00 (excluido). Tokio no cambia de hora; el servidor sí sigue a Nueva York.
    ACTIVACIÓN = CRUCE_BAJA y ASIA en esta vela.
    Sin las velas suficientes para calcular algo, CRUCE_BAJA, CRUCE_ALZA y ACTIVACIÓN son falsos.

CADA VELA NUEVA (la llamo VELA ACTUAL), en este orden:

  1. Al empezar la VELA ACTUAL (haya o no mercado abierto):
       SI hay una ORDEN VIVA: VIDA = VIDA + 1.
       SI hay una operación abierta: VELAS_DENTRO = VELAS_DENTRO + 1 (la vela de entrada es la 0).

  2. En el PRIMER TICK de la VELA ACTUAL:
       a. SI estoy dentro y VELAS_DENTRO = 49 (la entrada fue en la vela F y ya pasaron 48 velas
          completas después de F): CIERRO a mercado al Bid de ese tick (a la apertura). SI el
          mercado está cerrado, cierro en el primer minuto con mercado abierto. Ve al paso 6.
       b. SI estoy fuera y hay una ORDEN VIVA y el Ask está en NIVEL o por debajo:
            COMPRA al Ask de ese tick (si abrió con gap, a esa apertura, que es mejor o igual que
            el nivel). Ve al paso 4.
       c. SI hay una ORDEN VIVA y hay una CANCELACIÓN pendiente (la vela anterior cerró con
          CRUCE_ALZA) o con VIDA >= 16 (ya vivió sus 15 velas): pido borrarla. SI el mercado está
          cerrado, no se reintenta si fue por la cancelación inversa (la orden queda viva hasta
          vencer); por vencimiento se reintenta en cada tick con mercado abierto. En el primer
          tick con mercado abierto se hace antes el punto b. Orden borrada: ya no hay ORDEN VIVA.
       d. SI hay una SEÑAL (la dejó la vela anterior) y estoy fuera:
            - SI el mercado está cerrado en ese minuto: la SEÑAL se pierde, no se reintenta.
              La ORDEN VIVA anterior, si la había, queda como estaba.
            - SI NO: SI hay una ORDEN VIVA, la cancelo y espero a que el borrado se confirme
              (si no, la anterior sigue con su NIVEL, VIDA y ATR_ORDEN, y la nueva no se coloca).
              Luego:
                * Caso B: SI el Ask ya está en NIVEL_SEÑAL o por debajo: la limit no es una
                  pendiente válida; COMPRA al Ask de ese tick (a mercado). Ve al paso 4.
                * Caso C: SI NO, SI Ask - NIVEL_SEÑAL < 150 puntos enteros (1,5 unidades): el
                  bróker rechaza la orden y no se reintenta; no queda ORDEN VIVA.
                * Caso A: SI NO, coloco una ORDEN VIVA de COMPRA LIMIT con NIVEL = NIVEL_SEÑAL,
                  ATR_ORDEN = ATR_SEÑAL y VIDA = 1. La VELA ACTUAL es la VELA DE COLOCACIÓN.
            Borro la SEÑAL (se usa una sola vez).

  3. Durante la VELA ACTUAL, recorriendo sus M1 en orden, con mercado abierto:
       SI estoy fuera y hay una ORDEN VIVA con VIDA <= 15 y el Ask baja hasta NIVEL:
         COMPRA en NIVEL. Ve al paso 4.

  4. Tras cualquier COMPRA (en el paso 2 o en el 3):
       PRECIO_ENTRADA = el precio real de la compra. La ORDEN VIVA desaparece. VELAS_DENTRO = 0.
       ATR_STOP = ATR_ORDEN de la orden (si la compra fue a mercado en el paso 2d, el ATR_SEÑAL
                  de la SEÑAL que la originó). Es el ATR(30) fotografiado en la vela de señal.
       DISTANCIA = 2 x ATR_STOP, en unidades de índice.
       SL_INICIAL = PRECIO_ENTRADA - DISTANCIA (con el precio real, no con NIVEL).
       SI DISTANCIA < 150 puntos enteros (1,5 unidades): la entrada se descarta. Ve al paso 6.
       LOTE = RIESGO / (DISTANCIA x VALOR_UNIDAD), redondeado hacia ABAJO a 0,01 y acotado entre
              0,01 y 300.
       STOP_VIGENTE = SL_INICIAL. Ve al paso 5.

  5. MIENTRAS esté dentro, en cada vela nueva, en este orden:
       a. En cada minuto con mercado abierto (también el de la compra y los siguientes de la vela
          de entrada): SI la vela abrió con el Bid por debajo de STOP_VIGENTE, SALGO a esa
          apertura. SI NO, SI el Bid toca STOP_VIGENTE, SALGO en STOP_VIGENTE. Si la compra y el
          toque caen en el mismo minuto, gana el stop. Tras SALGO ve al paso 6.
       b. Al cierre de la VELA ACTUAL, si sigo dentro (también al cierre de la vela de entrada,
          sin exigir avance previo):
            TRAILING = cierre (Bid) de la VELA ACTUAL - 2,5 x ATR(30) de esa misma vela
                       (no el ATR_STOP fotografiado).
            SI TRAILING > STOP_VIGENTE: STOP_VIGENTE = TRAILING.
            El stop nuevo vale desde la apertura de la vela siguiente.

  6. Al cerrar la VELA ACTUAL, calculo los indicadores (siempre, haya o no operación) y:
       SI hay CRUCE_ALZA y hay una ORDEN VIVA: marco CANCELACIÓN pendiente (se pide en el
         primer tick de la vela siguiente, paso 2c).
       SI estoy fuera (sin operación) y hay ACTIVACIÓN:
         NIVEL_SEÑAL = HMA(30) + 1 x ATR(14), con los datos hasta el cierre de la VELA ACTUAL
                       inclusive. Queda congelado.
         ATR_SEÑAL = ATR(30) al cierre de la VELA ACTUAL (la fotografía; fija el stop inicial y el lote).
         SEÑAL = lista para pedirse en el primer tick de la vela siguiente.
         (Una salida en esta misma vela no impide la ACTIVACIÓN: puede haber reentrada desde la
         vela siguiente. En esta misma vela no hay otra entrada.)
       SI NO (no hay ACTIVACIÓN, o estoy dentro): no hay SEÑAL nueva. Mientras no haya otra
         ACTIVACIÓN, la ORDEN VIVA no cambia: NIVEL, VIDA y ATR_ORDEN siguen igual.

  7. SI no se cumplió nada de lo anterior → no hago nada. FIN de la vela.
     Si la orden agota sus 15 velas sin llenarse, se borra (paso 2c) y no se opera hasta la
     próxima ACTIVACIÓN. Una posición abierta sigue abierta hasta que el stop o las 48 velas la cierren.
```

Lo que viene del texto del trader y se aplicó tal cual (no son supuestos): disparo cross_below(macd(10,50).main, macd(10,50,9).signal) con filtro in_session(asia) de 09:00 a 15:00 Asia/Tokyo; nivel hma(30) + 1 × ATR(14) calculado al cierre de la vela de señal, congelado y colocado en la apertura siguiente; vigencia de 15 velas de la serie completa desde la de colocación incluida; activación nueva reemplaza nivel y vencimiento, con borrado confirmado antes de colocar la nueva; activación inversa cancela la orden; entrada a mercado si la cotización ya está en el nivel o más allá; fill con gap a la apertura, SL y lote con el precio real; stop inicial 2 × ATR(30); trailing 2,5 × ATR(30) de la vela recién cerrada desde la vela de entrada; cierre forzado a las 48 velas (barras completas DESPUÉS de la del fill, a la apertura siguiente); sizing de 1 % sobre 100.000 con lote hacia abajo y acotado; entra al Ask y sale al Bid; con mercado cerrado se pide una sola vez; stops level 150 puntos sin reintento; horario de lunes a viernes 01:00–23:59; reentrada desde la vela siguiente a la de salida.

Supuestos del pseudocódigo (todos decididos; solo lo que el texto no dice):
1. US30 y velas de 30 min: dato del trader; solo compras («ENTRADA LONG»).
2. MACD, ATR y HMA: definiciones exactas del trader (EMA con semilla de media simple y alpha 2/(n+1)).
3. CRUCE_BAJA = la principal pasa de ≥ a < la señal entre dos cierres consecutivos; CRUCE_ALZA, el inverso (supuesto sobre «cross_below»).
4. ACTIVACIÓN = CRUCE_BAJA con ASIA en la vela de señal; con posición abierta no se arman órdenes nuevas, pero los indicadores se calculan igual. Los cruces no se repiten sin un cruce al alza en medio, así que «mientras el trigger siga verdadero no se modifica» solo afecta a esa vela.
5. La orden es una LIMIT de compra. hma(30) + 1 ATR casi siempre queda por encima del precio: ahí no hay pendiente válida (una limit de compra por encima del Ask se ejecutaría ya) y se compra a mercado en la apertura siguiente, como dice el texto en BRÓKER. En el tramo del AED esto pasó en 1.042 de 1.043 casos. No se cambió el signo del nivel.
6. ASIA se evalúa con la hora de apertura de la vela de señal (la vela cuenta si empieza dentro de la ventana). Servidor = Nueva York + 7 h.
7. Solo hay una posición a la vez; una activación con la orden viva y sin posición la reemplaza (nivel, vencimiento y ATR).
8. El texto dice que el reemplazo «fotografía otro ATR» y que «el lotaje cambia con el ATR». Decido, por ser lo más fiel: el ATR(30) de la vela de señal se guarda con la orden (ATR_ORDEN) y de él salen el stop inicial (2 × ATR_ORDEN, medido desde el precio real de entrada) y el lote. El trailing sí usa el ATR(30) de la vela recién cerrada, nunca el fotografiado. El ATR(14) del nivel es el de la vela de señal.
9. Activación inversa = CRUCE_ALZA (el texto no la define). La cancelación se pide en el primer tick de la vela siguiente; con mercado cerrado no se reintenta y la orden queda viva hasta vencer (lo dice el texto).
10. Cierre forzado a las 48 velas: la vela de entrada es la F; se sostienen 48 velas completas después de F y se cierra al Bid en la apertura de la vela F + 49. Se cuentan velas de la serie completa, también las de horas cerradas. Con mercado cerrado a esa apertura, se cierra en el primer minuto con mercado abierto.
11. Si la orden agota sus 15 velas, se borra y no se opera hasta la próxima activación; si la vela de colocación o la de reemplazo abre en el nivel o por debajo, la orden vieja se llena primero (paso 2b).
12. Stop vigente = el mayor entre el SL inicial y el trailing; el trailing solo sube. El texto no dice «solo sube».
13. Si una vela posterior abre con el Bid por debajo del stop, se sale a esa apertura (hueco); si no, en el nivel del stop.
14. Si la compra y el toque del stop caen en el mismo minuto, gana el stop; si caen en la misma vela se recorren las M1 desde el minuto de la compra.
15. Si tras un fill con gap el SL calculado con el precio real queda a menos de 150 puntos del Bid, la entrada se descarta (stops level); la orden queda consumida.
16. Sin objetivo de ganancia: salen el SL inicial, el trailing y las 48 velas.
17. Sin límite de operaciones por día; la posición puede pasar de un día a otro y de una semana a otra (ver NOTA). Sin cierre del viernes.
18. En el backtest, un borrado o un reemplazo con mercado abierto se confirma siempre; solo falla por mercado cerrado.
19. En real, el EA recuerda el stop del trailing si el bróker lo rechaza y lo reintenta en cada tick con sesión abierta; el backtest da por hecho que el stop nuevo rige desde la apertura siguiente y que un toque solo cuenta con el mercado abierto.
20. «Punto» = 0,01 unidades (supuesto: precios con 2 decimales; el spread del CSV, de 35 a 438 puntos, equivale a 0,35 a 4,38 unidades); las comparaciones del stops level (150 puntos) se hacen con enteros.
21. Si faltan datos (huecos), las velas se cuentan tal como están en el CSV, sin rellenar; las 15 velas de vigencia, las 48 del cierre y las de los indicadores se cuentan sobre esa serie.
22. Los indicadores necesitan sus velas completas (la señal del MACD, desde la vela 58); antes de eso no hay activación.
23. Todos los precios de las velas son Bid; el nivel de la limit se compara con el Ask de cada minuto.
24. Símbolo US30 (SUPUESTO, el trader no lo dio): punto 0,01; contract_size 1; 1 lote gana o pierde 1 USD por cada unidad de índice; paso de lote 0,01, mínimo 0,01, máximo 300; cuenta en USD, apalancamiento 1:100. Son los de US100; por confirmar.
25. Swap (SUPUESTO, el trader no lo dio): largo -6,9 % anual, base 365 días, una vez por cada noche de lunes a viernes al pasar el rollover de las 00:00 del servidor, nocional con el cierre Bid de la última vela antes del rollover. Es el de US100; por confirmar.
26. Spread (SUPUESTO): la columna spread de datos/US30.csv, en puntos de 0,01; si falta, la mediana. Por confirmar de qué bróker viene.
27. Horario operable 01:00–23:59 hora del servidor, inicio incluido, fin excluido (dato del texto); hora del servidor = Nueva York + 7 h.
28. AVISO de datos: el M1 de datos/us30_1m_mt5.csv da NO APTA (6,6 % de minutos faltantes dentro del horario; límite 5 %) y el M30 APTA CON AVISOS (3,6 %). Se usa igual, como en US100, sin rellenar huecos; los saltos (unos 2.100 en M30) quedan como aviso.

## Fase 04 · Backtest · MOTOR
Agente / skill: validador (validador-4de4) · código: codigo/us30_macd_hma_asia.py · reporte: resultados/us30_macd_hma_asia_reporte.md
Qué se hizo: backtest con datos/us30_1m_mt5.csv (M1, resuelve el orden dentro de cada vela) y el spread por minuto de datos/US30.csv (los 5.284.083 minutos coinciden por fecha, sin faltantes), velas M30 de datos/us30_30m_mt5.csv (APTA CON AVISOS). Corte 70/30 por velas: dentro de muestra 2011-01-03 a 2021-12-29 (129.993 velas); fuera de muestra 2021-12-29 a 2026-09-18 (55.712 velas). Capital 100.000, riesgo 1 % por operación, spread (mediano 2,2 unidades), swap largo −6,9 % anual, sin comisión. Motor derivado del de US100 (ya contrastado con el motor del trader); solo cambió lo propio de esta regla. Se rehicieron 3 operaciones a mano por otro camino (pandas) y coincidieron en señal, nivel, ATR, entrada, stop, lote, salida y swap; el motor no mira el futuro (con los indicadores recalculados solo hasta la vela 15.000 del tramo fuera de muestra, las 121 operaciones son idénticas).
Resultado: fuera de muestra y con costes: factor de beneficio 1,43 (≥ 1,3 ✓) · 430 operaciones (≥ 30 ✓) · caída máxima 8,92 % (< 20 % ✓) · factor de beneficio sin la mejor operación 1,38 (> 1 ✓). Veredicto 4/4. Resultado neto +66.416 USD (bruto 67.754 y swap −1.339), 40,5 % ganadoras. Dentro de muestra (solo referencia): factor de beneficio 1,27, 952 operaciones, caída 11,20 %. Por año fuera de muestra: 2022 2,13 · 2023 1,14 (sin la mejor 0,95) · 2024 0,88 (−4.545 USD) · 2025 1,65 · 2026 1,40; solo 2024 pierde. Por tramo: primeros 3 años 1,36 y resto 1,55. Las 430 entradas son a mercado (caso B): ninguna limit esperó (en el tramo dentro de muestra, 951 a mercado y 1 limit que esperó). Salidas fuera de muestra: 341 por trailing, 3 por trailing con hueco, 64 por el stop inicial y 22 por las 48 velas. Frecuencia: 91 operaciones al año = 7,6 al mes (el plan dice unas 6).
Supuestos: los 28 de la Fase 03. Los que más pesan: símbolo US30 (punto 0,01, 1 lote = 1 USD por unidad), swap −6,9 % anual y spread de datos/US30.csv son los de US100 o los del CSV, por confirmar con el bróker; el M1 da NO APTA (6,6 % de minutos faltantes) y se usó con ese aviso; el cierre a las 48 velas cuenta velas de la serie tal como está en el CSV.
Veredicto: APRUEBA (4/4). Reservas: la regla es en la práctica una compra a mercado tras el cruce a la baja del MACD en la sesión asiática, porque la limit en hma(30) + 1 ATR no espera; el resultado fuera de muestra (1,43) es mejor que el de dentro (1,27), poco habitual; 2023 y 2024 dan poco o pierden; la caída de 8,92 % supera el 6 % que el plan acepta en backtest; la frecuencia (7,6 al mes) supera la del plan (6).
Siguiente paso: fase 05 (optimización, meseta de parámetros) con skill optimizar, solo dentro de muestra.

## Fase 05 · Optimización · MOTOR
Agente / skill: director · optimizar (código: codigo/us30_macd_hma_asia_optimizar.py · tabla: resultados/us30_macd_hma_asia_meseta.csv)
Qué se hizo: meseta de parámetros SOLO dentro de muestra (el 70 % más antiguo, 2011 a 2021-12), con el mismo motor y los mismos costes de la fase 04. 4 ejes ya existentes en la regla, 5 valores cada uno, 625 combinaciones: EMA lenta del MACD (40, 45, 50, 55, 60), stop inicial en ATR(30) (1,6, 1,8, 2,0, 2,2, 2,4), trailing en ATR(30) (2,0, 2,25, 2,5, 2,75, 3,0) y cierre forzado (38, 43, 48, 53, 58 velas). Los parámetros de la orden limit (HMA(30), el + 1 ATR y las 15 velas de vigencia) no se variaron porque la orden casi nunca espera. No se añadió ningún parámetro ni se eligió un óptimo; los valores de la ficha no cambian. La combinación de la ficha reproduce la fase 04 dentro de muestra (factor de beneficio 1,27, 952 operaciones, caída 11,20 %).
Resultado: factor de beneficio de las 625 combinaciones entre 1,13 y 1,32 (mediana 1,22); todas ganan (factor > 1) y tienen entre 890 y 993 operaciones. Solo 10 (2 %) llegan a 1,3 dentro de muestra, y la caída va de 8,4 % a 33,0 % (mediana 15,2 %). Umbral del Reto (todos los vecinos inmediatos con factor ≥ 1,3, ≥ 30 operaciones y ≥ 70 % del factor actual): de los 8 vecinos a un paso en un solo eje cumplen 1, de los 80 vecinos del cubo completo cumplen 6; todos conservan más del 70 % del factor actual (el peor vecino da 1,18). Es una meseta PLANA Y BAJA, no un pico: ningún eje la rompe (por ejemplo, el cierre forzado de 38 a 58 velas da 1,26 a 1,28), pero la ventaja dentro de muestra (1,27) ya está por debajo de 1,3, así que ningún vecino puede superar el umbral. Lo que más pesa es el trailing (con 2,75 a 3,0 el factor baja a 1,25 y la caída sube a 18 a 20 %) y el stop inicial (con 1,6 a 1,8 baja a 1,22).
Supuestos: solo dentro de muestra; costes de la fase 04; rejilla con 5 valores por eje, centrada en la ficha; el umbral es el provisional del Reto (metodo/METODO.md no fija otro).
Veredicto: NO APRUEBA (con el umbral provisional del Reto: los vecinos no llegan a factor 1,3 dentro de muestra, porque el valor de la ficha tampoco). No es un pico: la ventaja es estable y modesta en toda la rejilla. Los parámetros de la ficha no se tocan.
Siguiente paso: decide el trader: cerrar la idea aquí (como la regla de US100 con Donchian), o seguir a la fase 06 (robustez) con los parámetros tal cual, sabiendo que la fase 05 no aprobó.

## Fase 06 · Robustez · MOTOR
Agente / skill: director · robustez (código: codigo/us30_macd_hma_asia_robustez.py, semilla 42; gráficas en resultados/us30_macd_hma_asia_robustez.png; números en _robustez.json)
Qué se hizo: la regla y los parámetros de la fase 04, sin cambiar nada, aunque la fase 05 no aprobó (el trader pidió seguir). Cuatro pruebas sobre el tramo fuera de muestra (2021-12-29 a 2026-09-18, 430 operaciones, que reproduce la fase 04) y, para los años, sobre todo el periodo.
Resultado: (a) costes ×2 ✓: factor de beneficio 1,27 (mínimo 1,1), caída 12,39 %, con 432 operaciones. (b) Monte Carlo del orden ✓: 1.000 barajas, caída máxima mediana 9,8 %, percentil 95 de 16,5 % (máximo 30 %), la peor 34,0 %. (c) Remuestreo con reemplazo ✓: factor de beneficio con percentil 5 de 1,13 (mínimo 1), mediana 1,44, percentil 95 de 1,78. (d) Años malos ✓: 14 de 16 años ganan; pierden 2015 (−1.062 USD) y 2024 (−4.545 USD); sin el mejor año (2022) el factor de beneficio es 1,27. Veredicto de robustez 4/4. Prueba extra, informativa: spread ×2 y swap ×2 a la vez da factor de beneficio 1,26 y caída 12,56 %.
Supuestos: umbrales provisionales del Reto (a: factor ≥ 1,1; b: caída p95 < 30 %; c: factor p5 > 1; d: mitad de los años ganadores y factor sin el mejor año > 1), METODO.md no trae otros. Costes ×2 = el spread del CSV multiplicado por 2 (spread medio 2,9 unidades de índice, mediana 2,2; la fase 04 no tiene comisión ni deslizamiento que duplicar). Monte Carlo y remuestreo sobre el resultado de cada operación (1 % de riesgo sobre el capital inicial, sin reinvertir), con la caída medida con operaciones cerradas. Años por fecha de entrada; 2026 es un año parcial. Símbolo, swap y spread de US30 siguen siendo supuestos por confirmar.
Veredicto: APRUEBA (4/4). Avisos: (1) la fase 05 NO aprobó: el factor de beneficio dentro de muestra (1,27) no llega a 1,3 y con costes ×2 el fuera de muestra baja a 1,27: la ventaja existe pero es modesta, y es sensible al spread (el spread es el supuesto menos seguro). (2) El Monte Carlo baraja el orden: la peor baraja cae 34,0 %, sobre el 30 %, aunque el percentil 95 pasa; la caída real fuera de muestra es de 8,92 %, sobre el 6 % de MI_PLAN.md. (3) La regla es en la práctica una compra a mercado tras el cruce a la baja del MACD en sesión asiática; la limit no espera. (4) 2024 pierde y 2023 apenas gana. Aprobar la fase 06 no valida la estrategia: faltan tamaño y riesgo (07) y puesta en marcha (08).
Siguiente paso: fases 07 y 08, que todavía no tienen agente ni skill; se construyen durante el Reto. Antes conviene confirmar con el bróker el spread, el swap y las especificaciones de US30, que son los datos que más mueven el resultado.
