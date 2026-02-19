"""
Analytics UI Components for Professor Assistant
Streamlit components for visualizing student and class insights.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Optional
import pandas as pd
import numpy as np

from src.domain.analytics_schemas import StudentProfile, ClassInsights


def render_metric_card(title: str, value: str, delta: Optional[str] = None, icon: str = "📊"):
    """Render a styled metric card"""
    delta_html = f"<p style='margin: 0; font-size: 0.9rem; color: #666;'>{delta}</p>" if delta else ""
    
    st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <p style="margin: 0; font-size: 0.9rem; color: #999; text-transform: uppercase;">
                {icon} {title}
            </p>
            <h2 style="margin: 0.5rem 0 0 0; font-size: 2.5rem; color: #333;">
                {value}
            </h2>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def render_student_profile_card(profile: StudentProfile):
    """Render detailed student profile with visualizations"""
    
    # Header with styled card
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h1 style="margin: 0; font-size: 2.5rem;">👤 {profile.student_name}</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">
                ID: {profile.student_id} • {profile.submission_count} submissões
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Key metrics with custom cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        grade_color = "#2ecc71" if profile.avg_grade >= 7 else "#e74c3c" if profile.avg_grade < 5 else "#f39c12"
        st.markdown(f"""
            <div style="padding: 1rem; background: {grade_color}; color: white; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0;">📊 Média</h3>
                <h1 style="margin: 0.5rem 0;">{profile.avg_grade:.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        trend_emoji = {
            "improving": "📈",
            "stable": "➡️",
            "declining": "📉",
            "insufficient_data": "❓"
        }
        trend_color = {
            "improving": "#2ecc71",
            "stable": "#3498db",
            "declining": "#e74c3c",
            "insufficient_data": "#95a5a6"
        }
        st.markdown(f"""
            <div style="padding: 1rem; background: {trend_color[profile.trend]}; color: white; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0;">{trend_emoji[profile.trend]} Tendência</h3>
                <h2 style="margin: 0.5rem 0; font-size: 1.2rem;">{profile.trend.replace('_', ' ').title()}</h2>
                <p style="margin: 0; font-size: 0.9rem;">Conf: {profile.trend_confidence:.0%}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div style="padding: 1rem; background: #667eea; color: white; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0;">📝 Submissões</h3>
                <h1 style="margin: 0.5rem 0;">{profile.submission_count}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        gaps_color = "#e74c3c" if len(profile.learning_gaps) > 2 else "#f39c12" if len(profile.learning_gaps) > 0 else "#2ecc71"
        st.markdown(f"""
            <div style="padding: 1rem; background: {gaps_color}; color: white; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0;">⚠️ Gaps</h3>
                <h1 style="margin: 0.5rem 0;">{len(profile.learning_gaps)}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Grade evolution chart with enhanced visualizations
    if len(profile.submissions_history) >= 2:
        st.subheader("📊 Evolução das Notas")
        
        df = pd.DataFrame([
            {
                "Submissão": i + 1,
                "Nota": sub.grade,
                "Data": sub.timestamp.strftime("%d/%m"),
                "Questão": sub.question_text[:40] + "..."
            }
            for i, sub in enumerate(profile.submissions_history)
        ])
        
        # Create dual chart: line + bar
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Trajetória de Desempenho", "Performance por Questão"),
            column_widths=[0.6, 0.4]
        )
        
        # Line chart with trend
        fig.add_trace(
            go.Scatter(
                x=df["Submissão"],
                y=df["Nota"],
                mode='lines+markers',
                name='Nota',
                line=dict(color='#667eea', width=3),
                marker=dict(size=10, color='#764ba2'),
                hovertemplate='<b>Submissão %{x}</b><br>Nota: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add trend line if applicable
        if profile.trend != "insufficient_data":
            x = np.arange(len(df))
            z = np.polyfit(x, df["Nota"], 1)
            p = np.poly1d(z)
            
            fig.add_trace(
                go.Scatter(
                    x=df["Submissão"],
                    y=p(x),
                    mode='lines',
                    name='Tendência',
                    line=dict(color='rgba(255,165,0,0.5)', dash='dash', width=2),
                    hovertemplate='Tendência: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Bar chart
        colors = ['#2ecc71' if g >= 7 else '#e74c3c' if g < 5 else '#f39c12' 
                  for g in df["Nota"]]
        
        fig.add_trace(
            go.Bar(
                x=df["Submissão"],
                y=df["Nota"],
                marker_color=colors,
                name='Nota',
                hovertemplate='<b>%{customdata}</b><br>Nota: %{y:.2f}<extra></extra>',
                customdata=df["Questão"]
            ),
            row=1, col=2
        )
        
        # Reference lines
        for col_idx in [1, 2]:
            fig.add_hline(
                y=7.0, line_dash="dash", line_color="green", 
                annotation_text="Aprovação", annotation_position="right",
                row=1, col=col_idx
            )
            fig.add_hline(
                y=5.0, line_dash="dot", line_color="orange",
                row=1, col=col_idx
            )
        
        fig.update_xaxes(title_text="Submissão", row=1, col=1)
        fig.update_xaxes(title_text="Submissão", row=1, col=2)
        fig.update_yaxes(title_text="Nota", range=[0, 10], row=1, col=1)
        fig.update_yaxes(title_text="Nota", range=[0, 10], row=1, col=2)
        
        fig.update_layout(
            height=400,
            showlegend=False,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Criterion performance heatmap
        st.subheader("🔥 Heatmap de Performance por Critério")
        
        # Build criterion matrix
        criterion_matrix = {}
        for sub in profile.submissions_history:
            for crit_name, score in sub.criterion_scores.items():
                if crit_name not in criterion_matrix:
                    criterion_matrix[crit_name] = []
                criterion_matrix[crit_name].append(score)
        
        if criterion_matrix:
            # Create heatmap data
            heatmap_data = []
            criteria = list(criterion_matrix.keys())
            max_len = max(len(v) for v in criterion_matrix.values())
            
            for crit in criteria:
                scores = criterion_matrix[crit]
                # Pad with None for missing values
                scores += [None] * (max_len - len(scores))
                heatmap_data.append(scores)
            
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=[f"Sub {i+1}" for i in range(max_len)],
                y=criteria,
                colorscale='RdYlGn',
                zmid=5,
                zmin=0,
                zmax=10,
                text=[[f"{v:.1f}" if v is not None else "" for v in row] for row in heatmap_data],
                texttemplate="%{text}",
                textfont={"size": 12},
                hovertemplate='<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>'
            ))
            
            fig_heat.update_layout(
                title="Evolução por Critério de Avaliação",
                xaxis_title="Submissão",
                yaxis_title="Critério",
                height=300
            )
            
            st.plotly_chart(fig_heat, use_container_width=True)
    
    # Learning gaps with styled cards
    if profile.learning_gaps:
        st.subheader("⚠️ Gaps de Aprendizado")
        
        for gap in profile.learning_gaps:
            severity_config = {
                "high": {"color": "#e74c3c", "icon": "🔴", "label": "CRÍTICO"},
                "medium": {"color": "#f39c12", "icon": "🟡", "label": "MODERADO"},
                "low": {"color": "#2ecc71", "icon": "🟢", "label": "LEVE"}
            }
            
            config = severity_config[gap.severity]
            
            with st.expander(f"{config['icon']} {gap.criterion_name} - Média: {gap.avg_score:.1f}/10"):
                st.markdown(f"""
                    <div style="padding: 1rem; background: {config['color']}15; border-left: 4px solid {config['color']}; border-radius: 5px; margin-bottom: 1rem;">
                        <h4 style="margin: 0; color: {config['color']};">Severidade: {config['label']}</h4>
                        <p style="margin: 0.5rem 0;">Evidências: {gap.evidence_count} submissões</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.info(f"💡 **Sugestão:** {gap.suggestion}")
    else:
        st.success("✅ Nenhum gap crítico identificado!")
    
    # Strengths
    if profile.strengths:
        st.subheader("💪 Pontos Fortes")
        
        strength_df = pd.DataFrame([
            {
                "Critério": s.criterion_name,
                "Média": s.avg_score,
                "Consistência": f"{s.consistency:.0%}"
            }
            for s in profile.strengths
        ])
        
        st.dataframe(strength_df, use_container_width=True, hide_index=True)
    
    # Detailed submissions
    with st.expander("📝 Histórico Detalhado de Submissões"):
        for i, sub in enumerate(profile.submissions_history):
            st.markdown(f"**Submissão {i+1}** - {sub.timestamp.strftime('%d/%m/%Y %H:%M')}")
            st.write(f"Questão: {sub.question_text[:100]}...")
            st.write(f"Nota: **{sub.grade:.2f}** / {sub.max_score}")
            
            if sub.criterion_scores:
                st.write("Detalhamento por critério:")
                for crit, score in sub.criterion_scores.items():
                    st.write(f"  - {crit}: {score:.1f}")
            
            if sub.divergence_detected:
                st.warning("⚠️ Correção teve divergência entre agentes")
            
            st.divider()


def render_class_analytics_dashboard(insights: ClassInsights, profiles: List[StudentProfile]):
    """Render class-level analytics dashboard"""
    
    # Styled header
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h1 style="margin: 0; font-size: 2.5rem;">🏫 Análise da Turma</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">
                {insights.class_id} • {insights.total_students} alunos • {insights.total_submissions} submissões
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Key metrics with colored cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_color = "#2ecc71" if insights.class_avg_grade >= 7 else "#e74c3c" if insights.class_avg_grade < 5 else "#f39c12"
        st.markdown(f"""
            <div style="padding: 1rem; background: {avg_color}; color: white; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0;">📊 Média da Turma</h3>
                <h1 style="margin: 0.5rem 0;">{insights.class_avg_grade:.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style="padding: 1rem; background: #3498db; color: white; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0;">📍 Mediana</h3>
                <h1 style="margin: 0.5rem 0;">{insights.median_grade:.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        std_color = "#2ecc71" if insights.std_deviation < 1.5 else "#f39c12" if insights.std_deviation < 2.5 else "#e74c3c"
        st.markdown(f"""
            <div style="padding: 1rem; background: {std_color}; color: white; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0;">📏 Desvio Padrão</h3>
                <h1 style="margin: 0.5rem 0;">{insights.std_deviation:.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div style="padding: 1rem; background: #9b59b6; color: white; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0;">👥 Total de Alunos</h3>
                <h1 style="margin: 0.5rem 0;">{insights.total_students}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Grade distribution with multiple views
    st.subheader("📊 Distribuição de Desempenho")
    
    tab_dist, tab_box, tab_violin = st.tabs(["📊 Conceitos", "📦 Box Plot", "🎻 Violino"])
    
    with tab_dist:
        dist_df = pd.DataFrame([
            {"Conceito": k, "Quantidade": v}
            for k, v in insights.grade_distribution.items()
        ])
        
        fig = go.Figure()
        
        colors = {
            "A": "#2ecc71", "B": "#3498db", "C": "#f39c12",
            "D": "#e67e22", "F": "#e74c3c"
        }
        
        for _, row in dist_df.iterrows():
            fig.add_trace(go.Bar(
                x=[row["Conceito"]],
                y=[row["Quantidade"]],
                name=row["Conceito"],
                marker_color=colors.get(row["Conceito"], "#95a5a6"),
                text=[row["Quantidade"]],
                textposition='outside',
                hovertemplate=f'<b>{row["Conceito"]}</b>: {row["Quantidade"]} alunos<extra></extra>'
            ))
        
        fig.update_layout(
            title="Distribuição por Conceito",
            xaxis_title="Conceito",
            yaxis_title="Quantidade de Alunos",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_box:
        all_grades = []
        for profile in profiles:
            all_grades.extend([s.grade for s in profile.submissions_history])
        
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=all_grades,
            name="Notas",
            marker_color='#667eea',
            boxmean='sd',
            hovertemplate='<b>Estatísticas</b><br>Valor: %{y:.2f}<extra></extra>'
        ))
        
        # Add reference lines
        fig.add_hline(y=7.0, line_dash="dash", line_color="green", 
                     annotation_text="Aprovação (7.0)", annotation_position="right")
        fig.add_hline(y=insights.class_avg_grade, line_dash="dot", line_color="blue",
                     annotation_text=f"Média ({insights.class_avg_grade:.2f})", 
                     annotation_position="left")
        
        fig.update_layout(
            title="Distribuição Estatística das Notas",
            yaxis_title="Nota",
            yaxis_range=[0, 10],
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics summary
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            st.metric("Q1 (25%)", f"{pd.Series(all_grades).quantile(0.25):.2f}")
        with col_s2:
            st.metric("Mediana", f"{insights.median_grade:.2f}")
        with col_s3:
            st.metric("Q3 (75%)", f"{pd.Series(all_grades).quantile(0.75):.2f}")
        with col_s4:
            st.metric("IQR", f"{np.subtract(*pd.Series(all_grades).quantile([0.75, 0.25])):.2f}")
    
    with tab_violin:
        all_grades_with_names = []
        for profile in profiles:
            for sub in profile.submissions_history:
                all_grades_with_names.append({
                    "Aluno": profile.student_name,
                    "Nota": sub.grade
                })
        
        df_violin = pd.DataFrame(all_grades_with_names)
        
        fig = go.Figure()
        
        fig.add_trace(go.Violin(
            y=df_violin["Nota"],
            name="Distribuição",
            box_visible=True,
            meanline_visible=True,
            fillcolor='#764ba2',
            opacity=0.6,
            hovertemplate='Nota: %{y:.2f}<extra></extra>'
        ))
        
        fig.add_hline(y=7.0, line_dash="dash", line_color="green")
        
        fig.update_layout(
            title="Distribuição de Densidade das Notas",
            yaxis_title="Nota",
            yaxis_range=[0, 10],
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Outliers with styled cards
    col_struggle, col_top = st.columns(2)
    
    with col_struggle:
        st.subheader("⚠️ Alunos em Dificuldade")
        if insights.struggling_students:
            for student in insights.struggling_students:
                st.markdown(f"""
                    <div style="padding: 0.8rem; background: #e74c3c15; border-left: 4px solid #e74c3c; border-radius: 5px; margin: 0.5rem 0;">
                        ⚠️ <b>{student}</b>
                    </div>
                """, unsafe_allow_html=True)
            st.caption(f"Critério: Média < {insights.class_avg_grade - insights.std_deviation:.2f}")
        else:
            st.success("✅ Nenhum aluno significativamente abaixo da média")
    
    with col_top:
        st.subheader("🏆 Destaques da Turma")
        if insights.top_performers:
            for student in insights.top_performers:
                st.markdown(f"""
                    <div style="padding: 0.8rem; background: #2ecc7115; border-left: 4px solid #2ecc71; border-radius: 5px; margin: 0.5rem 0;">
                        🏆 <b>{student}</b>
                    </div>
                """, unsafe_allow_html=True)
            st.caption(f"Critério: Média > {insights.class_avg_grade + insights.std_deviation:.2f}")
        else:
            st.info("Nenhum aluno significativamente acima da média")
    
    st.divider()
    
    # Common gaps
    if insights.most_common_gaps:
        st.subheader("🔍 Gaps Comuns da Turma")
        st.caption("Dificuldades identificadas em >30% dos alunos")
        
        for gap in insights.most_common_gaps:
            severity_config = {
                "high": {"color": "#e74c3c", "icon": "🔴"},
                "medium": {"color": "#f39c12", "icon": "🟡"},
                "low": {"color": "#2ecc71", "icon": "🟢"}
            }
            config = severity_config[gap.severity]
            
            with st.expander(f"{config['icon']} {gap.criterion_name} - {gap.evidence_count} alunos afetados"):
                st.markdown(f"""
                    <div style="padding: 1rem; background: {config['color']}15; border-left: 4px solid {config['color']}; border-radius: 5px;">
                        <p style="margin: 0;"><b>Média de desempenho:</b> {gap.avg_score:.2f}/10</p>
                        <p style="margin: 0.5rem 0 0 0;"><b>Severidade:</b> {gap.severity.upper()}</p>
                    </div>
                """, unsafe_allow_html=True)
                st.info(f"💡 **Recomendação:** {gap.suggestion}")
    else:
        st.success("✅ Nenhum gap comum identificado na turma")
    
    # Student ranking with radar chart
    st.divider()
    st.subheader("🏆 Ranking e Comparação de Alunos")
    
    # Prepare data
    student_data = []
    for profile in profiles:
        if profile.submission_count >= 3:  # Only students with enough data
            student_data.append({
                "Nome": profile.student_name,
                "Média": profile.avg_grade,
                "Submissões": profile.submission_count,
                "Tendência": profile.trend
            })
    
    if student_data:
        df_rank = pd.DataFrame(student_data).sort_values("Média", ascending=False)
        
        col_rank, col_radar = st.columns([1, 1])
        
        with col_rank:
            # Enhanced ranking table
            st.markdown("#### 📋 Classificação Geral")
            
            for i, row in df_rank.head(10).iterrows():
                trend_emoji = {
                    "improving": "📈",
                    "stable": "➡️",
                    "declining": "📉",
                    "insufficient_data": "❓"
                }
                
                medal = ""
                rank_pos = df_rank.index.get_loc(i)
                if rank_pos == 0:
                    medal = "🥇"
                elif rank_pos == 1:
                    medal = "🥈"
                elif rank_pos == 2:
                    medal = "🥉"
                else:
                    medal = f"{rank_pos + 1}º"
                
                st.markdown(f"""
                    <div style="
                        padding: 0.8rem;
                        margin: 0.5rem 0;
                        background: linear-gradient(90deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                        border-left: 4px solid #667eea;
                        border-radius: 5px;
                    ">
                        <b>{medal} {row['Nome']}</b> {trend_emoji[row['Tendência']]}<br>
                        <span style="color: #666;">
                            Média: <b>{row['Média']:.2f}</b> • {row['Submissões']} submissões
                        </span>
                    </div>
                """, unsafe_allow_html=True)
        
        with col_radar:
            st.markdown("#### 🕸️ Comparação Multidimensional (Top 5)")
            
            # Select top 5 for radar
            top_5 = df_rank.head(5)
            
            # Build radar chart data
            categories = []
            if profiles[0].submissions_history and profiles[0].submissions_history[0].criterion_scores:
                categories = list(profiles[0].submissions_history[0].criterion_scores.keys())
            
            if categories:
                fig_radar = go.Figure()
                
                for _, student_row in top_5.iterrows():
                    # Find profile
                    profile = next(p for p in profiles if p.student_name == student_row["Nome"])
                    
                    # Calculate avg per criterion
                    criterion_avgs = {cat: [] for cat in categories}
                    for sub in profile.submissions_history:
                        for cat, score in sub.criterion_scores.items():
                            if cat in criterion_avgs:
                                criterion_avgs[cat].append(score)
                    
                    values = [sum(v)/len(v) if v else 0 for v in criterion_avgs.values()]
                    
                    fig_radar.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name=student_row["Nome"],
                        hovertemplate='<b>%{theta}</b><br>Média: %{r:.2f}<extra></extra>'
                    ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10]
                        )
                    ),
                    showlegend=True,
                    height=400
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Dados insuficientes para gerar radar chart.")
    
    # Question difficulty
    if insights.most_difficult_questions:
        st.divider()
        st.subheader("❓ Questões Mais Difíceis")
        
        diff_df = pd.DataFrame(insights.most_difficult_questions).head(10)
        
        fig = go.Figure()
        
        colors = {
            "Hard": "#e74c3c",
            "Medium": "#f39c12",
            "Easy": "#2ecc71"
        }
        
        for difficulty in ["Hard", "Medium", "Easy"]:
            subset = diff_df[diff_df["difficulty"] == difficulty]
            if not subset.empty:
                fig.add_trace(go.Bar(
                    x=subset["question_id"],
                    y=subset["avg_score"],
                    name=difficulty,
                    marker_color=colors[difficulty],
                    text=subset["avg_score"].apply(lambda x: f"{x:.1f}"),
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Média: %{y:.2f}<br>Tentativas: %{customdata}<extra></extra>',
                    customdata=subset["attempt_count"]
                ))
        
        fig.add_hline(y=7.0, line_dash="dash", line_color="green", 
                     annotation_text="Aprovação", annotation_position="right")
        fig.add_hline(y=insights.class_avg_grade, line_dash="dot", line_color="blue",
                     annotation_text=f"Média da turma", annotation_position="left")
        
        fig.update_layout(
            title="Top 10 Questões com Menor Desempenho",
            xaxis_title="ID da Questão",
            yaxis_title="Média de Acertos",
            yaxis_range=[0, 10],
            height=400,
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_analytics_selector(profiles: List[StudentProfile]):
    """Render student selector for individual analytics"""
    
    if not profiles:
        st.warning("⚠️ Nenhum dado de aluno disponível ainda. Execute correções primeiro.")
        return None
    
    student_names = [p.student_name for p in profiles]
    selected_name = st.selectbox(
        "Selecione um aluno para ver o perfil detalhado:",
        student_names
    )
    
    selected_profile = next(p for p in profiles if p.student_name == selected_name)
    return selected_profile
