import streamlit as st
import pandas as pd
import plotly.express as px
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="Cortex AI FinOps Monitor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_snowflake_session():
    try:
        return get_active_session()
    except:
        st.error("Unable to connect to Snowflake.")
        return None

session = get_snowflake_session()

with st.sidebar:
    st.title("🤖 Cortex AI FinOps")
    days_back = st.slider("Período de Análise (dias)", 7, 90, 30)
    st.markdown("---")
    st.markdown("""
    **Monitoramento de IA:**
    - 📊 Créditos & Tokens
    - 💻 Cortex Code
    - 🧠 Modelos & Funções
    - 🤖 Agentes & Analyst
    - 📝 Prompts & Educação
    - ⚡ Otimização & ROI
    """)

st.header("🤖 Cortex AI — Inteligência Artificial FinOps")
st.markdown("Monitoramento completo do uso de IA na plataforma Snowflake: modelos, tokens, créditos, eficiência e educação de usuários.")

if session is None:
    st.stop()

try:
    df_ai_summary = session.sql(f"""
        SELECT 'Cortex Code CLI' AS service, SUM(TOKEN_CREDITS) AS credits, SUM(TOKENS) AS tokens, COUNT(*) AS requests
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
        WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        UNION ALL
        SELECT 'Cortex Code Desktop', SUM(TOKEN_CREDITS), SUM(TOKENS), COUNT(*)
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_DESKTOP_USAGE_HISTORY
        WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        UNION ALL
        SELECT 'Cortex Code Snowsight', SUM(TOKEN_CREDITS), SUM(TOKENS), COUNT(*)
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
        WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        UNION ALL
        SELECT 'Cortex AI Functions', SUM(CREDITS), NULL, COUNT(*)
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
        WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        UNION ALL
        SELECT 'Cortex Search', SUM(CREDITS), NULL, COUNT(*)
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_SERVING_USAGE_HISTORY
        WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        UNION ALL
        SELECT 'Cortex Agent', SUM(TOKEN_CREDITS), SUM(TOKENS), COUNT(*)
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
        WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        UNION ALL
        SELECT 'Cortex Analyst', SUM(CREDITS), NULL, COUNT(*)
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
        WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        UNION ALL
        SELECT 'Cortex REST API', NULL, SUM(TOKENS), COUNT(*)
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
        WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        ORDER BY credits DESC NULLS LAST
    """).to_pandas()

    total_ai_credits = df_ai_summary['CREDITS'].sum() if not df_ai_summary.empty else 0
    total_ai_tokens = df_ai_summary['TOKENS'].sum() if not df_ai_summary.empty else 0
    total_ai_requests = df_ai_summary['REQUESTS'].sum() if not df_ai_summary.empty else 0

    df_cache_eff = session.sql(f"""
        SELECT
            SUM(f.value:cache_read_input::NUMBER) AS cache_read,
            SUM(f.value:cache_write_input::NUMBER) AS cache_write,
            SUM(f.value:input::NUMBER) AS fresh_input,
            SUM(f.value:output::NUMBER) AS output_tokens,
            ROUND(SUM(f.value:cache_read_input::NUMBER) * 100.0 /
                NULLIF(SUM(f.value:cache_read_input::NUMBER) +
                       SUM(f.value:cache_write_input::NUMBER) +
                       SUM(f.value:input::NUMBER), 0), 1) AS cache_hit_rate_pct
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY,
            LATERAL FLATTEN(INPUT => TOKENS_GRANULAR) f
        WHERE f.key = 'claude-opus-4-6'
            AND USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
    """).to_pandas()

    cache_hit_rate = float(df_cache_eff['CACHE_HIT_RATE_PCT'].iloc[0] or 0) if not df_cache_eff.empty else 0
    cache_read_tokens = float(df_cache_eff['CACHE_READ'].iloc[0] or 0) if not df_cache_eff.empty else 0
    credits_saved_estimate = cache_read_tokens * (0.00000275 - 0.00000028)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Créditos AI", f"{total_ai_credits:,.2f}")
    with col2:
        if total_ai_tokens and total_ai_tokens > 1_000_000_000:
            st.metric("Total Tokens", f"{total_ai_tokens/1_000_000_000:,.2f}B")
        elif total_ai_tokens and total_ai_tokens > 1_000_000:
            st.metric("Total Tokens", f"{total_ai_tokens/1_000_000:,.1f}M")
        else:
            st.metric("Total Tokens", f"{total_ai_tokens:,.0f}")
    with col3:
        st.metric("Total Requests AI", f"{total_ai_requests:,.0f}")
    with col4:
        st.metric("Cache Hit Rate", f"{cache_hit_rate}%")
    with col5:
        st.metric("Créditos Economizados", f"{credits_saved_estimate:,.0f}")

    st.divider()

    ai_tab1, ai_tab2, ai_tab3, ai_tab4, ai_tab5, ai_tab6 = st.tabs([
        "📊 Visão Geral", "💻 Cortex Code", "🧠 Modelos & Funções",
        "🤖 Agentes & Analyst", "📝 Prompts & Educação", "⚡ Otimização"
    ])

    with ai_tab1:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Distribuição de Créditos por Serviço AI")
            df_pie = df_ai_summary[df_ai_summary['CREDITS'] > 0].copy()
            if not df_pie.empty:
                fig_pie = px.pie(
                    df_pie, values='CREDITS', names='SERVICE',
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hole=0.4
                )
                fig_pie.update_layout(height=400, margin=dict(t=20, b=20))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Sem dados de créditos AI no período selecionado.")

        with col_right:
            st.markdown("#### Créditos por Modelo de IA")
            df_models = session.sql(f"""
                SELECT MODEL_NAME, SUM(CREDITS) AS total_credits, COUNT(*) AS requests
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
                WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
                    AND MODEL_NAME IS NOT NULL
                GROUP BY MODEL_NAME
                UNION ALL
                SELECT MODEL_NAME, SUM(TOKEN_CREDITS) AS total_credits, COUNT(*) AS requests
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY
                WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
                    AND MODEL_NAME IS NOT NULL AND MODEL_NAME != ''
                GROUP BY MODEL_NAME
                ORDER BY total_credits DESC
            """).to_pandas()

            if not df_models.empty:
                fig_models = px.bar(
                    df_models.head(10), x='TOTAL_CREDITS', y='MODEL_NAME',
                    orientation='h', color='TOTAL_CREDITS',
                    color_continuous_scale='Blues'
                )
                fig_models.update_layout(
                    height=400, margin=dict(t=20, b=20),
                    yaxis={'categoryorder': 'total ascending'},
                    showlegend=False
                )
                st.plotly_chart(fig_models, use_container_width=True)
            else:
                st.info("Sem dados de modelos no período selecionado.")

        st.markdown("#### Tendência Diária de Consumo AI")
        df_trend = session.sql(f"""
            SELECT DATE_TRUNC('day', USAGE_TIME::TIMESTAMP_NTZ)::DATE AS dt,
                   SUM(TOKEN_CREDITS) AS credits, COUNT(*) AS requests
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
            WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
            GROUP BY 1
            ORDER BY 1
        """).to_pandas()

        if not df_trend.empty:
            fig_trend = px.area(
                df_trend, x='DT', y='CREDITS',
                labels={'DT': 'Data', 'CREDITS': 'Créditos'},
                color_discrete_sequence=['#636EFA']
            )
            fig_trend.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig_trend, use_container_width=True)

    with ai_tab2:
        st.markdown("#### Produtividade com Cortex Code")

        df_code_interfaces = session.sql(f"""
            SELECT 'CLI' AS interface, COUNT(*) AS requests, SUM(TOKEN_CREDITS) AS credits, SUM(TOKENS) AS tokens
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
            WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
            UNION ALL
            SELECT 'Desktop', COUNT(*), SUM(TOKEN_CREDITS), SUM(TOKENS)
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_DESKTOP_USAGE_HISTORY
            WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
            UNION ALL
            SELECT 'Snowsight', COUNT(*), SUM(TOKEN_CREDITS), SUM(TOKENS)
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
            WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        """).to_pandas()

        col1, col2, col3 = st.columns(3)
        for i, row in df_code_interfaces.iterrows():
            with [col1, col2, col3][i]:
                st.metric(
                    f"{row['INTERFACE']}",
                    f"{int(row['REQUESTS']):,} requests",
                    f"{row['CREDITS']:,.2f} créditos"
                )

        st.divider()
        st.markdown("#### Eficiência de Cache — Tokens Breakdown")
        st.markdown("""
> **Cache Read** = tokens reutilizados de contexto anterior (muito mais barato)
> **Cache Write** = tokens novos sendo armazenados no cache
> **Output** = tokens gerados pela IA como resposta
        """)

        df_cache_detail = session.sql(f"""
            SELECT
                DATE_TRUNC('day', h.USAGE_TIME::TIMESTAMP_NTZ)::DATE AS dt,
                SUM(f.value:cache_read_input::NUMBER) AS cache_read,
                SUM(f.value:cache_write_input::NUMBER) AS cache_write,
                SUM(f.value:output::NUMBER) AS output_tokens
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY h,
                LATERAL FLATTEN(INPUT => h.TOKENS_GRANULAR) f
            WHERE f.key = 'claude-opus-4-6'
                AND h.USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
            GROUP BY 1
            ORDER BY 1
        """).to_pandas()

        if not df_cache_detail.empty:
            df_melt = df_cache_detail.melt(id_vars=['DT'],
                value_vars=['CACHE_READ', 'CACHE_WRITE', 'OUTPUT_TOKENS'],
                var_name='Tipo', value_name='Tokens')
            df_melt['Tipo'] = df_melt['Tipo'].map({
                'CACHE_READ': 'Cache Read (economia)',
                'CACHE_WRITE': 'Cache Write (novo contexto)',
                'OUTPUT_TOKENS': 'Output (resposta IA)'
            })
            fig_cache = px.bar(
                df_melt, x='DT', y='Tokens', color='Tipo',
                barmode='stack',
                color_discrete_map={
                    'Cache Read (economia)': '#2ECC71',
                    'Cache Write (novo contexto)': '#F39C12',
                    'Output (resposta IA)': '#3498DB'
                }
            )
            fig_cache.update_layout(height=400, margin=dict(t=20, b=20))
            st.plotly_chart(fig_cache, use_container_width=True)

            total_cache_read = df_cache_detail['CACHE_READ'].sum()
            total_cache_write = df_cache_detail['CACHE_WRITE'].sum()
            total_output = df_cache_detail['OUTPUT_TOKENS'].sum()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cache Read (reutilizado)", f"{total_cache_read/1_000_000:,.0f}M tokens")
            with col2:
                pct = total_cache_read * 100 / (total_cache_read + total_cache_write) if (total_cache_read + total_cache_write) > 0 else 0
                st.metric("Taxa de Reutilização", f"{pct:.1f}%")
            with col3:
                st.metric("Output Gerado", f"{total_output/1_000_000:,.1f}M tokens")

            st.success(f"💡 **Economia com Cache:** {pct:.0f}% dos tokens de input foram reutilizados do cache, custando ~10x menos que tokens novos.")

    with ai_tab3:
        st.markdown("#### Modelos de IA Mais Utilizados")

        df_all_models = session.sql(f"""
            SELECT MODEL_NAME, FUNCTION_NAME,
                   COUNT(*) AS requests, SUM(CREDITS) AS credits
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
            WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
                AND MODEL_NAME IS NOT NULL
            GROUP BY MODEL_NAME, FUNCTION_NAME
            ORDER BY credits DESC
        """).to_pandas()

        if not df_all_models.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Por Créditos**")
                fig_m1 = px.bar(
                    df_all_models.head(8), x='MODEL_NAME', y='CREDITS',
                    color='FUNCTION_NAME',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_m1.update_layout(height=350, margin=dict(t=10, b=10))
                st.plotly_chart(fig_m1, use_container_width=True)

            with col2:
                st.markdown("**Por Requests**")
                fig_m2 = px.bar(
                    df_all_models.head(8), x='MODEL_NAME', y='REQUESTS',
                    color='FUNCTION_NAME',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_m2.update_layout(height=350, margin=dict(t=10, b=10))
                st.plotly_chart(fig_m2, use_container_width=True)

        st.divider()
        st.markdown("#### Funções AI Chamadas")
        df_functions = session.sql(f"""
            SELECT FUNCTION_NAME AS "Função", MODEL_NAME AS "Modelo",
                   COUNT(*) AS "Requests",
                   ROUND(SUM(CREDITS), 4) AS "Créditos",
                   ROUND(SUM(CREDITS) / NULLIF(COUNT(*), 0), 6) AS "Custo/Request"
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
            WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
            GROUP BY FUNCTION_NAME, MODEL_NAME
            ORDER BY "Créditos" DESC
        """).to_pandas()

        if not df_functions.empty:
            st.dataframe(df_functions, use_container_width=True, hide_index=True)

        st.markdown("#### Referência: Custo por 1000 Tokens (Input)")
        st.markdown("""
| Modelo | Custo/1K tokens (input) | Melhor para |
|--------|------------------------|-------------|
| `claude-opus-4-6` | ~$0.015 | Tarefas complexas, código longo |
| `claude-sonnet-4-6` | ~$0.003 | Equilíbrio custo/qualidade |
| `llama3.1-70b` | ~$0.00088 | Tarefas simples, alto volume |
| `llama3.1-8b` | ~$0.00019 | Classificação, extração básica |
| `snowflake-arctic-embed` | ~$0.00003 | Embeddings (busca semântica) |
        """)

    with ai_tab4:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Cortex Agents")
            df_agents = session.sql(f"""
                SELECT
                    COALESCE(AGENT_NAME, 'Ad-hoc Agent') AS agent_name,
                    COALESCE(AGENT_DATABASE_NAME, '-') AS database_name,
                    COUNT(*) AS requests,
                    ROUND(SUM(TOKEN_CREDITS), 4) AS credits,
                    SUM(TOKENS) AS tokens
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
                WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
                GROUP BY AGENT_NAME, AGENT_DATABASE_NAME
                ORDER BY credits DESC
            """).to_pandas()

            if not df_agents.empty:
                st.dataframe(df_agents, use_container_width=True, hide_index=True)
                fig_agents = px.bar(
                    df_agents, x='AGENT_NAME', y='CREDITS',
                    color='AGENT_NAME',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_agents.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_agents, use_container_width=True)
            else:
                st.info("Sem uso de Cortex Agents no período.")

        with col_right:
            st.markdown("#### Cortex Analyst")
            df_analyst = session.sql(f"""
                SELECT
                    USERNAME AS user_name,
                    COUNT(*) AS requests,
                    ROUND(SUM(CREDITS), 4) AS credits,
                    SUM(REQUEST_COUNT) AS total_questions
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
                WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
                GROUP BY USERNAME
                ORDER BY credits DESC
            """).to_pandas()

            if not df_analyst.empty:
                st.dataframe(df_analyst, use_container_width=True, hide_index=True)
                total_analyst_credits = df_analyst['CREDITS'].sum()
                total_analyst_questions = df_analyst['TOTAL_QUESTIONS'].sum()
                st.metric("Total Perguntas ao Analyst", f"{int(total_analyst_questions):,}")
                if total_analyst_questions > 0:
                    st.metric("Custo Médio/Pergunta", f"{total_analyst_credits/total_analyst_questions:.4f} créditos")
            else:
                st.info("Sem uso de Cortex Analyst no período.")

    with ai_tab5:
        st.markdown("#### Análise de Prompts dos Usuários")
        st.markdown("Entenda como os usuários estão interagindo com a IA para educar e otimizar o uso.")

        st.markdown("##### Top 10 Queries AI Mais Caras (por duração)")
        df_expensive = session.sql(f"""
            SELECT
                QUERY_ID,
                USER_NAME,
                LEFT(QUERY_TEXT, 200) AS query_preview,
                TOTAL_ELAPSED_TIME/1000 AS duration_sec,
                START_TIME::DATE AS query_date
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE (QUERY_TEXT ILIKE '%%CORTEX.COMPLETE%%'
                   OR QUERY_TEXT ILIKE '%%AI_COMPLETE%%'
                   OR QUERY_TEXT ILIKE '%%AI_EMBED%%')
                AND START_TIME >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
            ORDER BY TOTAL_ELAPSED_TIME DESC
            LIMIT 10
        """).to_pandas()

        if not df_expensive.empty:
            st.dataframe(df_expensive, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("##### Distribuição de Tamanho de Prompts (tokens input)")
        df_prompt_sizes = session.sql(f"""
            SELECT
                CASE
                    WHEN f.value:input::NUMBER + COALESCE(f.value:cache_write_input::NUMBER, 0) < 1000 THEN '< 1K tokens'
                    WHEN f.value:input::NUMBER + COALESCE(f.value:cache_write_input::NUMBER, 0) < 10000 THEN '1K-10K tokens'
                    WHEN f.value:input::NUMBER + COALESCE(f.value:cache_write_input::NUMBER, 0) < 50000 THEN '10K-50K tokens'
                    WHEN f.value:input::NUMBER + COALESCE(f.value:cache_write_input::NUMBER, 0) < 100000 THEN '50K-100K tokens'
                    ELSE '> 100K tokens'
                END AS size_bucket,
                COUNT(*) AS requests
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY,
                LATERAL FLATTEN(INPUT => TOKENS_GRANULAR) f
            WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
            GROUP BY 1
            ORDER BY
                CASE size_bucket
                    WHEN '< 1K tokens' THEN 1
                    WHEN '1K-10K tokens' THEN 2
                    WHEN '10K-50K tokens' THEN 3
                    WHEN '50K-100K tokens' THEN 4
                    ELSE 5
                END
        """).to_pandas()

        if not df_prompt_sizes.empty:
            fig_sizes = px.bar(
                df_prompt_sizes, x='SIZE_BUCKET', y='REQUESTS',
                color='SIZE_BUCKET',
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig_sizes.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_sizes, use_container_width=True)

        st.divider()
        st.markdown("##### 📚 Boas Práticas para Uso Eficiente de IA")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
**✅ FAZER:**
- Ser específico e direto no prompt
- Usar structured output (JSON schema)
- Aproveitar o cache (manter contexto incremental)
- Escolher o modelo certo para a tarefa:
  - Tarefas simples → `llama3.1-8b`
  - Análise moderada → `claude-sonnet`
  - Código complexo → `claude-opus`
- Usar embeddings para busca semântica
- Definir o formato de resposta esperado
            """)

        with col2:
            st.markdown("""
**❌ EVITAR:**
- Repetir todo o contexto a cada pergunta
- Usar modelo premium para tarefas triviais
- Prompts vagos ("me ajuda com isso")
- Enviar documentos inteiros sem resumir
- Ignorar o cache (cada nova sessão = cache frio)
- Pedir múltiplas tarefas em um único prompt longo
            """)

        st.info("""
💡 **Dica de Ouro:** Perguntas educadas como "por favor" e "será que você consegue" **não melhoram a resposta**
mas adicionam tokens extras. Seja direto: "Liste os top 5 clientes por receita" é mais eficiente que
"Olá! Será que você poderia, por favor, me listar os top 5 clientes por receita? Muito obrigado!".
A economia pode parecer pequena, mas em escala (milhares de requests) faz diferença.
        """)

        if cache_hit_rate and cache_hit_rate > 80:
            st.success(f"🎯 **Excelente!** Taxa de cache de {cache_hit_rate}% indica uso eficiente de contexto incremental.")
        elif cache_hit_rate and cache_hit_rate > 50:
            st.warning(f"⚠️ Taxa de cache de {cache_hit_rate}%. Considere manter sessões mais longas para aproveitar o cache.")
        elif cache_hit_rate:
            st.error(f"🚨 Taxa de cache de apenas {cache_hit_rate}%. Muitas sessões curtas descartam contexto.")

    with ai_tab6:
        st.markdown("#### Recomendações de Otimização")

        df_daily_avg = session.sql("""
            SELECT
                ROUND(AVG(daily_credits), 4) AS avg_daily_credits,
                ROUND(AVG(daily_credits) * 30, 2) AS projected_monthly
            FROM (
                SELECT DATE_TRUNC('day', USAGE_TIME::TIMESTAMP_NTZ)::DATE AS dt,
                       SUM(TOKEN_CREDITS) AS daily_credits
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
                WHERE USAGE_TIME::TIMESTAMP_NTZ >= DATEADD('day', -30, CURRENT_TIMESTAMP())
                GROUP BY 1
            )
        """).to_pandas()

        col1, col2, col3 = st.columns(3)
        with col1:
            if not df_daily_avg.empty:
                st.metric("Média Diária (Cortex Code)", f"{df_daily_avg['AVG_DAILY_CREDITS'].iloc[0]:,.2f} créditos")
        with col2:
            if not df_daily_avg.empty:
                st.metric("Projeção Mensal", f"{df_daily_avg['PROJECTED_MONTHLY'].iloc[0]:,.2f} créditos")
        with col3:
            st.metric("Custo/1K Tokens (média)", f"~$0.001")

        st.divider()
        st.markdown("##### 🎯 Recomendações Automáticas")

        recommendations = []

        if 'df_all_models' in dir() and not df_all_models.empty:
            opus_usage = df_all_models[df_all_models['MODEL_NAME'].str.contains('opus', case=False, na=False)]
            if not opus_usage.empty and opus_usage['REQUESTS'].sum() > 10:
                recommendations.append(
                    "**Modelo Premium em Alto Volume:** claude-opus-4-6 foi usado " +
                    f"{int(opus_usage['REQUESTS'].sum())} vezes. Para tarefas simples, " +
                    "considere claude-sonnet (3-5x mais barato) ou llama3.1-70b (10x mais barato)."
                )

        if cache_hit_rate and cache_hit_rate > 85:
            recommendations.append(
                f"**Cache Otimizado ✅:** Taxa de {cache_hit_rate}% é excelente. "
                "O contexto está sendo bem reutilizado entre requests."
            )

        if total_ai_credits and total_ai_credits > 100:
            recommendations.append(
                f"**Volume Significativo:** Com {total_ai_credits:,.0f} créditos gastos, "
                "considere Provisioned Throughput para cargas previsíveis (desconto de até 50%)."
            )

        recommendations.append(
            "**Embeddings Eficientes:** Use `snowflake-arctic-embed-m-v1.5` para busca semântica — "
            "custa ~100x menos que modelos generativos e é otimizado para Snowflake."
        )

        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")

        st.divider()
        st.markdown("##### Eficiência por Serviço")
        df_efficiency = df_ai_summary.copy()
        df_efficiency['CUSTO_POR_REQUEST'] = df_efficiency['CREDITS'] / df_efficiency['REQUESTS']
        df_efficiency = df_efficiency[['SERVICE', 'REQUESTS', 'CREDITS', 'CUSTO_POR_REQUEST']].sort_values('CREDITS', ascending=False)
        df_efficiency.columns = ['Serviço', 'Requests', 'Créditos', 'Custo/Request']
        st.dataframe(df_efficiency, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao carregar dados de Cortex AI: {str(e)}")

# ============================================================
# AI ROI CALCULATOR
# ============================================================

st.divider()
st.header("🧮 AI ROI Calculator")
st.markdown("Quanto valor a IA está gerando na sua organização?")

try:
    df_roi = session.sql("""
        SELECT
            COUNT(*) AS total_requests,
            COUNT(DISTINCT DATE_TRUNC('day', USAGE_TIME::TIMESTAMP_NTZ)) AS active_days
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
    """).to_pandas()

    df_roi_all = session.sql("""
        SELECT ROUND(SUM(credits), 2) AS total_ai_credits
        FROM (
            SELECT SUM(TOKEN_CREDITS) AS credits FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
            UNION ALL SELECT SUM(TOKEN_CREDITS) FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_DESKTOP_USAGE_HISTORY
            UNION ALL SELECT SUM(TOKEN_CREDITS) FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
            UNION ALL SELECT SUM(CREDITS) FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
            UNION ALL SELECT SUM(CREDITS) FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_SERVING_USAGE_HISTORY
            UNION ALL SELECT SUM(TOKEN_CREDITS) FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
            UNION ALL SELECT SUM(CREDITS) FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
        )
    """).to_pandas()

    if not df_roi.empty:
        total_requests_roi = int(df_roi['TOTAL_REQUESTS'].iloc[0] or 0)
        active_days_roi = int(df_roi['ACTIVE_DAYS'].iloc[0] or 1)
        total_all_credits_roi = float(df_roi_all['TOTAL_AI_CREDITS'].iloc[0] or 0)

        estimated_hours_saved = total_requests_roi * (5 / 60)  # 5 min por request
        developer_hourly_rate = 75
        estimated_value_generated = estimated_hours_saved * developer_hourly_rate
        credit_cost_usd = total_all_credits_roi * 3.0
        roi_ratio = estimated_value_generated / max(credit_cost_usd, 1)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Investimento Total AI", f"${credit_cost_usd:,.0f}")
        with col2:
            st.metric("Horas Economizadas", f"{estimated_hours_saved:,.0f}h")
        with col3:
            st.metric("Valor Gerado (estimado)", f"${estimated_value_generated:,.0f}")
        with col4:
            st.metric("ROI", f"{roi_ratio:.0f}x")

        st.markdown(f"""
**Premissas (conservadoras):**
- Cada request AI economiza ~5 minutos de trabalho manual
- Custo médio desenvolvedor: ${developer_hourly_rate}/hora
- Custo médio crédito Snowflake: ~$3.00
- Período analisado: {active_days_roi} dias ativos
- Total de requests AI: {total_requests_roi:,}
        """)

        fig_roi = px.bar(
            x=['Investimento AI', 'Valor Gerado'],
            y=[credit_cost_usd, estimated_value_generated],
            color=['Investimento AI', 'Valor Gerado'],
            color_discrete_map={'Investimento AI': '#E74C3C', 'Valor Gerado': '#2ECC71'}
        )
        fig_roi.update_layout(height=300, showlegend=False, yaxis_title='USD ($)', xaxis_title='')
        st.plotly_chart(fig_roi, use_container_width=True)

        st.success(f"💰 **Para cada $1 investido em IA, a organização gerou ~${roi_ratio:.0f} em produtividade.**")

except Exception as e:
    st.error(f"Erro ao calcular ROI: {str(e)}")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built with 🤖 Cortex AI FinOps Monitor</p>
</div>
""", unsafe_allow_html=True)
