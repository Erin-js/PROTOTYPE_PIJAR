import plotly.graph_objects as go

BLUE = "#173C65"
GREEN = "#18865F"
ORANGE = "#E58A2F"


def polish(fig, ytitle=None, bounded=False, height=330):
    fig.update_layout(template="plotly_white", height=height,
                      font=dict(family="Arial, sans-serif", color=BLUE, size=13),
                      margin=dict(l=35, r=20, t=25, b=35),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.2, x=0),
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#E5ECE8", title=ytitle))
    if bounded:
        fig.update_yaxes(range=[0, 4.1])
    return fig


def personal_history(history):
    fig = go.Figure()
    for col, label, color in [("IP_Semester", "IP semester", GREEN), ("IPK_Kumulatif", "IPK kumulatif", BLUE)]:
        fig.add_trace(go.Scatter(x=history.Semester_Ke, y=history[col], mode="lines+markers",
                                name=label, line=dict(color=color, width=3),
                                hovertemplate="Semester %{x}<br>Nilai %{y:.2f}<extra>%{fullData.name}</extra>"))
    fig.update_xaxes(title="Semester", dtick=1)
    return polish(fig, "Nilai (0–4)", True)


def individual_prediction(values, pred, actual=None):
    fig = go.Figure(go.Scatter(x=[1, 2, 3], y=values, mode="lines+markers", name="IP tercatat", line=dict(color=BLUE, width=3)))
    fig.add_trace(go.Scatter(x=[3, 4], y=[values[2], pred["pred"]], mode="lines+markers", name="Prediksi IP4",
                            line=dict(color=GREEN, width=3, dash="dash"),
                            error_y=dict(type="data", symmetric=False, array=[0, pred["high"] - pred["pred"]],
                                         arrayminus=[0, pred["pred"] - pred["low"]])))
    if actual is not None:
        fig.add_trace(go.Scatter(x=[4], y=[actual], mode="markers", name="IP4 aktual", marker=dict(color=ORANGE, size=12, symbol="diamond")))
    fig.add_vrect(x0=3.5, x1=4.3, fillcolor=GREEN, opacity=0.05, line_width=0)
    fig.update_xaxes(title="Semester", tickvals=[1, 2, 3, 4], ticktext=["1", "2", "3", "4 (prediksi)"])
    return polish(fig, "IP semester (0–4)", True)


def group_prediction(test):
    fig = go.Figure()
    for fg, label, color in [(True, "Generasi pertama", ORANGE), (False, "Bukan generasi pertama", BLUE)]:
        group = test.loc[test.fg.eq(fg)]
        if group.empty:
            continue
        means = group[["ip1", "ip2", "ip3", "pred"]].mean().to_numpy()
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=means[:3], mode="lines+markers", name=f"{label} (n={len(group):,})", line=dict(color=color, width=3)))
        fig.add_trace(go.Scatter(x=[3, 4], y=means[2:], mode="lines+markers", name=f"Prediksi {label}", showlegend=False,
                                line=dict(color=color, width=3, dash="dash")))
    fig.update_xaxes(title="Semester", dtick=1)
    return polish(fig, "Rata-rata IP semester (0–4)", True)


def cohort_chart(frame):
    fig = go.Figure()
    for fg, label, color in [(True, "Generasi pertama", ORANGE), (False, "Bukan generasi pertama", BLUE)]:
        g = frame.loc[frame.fg.eq(fg)]
        if not g.empty:
            fig.add_trace(go.Scatter(x=g.Semester_Ke, y=g["mean"], mode="lines+markers", name=f"{label} (n={int(g.iloc[0]['size'])})", line=dict(color=color, width=3)))
    fig.update_xaxes(title="Semester", dtick=1)
    return polish(fig, "Rata-rata IPK kumulatif (0–4)", True)
