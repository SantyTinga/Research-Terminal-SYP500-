import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Santi Research Terminal", layout="wide", page_icon="📈")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
@st.cache_data(ttl=3600)
def fetch_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    if df.empty: return None
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df.dropna(inplace=True)
    df['EMA20'] = ta.ema(df['Close'], length=20)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    df['EMA200'] = ta.ema(df['Close'], length=200)
    df['RSI14'] = ta.rsi(df['Close'], length=14)
    df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
    
    return df.tail(250)

@st.cache_data(ttl=86400)
def get_fundamentals(ticker):
    try: return yf.Ticker(ticker).info
    except: return {}

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("⚙️ Panel de Control")
    st.markdown("---")
    
    ticker_input = st.text_input("Ticker individual a analizar:", value="NVDA").upper().strip()
    
    st.markdown("### 🤖 IA Integrada")
    api_key = st.text_input("Gemini API Key:", type="password", help="Tu clave de Google AI Studio")
    
    st.markdown("---")
    st.caption("Desarrollado por Santi Tinganelli")

# --- 4. INTERFAZ PRINCIPAL ---
st.title(f"📊 Terminal de Análisis: {ticker_input}" if ticker_input else "📊 Terminal de Análisis")

if ticker_input:
    df = fetch_data(ticker_input)
    info = get_fundamentals(ticker_input)
    
    if df is None:
        st.error(f"❌ No se encontraron datos para {ticker_input}.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Análisis Técnico", "🏢 Auditoría Total (Score)", "🤖 Auditoría Gemini", "🏆 Escáner Global"])
        
        # --- PESTAÑA 1: GRÁFICO ---
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'))
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='yellow', width=1), name='EMA 20'))
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='orange', width=1), name='EMA 50'))
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='purple', width=2), name='EMA 200'))
            
            fig.update_layout(template='plotly_dark', height=600, margin=dict(l=0, r=0, t=30, b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        # --- PESTAÑA 2: AUDITORÍA COMPLETA (100 PUNTOS) ---
        with tab2:
            col1, col2 = st.columns(2)
            
            # -- FUNDAMENTAL (50 pts) --
            with col1:
                st.subheader("🏢 Auditoría Fundamental")
                fund_score = 0
                
                if not info or 'shortName' not in info:
                    st.error("Datos fundamentales no disponibles.")
                else:
                    rev_growth = info.get('revenueGrowth', 0) or 0
                    if rev_growth > 0.10: 
                        fund_score += 10
                        st.write(f"✅ Ingresos altos ({(rev_growth*100):.1f}%) (+10 pts)")
                    elif rev_growth > 0: 
                        fund_score += 5
                        st.write(f"⚠️ Ingresos lentos ({(rev_growth*100):.1f}%) (+5 pts)")
                    else: st.write(f"❌ Ingresos cayendo ({(rev_growth*100):.1f}%) (0 pts)")
                    
                    op_margin = info.get('operatingMargins', 0) or 0
                    if op_margin > 0.20: 
                        fund_score += 15
                        st.write(f"✅ Margen Operativo excelente ({(op_margin*100):.1f}%) (+15 pts)")
                    elif op_margin > 0.10: 
                        fund_score += 8
                        st.write(f"⚠️ Margen Operativo aceptable ({(op_margin*100):.1f}%) (+8 pts)")
                    else: st.write(f"❌ Margen Operativo bajo ({(op_margin*100):.1f}%) (0 pts)")
                    
                    cash = info.get('totalCash', 0) or 0
                    debt = info.get('totalDebt', 0) or 0
                    if cash > debt * 1.2: 
                        fund_score += 15
                        st.write("✅ Caja supera holgadamente deuda (+15 pts)")
                    elif cash > debt: 
                        fund_score += 10
                        st.write("⚠️ Balance estable (+10 pts)")
                    else: st.write("❌ Riesgo solvencia (0 pts)")
                    
                    fwd_pe = info.get('forwardPE', 999) or 999
                    if fwd_pe < 20: 
                        fund_score += 10
                        st.write(f"✅ Valuación atractiva (Fwd P/E {fwd_pe:.1f}) (+10 pts)")
                    elif fwd_pe < 30: 
                        fund_score += 5
                        st.write(f"⚠️ Valuación razonable (Fwd P/E {fwd_pe:.1f}) (+5 pts)")
                    else: 
                        st.write(f"❌ Valuación exigente (Fwd P/E {fwd_pe:.1f}) (0 pts)")
                
                st.markdown("---")
                st.write(f"**Puntaje Fundamental:** {fund_score}/50 pts")
                st.progress(fund_score / 50.0 if fund_score <= 50 else 1.0)
            
            # -- TÉCNICA (50 pts) --
            with col2:
                st.subheader("🎯 Auditoría Técnica")
                precio = df['Close'].iloc[-1]
                ema200 = df['EMA200'].iloc[-1]
                ema50 = df['EMA50'].iloc[-1]
                ema20 = df['EMA20'].iloc[-1]
                rsi = df['RSI14'].iloc[-1]
                rvol = df['RVOL'].iloc[-1]
                
                tech_score = 0
                
                if pd.notna(ema200) and precio > ema200: 
                    tech_score += 15
                    st.write("✅ Precio sobre EMA200 (+15 pts)")
                else: st.write("❌ Precio bajo EMA200 (0 pts)")
                
                if pd.notna(ema20) and pd.notna(ema50) and pd.notna(ema200):
                    if (ema20 > ema50) and (ema50 > ema200): 
                        tech_score += 15
                        st.write("✅ EMAs Alineadas (+15 pts)")
                    else: st.write("❌ EMAs desalineadas (0 pts)")
                
                if pd.notna(rsi):
                    if 35 <= rsi <= 50: 
                        tech_score += 10
                        st.write(f"✅ RSI en pullback ({rsi:.1f}) (+10 pts)")
                    elif rsi < 35: 
                        tech_score += 5
                        st.write(f"⚠️ RSI sobrevendido ({rsi:.1f}) (+5 pts)")
                    else: st.write(f"❌ RSI alto/neutral ({rsi:.1f}) (0 pts)")
                    
                if pd.notna(rvol) and rvol > 1.1:
                    tech_score += 10
                    st.write(f"✅ RVOL alto ({rvol:.2f}x) (+10 pts)")
                else: 
                    st.write(f"❌ RVOL bajo/normal (0 pts)")
                
                st.markdown("---")
                st.write(f"**Puntaje Técnico:** {tech_score}/50 pts")
                st.progress(tech_score / 50.0 if tech_score <= 50 else 1.0)

            # -- TABLA DE MÉTRICAS CLAVE (NUEVO) --
            st.markdown("---")
            st.subheader("📊 Tabla de Métricas Clave (Valuation & Salud)")
            
            # 1. Función para darle un formato lindo a los números (porcentajes, millones, etc)
            def format_val(ind, val):
                if val is None or pd.isna(val): return "N/A"
                if any(x in ind for x in ["Margen", "ROE", "ROA", "Yield"]): return f"{val*100:.2f}%"
                if "Cash Flow" in ind: return f"${val/1e9:.2f} B" if abs(val) > 1e9 else f"${val/1e6:.2f} M"
                return f"{val:.2f}"

            # 2. Armamos la tabla cruda
            data_metrics = [
                ["PER (Forward P/E)", info.get('forwardPE'), "< 20 Bueno | > 30 Caro", info.get('forwardPE')],
                ["ROE", info.get('returnOnEquity'), "> 15% Bueno | < 10% Bajo", info.get('returnOnEquity')],
                ["ROA", info.get('returnOnAssets'), "> 5% Bueno | < 2% Bajo", info.get('returnOnAssets')],
                ["Margen Neto", info.get('profitMargins'), "> 10% Bueno | < 5% Bajo", info.get('profitMargins')],
                ["Margen Operativo", info.get('operatingMargins'), "> 15% Bueno | < 8% Bajo", info.get('operatingMargins')],
                ["Deuda / Patrimonio", info.get('debtToEquity'), "< 100 Bueno | > 200 Riesgo", info.get('debtToEquity')],
                ["Current Ratio (Liquidez)", info.get('currentRatio'), "> 1.5 Bueno | < 1 Peligro", info.get('currentRatio')],
                ["Free Cash Flow", info.get('freeCashflow'), "> 0 Positivo", info.get('freeCashflow')],
                ["EV / EBITDA", info.get('enterpriseToEbitda'), "< 12 Bueno | > 18 Caro", info.get('enterpriseToEbitda')],
                ["BPA / EPS", info.get('trailingEps'), "> 0 Rentable", info.get('trailingEps')],
                ["Dividend Yield", info.get('dividendYield'), "> 2% Bueno", info.get('dividendYield')],
                ["P/BV (Precio/Libros)", info.get('priceToBook'), "< 3 Bueno | > 5 Caro", info.get('priceToBook')]
            ]
            
            df_metrics = pd.DataFrame(data_metrics, columns=["Indicador", "Valor", "Referencia", "Raw"])
            df_metrics["Valor"] = df_metrics.apply(lambda x: format_val(x["Indicador"], x["Raw"]), axis=1)
            
            # 3. Lógica condicional: ¿Es bueno o malo? (Verde o Rojo)
            def highlight_row(row):
                val = row["Raw"]
                ind = row["Indicador"]
                color = ''
                
                if pd.notna(val) and val != "N/A":
                    try:
                        v = float(val)
                        if ind == "PER (Forward P/E)": color = 'background-color: rgba(39, 174, 96, 0.3)' if v < 20 else ('background-color: rgba(192, 57, 43, 0.3)' if v > 30 else '')
                        elif ind == "ROE": color = 'background-color: rgba(39, 174, 96, 0.3)' if v > 0.15 else ('background-color: rgba(192, 57, 43, 0.3)' if v < 0.10 else '')
                        elif ind == "ROA": color = 'background-color: rgba(39, 174, 96, 0.3)' if v > 0.05 else ('background-color: rgba(192, 57, 43, 0.3)' if v < 0.02 else '')
                        elif ind == "Margen Neto": color = 'background-color: rgba(39, 174, 96, 0.3)' if v > 0.10 else ('background-color: rgba(192, 57, 43, 0.3)' if v < 0.05 else '')
                        elif ind == "Margen Operativo": color = 'background-color: rgba(39, 174, 96, 0.3)' if v > 0.15 else ('background-color: rgba(192, 57, 43, 0.3)' if v < 0.08 else '')
                        elif ind == "Deuda / Patrimonio": color = 'background-color: rgba(39, 174, 96, 0.3)' if v < 100 else ('background-color: rgba(192, 57, 43, 0.3)' if v > 200 else '')
                        elif ind == "Current Ratio (Liquidez)": color = 'background-color: rgba(39, 174, 96, 0.3)' if v > 1.5 else ('background-color: rgba(192, 57, 43, 0.3)' if v < 1.0 else '')
                        elif ind == "Free Cash Flow": color = 'background-color: rgba(39, 174, 96, 0.3)' if v > 0 else 'background-color: rgba(192, 57, 43, 0.3)'
                        elif ind == "EV / EBITDA": color = 'background-color: rgba(39, 174, 96, 0.3)' if v < 12 else ('background-color: rgba(192, 57, 43, 0.3)' if v > 18 else '')
                        elif ind == "BPA / EPS": color = 'background-color: rgba(39, 174, 96, 0.3)' if v > 0 else 'background-color: rgba(192, 57, 43, 0.3)'
                        elif ind == "Dividend Yield": color = 'background-color: rgba(39, 174, 96, 0.3)' if v > 0.02 else ''
                        elif ind == "P/BV (Precio/Libros)": color = 'background-color: rgba(39, 174, 96, 0.3)' if v < 3 else ('background-color: rgba(192, 57, 43, 0.3)' if v > 5 else '')
                    except: pass
                        
                # Retornamos el color solo para la columna "Valor" (la posición 1 de nuestro DataFrame visible)
                return pd.Series(['', color, '', ''], index=row.index)

            # 4. Renderizamos aplicando colores y ocultando la columna con datos crudos
            styled_df = df_metrics.style.apply(highlight_row, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True, column_config={"Raw": None})
            
            # -- VEREDICTO FINAL --
            st.markdown("---")
            total_score = tech_score + fund_score
            st.metric("🏆 OPPORTUNITY SCORE TOTAL", f"{total_score} / 100")

        # --- PESTAÑA 3: GEMINI ---
        with tab3:
            st.subheader("🧠 Consultor Cuantitativo AI")
            if not api_key:
                st.warning("⚠️ Ingresá tu API Key de Gemini en la barra lateral.")
            else:
                if st.button("Generar Reporte Cualitativo", type="primary"):
                    with st.spinner("Conectando con Gemini..."):
                        try:
                            prompt = f"Actuá como un analista financiero. Ticker {ticker_input}. Precio ${df['Close'].iloc[-1]:.2f}, RSI {df['RSI14'].iloc[-1]:.1f}, Fwd P/E {info.get('forwardPE', 'N/A')}. Conclusión de riesgo y potencial en 3 párrafos."
                            client = genai.Client(api_key=api_key)
                            response = client.models.generate_content(model='gemini-3.8-flash', contents=prompt, config=types.GenerateContentConfig(temperature=0.2))
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"Error de API: {e}")

        # --- PESTAÑA 4: ESCÁNER GLOBAL ---
        with tab4:
            st.subheader("🏆 Ranking Global Absoluto")
            universo = st.radio("Elegí el universo:", ["S&P 500 (Automático)", "Ingreso Manual"], horizontal=True)
            
            tickers_a_escanear = []
            if universo == "Ingreso Manual":
                lista_ingresada = st.text_area("Tickers:", "GOOGL, MSFT, META, NVDA, YPF")
                tickers_a_escanear = [t.strip().upper() for t in lista_ingresada.split(",") if t.strip()]
            else:
                try:
                    with st.spinner("Extrayendo Wikipedia..."):
                        import requests, io
                        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
                        html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text
                        tickers_a_escanear = pd.read_html(io.StringIO(html))[0]['Symbol'].str.replace('.', '-').tolist()
                        st.success(f"✅ {len(tickers_a_escanear)} empresas del S&P 500 cargadas.")
                except Exception as e:
                    st.error("Falló Wikipedia. Ingresá manual.")
            
            st.markdown("---")
            limite_fundamental = st.slider("Top N empresas para balance:", 5, 50, 15)

            if st.button("Ejecutar Escáner", type="primary", key="btn_scan"):
                if tickers_a_escanear:
                    bar = st.progress(0)
                    txt = st.empty()
                    
                    # FASE 1: TÉCNICA
                    txt.text("Fase 1: Evaluando técnica...")
                    res_tech = []
                    
                    for i, t in enumerate(tickers_a_escanear):
                        df_t = fetch_data(t)
                        if df_t is not None and not df_t.empty:
                            p = df_t['Close'].iloc[-1]
                            e200 = df_t['EMA200'].iloc[-1]
                            e50 = df_t['EMA50'].iloc[-1]
                            e20 = df_t['EMA20'].iloc[-1]
                            r = df_t['RSI14'].iloc[-1]
                            rv = df_t['RVOL'].iloc[-1]
                            
                            ts = 0
                            if pd.notna(e200) and p > e200: ts += 15
                            if pd.notna(e20) and pd.notna(e50) and pd.notna(e200) and (e20 > e50 > e200): ts += 15
                            if pd.notna(r):
                                if 35 <= r <= 50: ts += 10
                                elif r < 35: ts += 5
                            if pd.notna(rv) and rv > 1.1: ts += 10
                            
                            res_tech.append({'Ticker': t, 'Precio': p, 'Tech Score': ts})
                        bar.progress((i + 1) / len(tickers_a_escanear) * 0.5)

                    df_tech = pd.DataFrame(res_tech).sort_values('Tech Score', ascending=False).head(limite_fundamental)
                    
                    # FASE 2: FUNDAMENTAL
                    txt.text("Fase 2: Descargando balances...")
                    res_fin = []
                    
                    for i, row in enumerate(df_tech.iterrows()):
                        d = row[1]
                        t = d['Ticker']
                        inf = get_fundamentals(t)
                        fs = 0
                        
                        rg = inf.get('revenueGrowth', 0) or 0
                        if rg > 0.10: fs += 10
                        elif rg > 0: fs += 5
                        
                        om = inf.get('operatingMargins', 0) or 0
                        if om > 0.20: fs += 15
                        elif om > 0.10: fs += 8
                        
                        c = inf.get('totalCash', 0) or 0
                        db = inf.get('totalDebt', 0) or 0
                        if c > db * 1.2: fs += 15
                        elif c > db: fs += 10
                        
                        pe = inf.get('forwardPE', 999) or 999
                        if pe < 20: fs += 10
                        elif pe < 30: fs += 5
                        
                        res_fin.append({
                            'Ticker': t,
                            'Precio': f"${d['Precio']:.2f}",
                            'Tech Score': d['Tech Score'],
                            'Fund Score': fs,
                            'TOTAL SCORE': d['Tech Score'] + fs
                        })
                        bar.progress(0.5 + ((i + 1) / limite_fundamental) * 0.5)

                    txt.text("¡Completado!")
                    if res_fin:
                        df_r = pd.DataFrame(res_fin).sort_values('TOTAL SCORE', ascending=False).reset_index(drop=True)
                        st.dataframe(df_r.style.background_gradient(subset=['TOTAL SCORE'], cmap='Greens'), use_container_width=True)