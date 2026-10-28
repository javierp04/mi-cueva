//+------------------------------------------------------------------+
//| xauusd_ruptura_donchian_eficiencia_mt5_estrategia.mq5             |
//| Ficha: fichas/xauusd_ruptura_donchian_eficiencia.md                |
//| Plataforma: MetaTrader 5 (Asesor Experto) · XAUUSD · M30 · solo compras |
//| Fecha: 2026-10-28 · generado desde la fase 03 (pseudocódigo)       |
//|                                                                    |
//| SUPUESTOS DE LA FICHA (resumen; la lista completa está en la ficha) |
//|  - rising(x) = valor de la vela cerrada mayor que el de la anterior.|
//|  - %K(7,3) = %K crudo de 7 velas suavizado con media simple de 3.   |
//|  - Eficiencia(50) = |cierre - cierre hace 50| / suma de |cambios|.  |
//|  - Activación = filtro verdadero y disparo pasa de falso a verdadero.|
//|  - ATR(30) = media simple del rango verdadero.                      |
//|  - Una sola posición; con posición abierta no se arman señales.      |
//|  - Sin cierre del viernes: la hipótesis no lo tiene.                |
//| SUPUESTOS DE PLATAFORMA                                              |
//|  P1. La orden stop es VIRTUAL: el robot guarda nivel y vida y compra |
//|      a mercado en el primer tick con Ask >= nivel. Así el lote y el |
//|      stop swing se calculan con el precio real de entrada, como pide |
//|      la ficha (con una orden pendiente real el lote quedaría fijo   |
//|      antes del fill). El fill puede ser algo peor que el nivel.      |
//|  P2. Hora: la regla usa la hora del servidor del bróker (NY+7), la   |
//|      misma de TimeCurrent(): desfase_horas = 0. Si tu bróker usa otra|
//|      hora, pon la diferencia.                                        |
//|  P3. Se pierde el estado (orden viva, vida) si reinicias el robot.   |
//|  P4. Stop level real del bróker: si rechaza el SL, la entrada se     |
//|      descarta (la ficha: entrada con SL demasiado cerca se descarta).|
//|  P5. Costes: los pone el probador (spread del historial del bróker). |
//|      La comisión depende del símbolo en tu bróker: revísala.         |
//+------------------------------------------------------------------+
#property version   "1.00"
#property description "XAUUSD ruptura Donchian con eficiencia (M30, solo compras)"
#include <Trade\Trade.mqh>

CTrade trade;

// ---- PARÁMETROS (mismos números y nombres que la ficha) ----
input int    n_donchian         = 55;       // canal Donchian
input int    n_swing            = 20;       // swing del stop inicial
input int    n_atr              = 30;       // ATR (media simple del rango verdadero)
input int    n_eficiencia       = 50;       // eficiencia
input int    k_periodo          = 7;        // estocástico: periodo
input int    k_suavizado        = 3;        // estocástico: suavizado
input double mult_atr           = 3.0;      // trailing: multiplicador del ATR
input int    vida_orden         = 10;       // vigencia de la orden (velas)
input int    stops_level_puntos = 4;        // distancia mínima (puntos enteros)
input double capital_inicial    = 100000.0; // capital inicial para el riesgo
input double riesgo_pct         = 1.0;      // % de riesgo por operación
input int    apertura_min       = 65;       // 01:05 (minutos desde 00:00, incluido)
input int    cierre_min         = 1439;     // 23:59 (excluido)
input int    desfase_horas      = 0;        // hora del servidor − hora de la regla (P2)
input long   numero_magico      = 20261;    // identifica las operaciones de este robot

MqlRates r[];
datetime ultima_vela = 0;
bool     orden_viva  = false;
double   orden_nivel = 0.0;
int      orden_vida  = 0;
bool     senal       = false;
double   senal_nivel = 0.0;
double   stop_objetivo = 0.0;

int OnInit()
{
   trade.SetExpertMagicNumber(numero_magico);
   ArraySetAsSeries(r, true);
   return INIT_SUCCEEDED;
}

// ---------------------------------------------------------------- utilidades
bool CargarVelas()
{
   int necesarias = MathMax(n_donchian, MathMax(n_eficiencia + 3, n_atr + 2)) + k_periodo + k_suavizado + 30;
   return CopyRates(_Symbol, _Period, 0, necesarias, r) == necesarias;
}

bool MercadoAbierto()
{
   MqlDateTime d;
   TimeToStruct(TimeCurrent() - desfase_horas * 3600, d);
   if(d.day_of_week < 1 || d.day_of_week > 5) return false;
   int minuto = d.hour * 60 + d.min;
   return minuto >= apertura_min && minuto < cierre_min;
}

bool BuscarPosicion(ulong &ticket)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == numero_magico)
      {
         ticket = t;
         return true;
      }
   }
   return false;
}

// ---------------------------------------------------------------- indicadores (velas cerradas: índice 1 en adelante)
double KCrudo(int s)
{
   for(int t = s; t < s + 20; t++)            // rango 0: repito el K crudo anterior
   {
      double ll = r[t].low, hh = r[t].high;
      for(int q = t + 1; q < t + k_periodo; q++)
      {
         ll = MathMin(ll, r[q].low);
         hh = MathMax(hh, r[q].high);
      }
      if(hh - ll > 0) return 100.0 * (r[t].close - ll) / (hh - ll);
   }
   return EMPTY_VALUE;
}

double K(int s)
{
   double suma = 0;
   for(int q = s; q < s + k_suavizado; q++)
   {
      double kc = KCrudo(q);
      if(kc == EMPTY_VALUE) return EMPTY_VALUE;
      suma += kc;
   }
   return suma / k_suavizado;
}

double Eficiencia(int s)
{
   double camino = 0;
   for(int t = s; t < s + n_eficiencia; t++) camino += MathAbs(r[t].close - r[t + 1].close);
   if(camino <= 0) return 0.0;
   return MathAbs(r[s].close - r[s + n_eficiencia].close) / camino;
}

double Atr(int s)
{
   double suma = 0;
   for(int t = s; t < s + n_atr; t++)
   {
      double anterior = r[t + 1].close;
      suma += MathMax(r[t].high - r[t].low, MathMax(MathAbs(r[t].high - anterior), MathAbs(r[t].low - anterior)));
   }
   return suma / n_atr;
}

double MaximoCanal()
{
   double m = r[1].high;
   for(int t = 2; t <= n_donchian; t++) m = MathMax(m, r[t].high);
   return m;
}

double MinimoSwing()
{
   double m = r[1].low;
   for(int t = 2; t <= n_swing; t++) m = MathMin(m, r[t].low);
   return m;
}

// ---------------------------------------------------------------- reglas
// Paso 6 · activación al cierre de la vela (índice 1)
bool Activacion(double &nivel)
{
   double k1 = K(1), k2 = K(2);
   if(k1 == EMPTY_VALUE || k2 == EMPTY_VALUE) return false;
   double e1 = Eficiencia(1), e2 = Eficiencia(2), e3 = Eficiencia(3);
   bool filtro = k1 > k2;
   bool disparo = e1 > e2;
   bool disparo_anterior = e2 > e3;
   if(!(filtro && disparo && !disparo_anterior)) return false;
   nivel = MaximoCanal();      // 55 velas cerradas, incluida la de señal; queda congelado
   return true;
}

// Paso 4 · compra con el precio real, stop swing y lote por riesgo
void Comprar(double ask)
{
   orden_viva = false;
   stop_objetivo = 0.0;
   double sw = MinimoSwing();
   double distancia = ask - sw;
   if((int)MathRound(distancia / _Point) < stops_level_puntos) return;     // entrada descartada

   double tick = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double valor = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(tick <= 0 || valor <= 0) return;
   double lote = (capital_inicial * riesgo_pct / 100.0) / (distancia / tick * valor);
   double paso = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lote = MathFloor(lote / paso + 1e-9) * paso;                            // hacia abajo
   lote = MathMax(MathMin(lote, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX)), SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN));
   lote = NormalizeDouble(lote, (int)MathMax(0, MathRound(-MathLog10(paso))));

   trade.Buy(lote, _Symbol, 0, NormalizeDouble(sw, _Digits), 0);
}

// Pasos 1, 2 y 6 al abrir una vela nueva sin posición
void NuevaVelaFuera(double ask, bool abierto)
{
   double nivel;
   if(Activacion(nivel))                         // Paso 6 · señal de la vela que acaba de cerrar
   {
      senal = true;
      senal_nivel = nivel;
   }
   if(orden_viva) orden_vida++;                  // Paso 1 · vida de la orden

   // Paso 2a · la orden viva se llena antes de cualquier reemplazo
   if(orden_viva && abierto && ask >= orden_nivel)
   {
      senal = false;
      Comprar(ask);
      return;
   }
   // Paso 2b · vencida: ya vivió sus velas y no se llenó
   if(orden_viva && orden_vida > vida_orden && abierto) orden_viva = false;

   // Paso 2c · señal pendiente: reemplaza la orden
   if(senal)
   {
      if(abierto)
      {
         orden_viva = false;
         if(ask >= senal_nivel)
            Comprar(ask);                        // ya está en el nivel o más allá: a mercado
         else if((int)MathRound((senal_nivel - ask) / _Point) >= stops_level_puntos)
         {
            orden_viva = true;
            orden_nivel = senal_nivel;
            orden_vida = 1;                      // esta vela es la vela de colocación
         }
      }
      senal = false;                             // con mercado cerrado la señal se pierde
   }
}

// Paso 5b · trailing al cierre de la vela (índice 1)
void CalcularTrailing(ulong ticket)
{
   double objetivo = r[1].close - mult_atr * Atr(1);
   if(!PositionSelectByTicket(ticket)) return;
   if(objetivo > PositionGetDouble(POSITION_SL) && objetivo > stop_objetivo) stop_objetivo = objetivo;
}

// El stop nuevo se recuerda y se reintenta en cada tick con el mercado abierto
void AplicarStopObjetivo(ulong ticket, bool abierto)
{
   if(stop_objetivo <= 0 || !abierto) return;
   if(!PositionSelectByTicket(ticket)) return;
   if(stop_objetivo <= PositionGetDouble(POSITION_SL)) { stop_objetivo = 0.0; return; }
   if(SymbolInfoDouble(_Symbol, SYMBOL_BID) <= stop_objetivo)
   {
      trade.PositionClose(ticket);               // cruzó el objetivo antes de confirmarse: cierra a mercado
      stop_objetivo = 0.0;
      return;
   }
   if(trade.PositionModify(ticket, NormalizeDouble(stop_objetivo, _Digits), 0)) stop_objetivo = 0.0;
}

void OnTick()
{
   datetime vela = iTime(_Symbol, _Period, 0);
   bool nueva = (vela != ultima_vela);
   bool abierto = MercadoAbierto();
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   ulong ticket = 0;
   bool dentro = BuscarPosicion(ticket);

   if(nueva)
   {
      if(!CargarVelas()) return;
      ultima_vela = vela;
      if(dentro) CalcularTrailing(ticket);
      else       NuevaVelaFuera(ask, abierto);
      dentro = BuscarPosicion(ticket);
   }

   if(dentro)
   {
      AplicarStopObjetivo(ticket, abierto);
      return;
   }
   stop_objetivo = 0.0;

   // Paso 3 · durante la vela: la orden viva se llena al alcanzar el nivel; vencida se borra
   if(orden_viva && abierto)
   {
      if(ask >= orden_nivel) Comprar(ask);
      else if(orden_vida > vida_orden) orden_viva = false;
   }
}
