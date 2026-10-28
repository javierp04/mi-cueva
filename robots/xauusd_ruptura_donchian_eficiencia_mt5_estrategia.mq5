//+------------------------------------------------------------------+
//| xauusd_ruptura_donchian_eficiencia_mt5_estrategia.mq5             |
//| Ficha: fichas/xauusd_ruptura_donchian_eficiencia.md                |
//| Plataforma: MetaTrader 5 (Asesor Experto) · XAUUSD · M30 · solo compras |
//| Fecha: 2026-10-28 (v3: orden stop real repuesta en cada vela) · generado desde la fase 03 |
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
//|  P1. La orden es una BUY STOP real (GTC, sin expiración del bróker): |
//|      se pide en el primer tick de la vela siguiente a la señal y se  |
//|      llena en el nivel (o en la apertura si hay gap). El robot la    |
//|      borra al vencer sus 10 velas.                                   |
//|  P2. El stop swing se lee en la vela de la ENTRADA y el lote sale de |
//|      él. Una orden pendiente no puede cambiar de lote, así que en    |
//|      cada vela nueva la orden se REPONE (se borra y se pide otra con |
//|      el mismo nivel y la misma vida) con el swing y el lote de esa   |
//|      vela, como hace el motor del trader. Un gap en la apertura puede|
//|      dejar el lote algo distinto del que saldría con el precio real. |
//|  P3. Hora: la regla usa la hora del servidor del bróker (NY+7), la   |
//|      misma de TimeCurrent(): desfase_horas = 0.                      |
//|  P4. Si reinicias el robot, la orden pendiente sigue en el bróker y  |
//|      se recupera su vida por la hora en que se colocó.               |
//|  P5. Costes: los pone el Probador/bróker (spread, swap). La comisión |
//|      depende del símbolo en tu bróker: revísala.                     |
//+------------------------------------------------------------------+
#property version   "3.00"
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
input int    desfase_horas      = 0;        // hora del servidor − hora de la regla (P3)
input long   numero_magico      = 20261;    // identifica las operaciones de este robot

MqlRates r[];
datetime ultima_vela   = 0;
ulong    orden_ticket  = 0;       // orden BUY STOP viva (0 = ninguna)
double   orden_nivel   = 0.0;
int      orden_vida    = 0;
bool     senal         = false;
double   senal_nivel   = 0.0;
ulong    posicion_lista = 0;      // posición cuyo stop swing ya se leyó en su vela de entrada
double   stop_objetivo = 0.0;     // stop que se quiere aplicar y se reintenta en cada tick
// Contadores de diagnóstico (se imprimen al terminar el test; se pueden borrar cuando todo funcione)
int c_velas = 0, c_sin_velas = 0, c_senales = 0, c_cerrado = 0, c_ordenes = 0, c_rechazos = 0, c_mercado = 0;

int OnInit()
{
   if(_Period != PERIOD_M30)       // la regla es de velas de 30 minutos
   {
      Print("Este robot es para M30. Gráfico actual: ", EnumToString(_Period));
      return INIT_FAILED;
   }
   trade.SetExpertMagicNumber(numero_magico);
   trade.SetTypeFillingBySymbol(_Symbol);       // el tipo de llenado que acepta el bróker para este símbolo
   trade.SetDeviationInPoints(30);              // desvío máximo en la compra a mercado (igual que el motor del trader)
   ArraySetAsSeries(r, true);
   for(int i = OrdersTotal() - 1; i >= 0; i--)     // P4: recuperar una orden que ya estaba viva
   {
      ulong t = OrderGetTicket(i);
      if(t == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == numero_magico
         && OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_STOP)
      {
         orden_ticket = t;
         orden_nivel = OrderGetDouble(ORDER_PRICE_OPEN);
         orden_vida = iBarShift(_Symbol, _Period, (datetime)OrderGetInteger(ORDER_TIME_SETUP)) + 1;
         break;
      }
   }
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

bool HayOrden()
{
   if(orden_ticket == 0) return false;
   if(OrderSelect(orden_ticket)) return true;
   orden_ticket = 0;
   return false;
}

// Borra la orden y confirma que ya no está viva
bool BorrarOrden()
{
   if(!trade.OrderDelete(orden_ticket)) return false;
   if(OrderSelect(orden_ticket)) return false;
   orden_ticket = 0;
   return true;
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

double MinimoSwing()           // las n_swing velas cerradas anteriores a la vela en curso
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

// Lote = riesgo / distancia al stop, hacia abajo al paso del símbolo, entre el mínimo y el máximo
double LoteDeRiesgo(double distancia)
{
   double tick = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double valor = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(tick <= 0 || valor <= 0 || distancia <= 0) return 0.0;
   double lote = (capital_inicial * riesgo_pct / 100.0) / (distancia / tick * valor);
   double paso = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lote = MathFloor(lote / paso + 1e-9) * paso;
   lote = MathMax(MathMin(lote, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX)), SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN));
   return NormalizeDouble(lote, (int)MathMax(0, MathRound(-MathLog10(paso))));
}

// Ya está en el nivel o más allá: entrada a mercado, con el precio real
void ComprarMercado(double ask)
{
   double sw = MinimoSwing();
   double distancia = ask - sw;
   if((int)MathRound(distancia / _Point) < stops_level_puntos) return;      // entrada descartada
   double lote = LoteDeRiesgo(distancia);
   if(lote <= 0) return;
   c_mercado++;
   if(!trade.Buy(lote, _Symbol, 0, NormalizeDouble(sw, _Digits), 0))
      Print("Compra a mercado rechazada: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription());
}

// Pide la orden BUY STOP una sola vez
void ColocarOrden(double nivel, int vida)
{
   double sw = MinimoSwing();
   double distancia = nivel - sw;
   if((int)MathRound(distancia / _Point) < stops_level_puntos) return;
   double lote = LoteDeRiesgo(distancia);
   if(lote <= 0) return;
   if(trade.BuyStop(lote, NormalizeDouble(nivel, _Digits), _Symbol, NormalizeDouble(sw, _Digits), 0, ORDER_TIME_GTC, 0))
   {
      orden_ticket = trade.ResultOrder();
      c_ordenes++;
      orden_nivel = nivel;
      orden_vida = vida;
   }
   else
   {
      c_rechazos++;
      Print("Orden BUY STOP rechazada en ", DoubleToString(nivel, _Digits), ": ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription());
   }
}

// El stop swing se lee en cada vela hasta que la orden se llena: se repone la orden con el mismo nivel y la misma vida
void ReponerOrden(double ask)
{
   if(orden_vida > vida_orden) return;
   if((int)MathRound((orden_nivel - ask) / _Point) < stops_level_puntos) return;   // muy cerca del precio: se deja la que está
   double nivel = orden_nivel;
   int vida = orden_vida;
   if(!BorrarOrden()) return;
   ColocarOrden(nivel, vida);
}

// Pasos 1, 2 y 6 al abrir una vela nueva sin posición
void NuevaVelaFuera(double ask, bool abierto)
{
   double nivel;
   if(Activacion(nivel))                         // Paso 6 · señal de la vela que acaba de cerrar
   {
      senal = true;
      senal_nivel = nivel;
      c_senales++;
   }
   if(HayOrden()) orden_vida++;                  // Paso 1 · vida de la orden

   // Paso 2b · vencida: el fill va primero (lo hace el bróker); si sigue viva, se borra
   if(HayOrden() && orden_vida > vida_orden && abierto) BorrarOrden();

   // Paso 2c · señal pendiente: reemplaza la orden
   if(senal)
   {
      if(abierto)
      {
         bool libre = true;
         if(HayOrden()) libre = BorrarOrden();   // el borrado se confirma antes de colocar la nueva
         if(libre)
         {
            if(ask >= senal_nivel)
               ComprarMercado(ask);              // ya está en el nivel o más allá: a mercado
            else if((int)MathRound((senal_nivel - ask) / _Point) >= stops_level_puntos)
               ColocarOrden(senal_nivel, 1);      // esta vela es la vela de colocación
         }
      }
      else c_cerrado++;
      senal = false;                             // con mercado cerrado la señal se pierde
   }
   else if(HayOrden() && abierto)
      ReponerOrden(ask);                         // paso 2d · sin señal nueva: se actualiza el stop swing y el lote
}

// Se lee el stop swing en la vela de la ENTRADA, con el precio real de entrada
void PrepararPosicion(ulong ticket)
{
   posicion_lista = ticket;
   if(!PositionSelectByTicket(ticket)) return;
   if((datetime)PositionGetInteger(POSITION_TIME) < iTime(_Symbol, _Period, 0)) return;   // posición anterior (reinicio): no se toca su stop
   double entrada = PositionGetDouble(POSITION_PRICE_OPEN);
   double sw = MinimoSwing();
   if((int)MathRound((entrada - sw) / _Point) < stops_level_puntos)
   {
      trade.PositionClose(ticket);               // entrada descartada
      return;
   }
   stop_objetivo = sw;
}

// Paso 5b · trailing al cierre de la vela (índice 1): ATR de la vela recién cerrada
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
   if(MathAbs(stop_objetivo - PositionGetDouble(POSITION_SL)) < _Point / 2) { stop_objetivo = 0.0; return; }
   if(SymbolInfoDouble(_Symbol, SYMBOL_BID) <= stop_objetivo)
   {
      trade.PositionClose(ticket);               // cruzó el objetivo antes de confirmarse: cierra a mercado
      stop_objetivo = 0.0;
      return;
   }
   if(trade.PositionModify(ticket, NormalizeDouble(stop_objetivo, _Digits), 0)) stop_objetivo = 0.0;
}

void OnDeinit(const int motivo)
{
   Print("Resumen: velas ", c_velas, " · sin velas suficientes ", c_sin_velas, " · señales ", c_senales,
         " · señales con mercado cerrado ", c_cerrado, " · órdenes colocadas ", c_ordenes,
         " · órdenes rechazadas ", c_rechazos, " · compras a mercado ", c_mercado);
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
      if(!CargarVelas()) { c_sin_velas++; return; }
      ultima_vela = vela;
      c_velas++;
   }

   if(dentro)
   {
      orden_ticket = 0;
      senal = false;
      if(ticket != posicion_lista) PrepararPosicion(ticket);    // recién llenada: el trailing empieza al cierre de esta vela
      else if(nueva)               CalcularTrailing(ticket);
      AplicarStopObjetivo(ticket, abierto);
      return;
   }
   posicion_lista = 0;
   stop_objetivo = 0.0;

   if(nueva) NuevaVelaFuera(ask, abierto);

   // Paso 3 · durante la vela: una orden vencida que no se pudo borrar se reintenta en cada tick con mercado abierto
   if(HayOrden() && abierto && orden_vida > vida_orden) BorrarOrden();
}
