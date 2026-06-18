"""Gradio UI for the language tutor. Renders what tutor_core tracks; styling in tutor_style."""
import html
import warnings

# Gradio 6.19 references a Starlette constant that was renamed; silence the per-request deprecation spam.
warnings.filterwarnings("ignore", message=r".*HTTP_422_UNPROCESSABLE_ENTITY.*")

import gradio as gr

import tutor_core as core
from tutor_style import CSS, HEAD

THINKING = '<span class="thinking"><i></i><i></i><i></i></span>'
GREETING = f"Whenever you're ready to start your next {core.LANGUAGE} lesson, just send me a message."


def _text(content):
    """Gradio 6 hands message content back as a string or a list of parts; get the text."""
    if isinstance(content, list):
        return " ".join(p.get("text", "") for p in content if isinstance(p, dict)).strip()
    return content or ""


def render_xp():
    level, total, into = core.xp_stats()
    return (
        f'<div class="xp-head"><div class="xp-level">Level <span>{level}</span></div>'
        f'<div class="xp-total">{total} XP</div></div>'
        f'<div class="xp-track"><div class="xp-fill" style="width:{into}%"></div></div>'
        f'<div class="xp-sub">{into} / 100 to level {level + 1}</div>'
    )


def render_vocab():
    words = core.recent_vocab(10)
    if not words:
        return '<div class="empty">No words yet -- say hola!</div>'
    rows = []
    for w in words:
        es = html.escape(str(w.get("es") or w.get("word") or ""))
        en = html.escape(str(w.get("en") or w.get("translation") or ""))
        conf = int(w.get("confidence", 1) or 1)
        dots = "".join(f'<span class="dot {"on" if i < conf else ""}"></span>' for i in range(5))
        rows.append(
            f'<div class="vocab-row"><div><span class="vocab-es">{es}</span>'
            f'<span class="vocab-en">{en}</span></div>'
            f'<div class="vocab-conf">{dots}</div></div>'
        )
    return "".join(rows)


def render_grammar():
    topics = core.grammar_topics()
    if not topics:
        return '<div class="empty">No grammar yet.</div>'
    rows = []
    for t in topics[-8:]:
        topic = html.escape(str(t.get("topic", "?")))
        status = str(t.get("status", "introduced")).lower()
        cls = status if status in ("introduced", "practising", "comfortable") else "introduced"
        rows.append(f'<div class="gram-row"><span class="gram-topic">{topic}</span><span class="pill {cls}">{status}</span></div>')
    return "".join(rows)


def render_journey():
    return core.journey_text() or "_Your learning plan will appear here as we go._"


def panels():
    """Everything the right-hand column shows, refreshed straight from the files."""
    return render_xp(), render_vocab(), render_grammar(), render_journey()


def user_submit(msg, history):
    """Show the user's message immediately and clear the input box."""
    msg = (msg or "").strip()
    if not msg:
        return "", history or []
    return "", (history or []) + [{"role": "user", "content": msg}]


async def bot_respond(history, session_id):
    """Stream the reply (fast, no tools), then let the scribe record and the coach refine."""
    user_msg = _text(history[-1]["content"])
    history = history + [{"role": "assistant", "content": THINKING}]
    yield history, session_id

    reply, sid = "", session_id
    async for reply, sid in core.stream_reply(user_msg, session_id):
        history[-1]["content"] = reply
        yield history, sid

    history[-1]["content"] = reply or "..."
    core.record_exchange(user_msg, reply)   # background: vocab / grammar / mistakes / notes
    core.maybe_refine()                     # background: the learning journey (high effort)
    yield history, sid


def build_demo():
    with gr.Blocks(title="Language Tutor") as demo:
        gr.HTML('<div id="app_title">Language <b>Tutor</b></div>')
        session = gr.State(None)
        # 3 columns side by side when wide enough; min_width lets the journey wrap below on narrow windows.
        with gr.Row(equal_height=False):
            with gr.Column(scale=3, min_width=440):
                chat = gr.Chatbot(elem_id="chat", height=560, show_label=False,
                                  value=[{"role": "assistant", "content": GREETING}])
                box = gr.Textbox(elem_id="msgbox", show_label=False, submit_btn=True,
                                 placeholder="Type in Spanish or English, then Enter...")
            with gr.Column(scale=2, min_width=300):
                with gr.Group(elem_id="xp_card", elem_classes="card"):
                    gr.HTML('<div class="card-label">Progress</div>')
                    xp_view = gr.HTML(render_xp())
                with gr.Group(elem_classes="card"):
                    gr.HTML('<div class="card-label">Recent words</div>')
                    vocab_view = gr.HTML(render_vocab())
                with gr.Group(elem_classes="card"):
                    gr.HTML('<div class="card-label">Grammar</div>')
                    grammar_view = gr.HTML(render_grammar())
            with gr.Column(scale=2, min_width=300):
                with gr.Group(elem_id="journey_card", elem_classes="card"):
                    gr.HTML('<div class="card-label">Learning journey</div>')
                    journey_view = gr.Markdown(render_journey(), elem_classes="journey-scroll")

        panel_out = [xp_view, vocab_view, grammar_view, journey_view]
        box.submit(user_submit, [box, chat], [box, chat]).then(bot_respond, [chat, session], [chat, session])
        gr.Timer(2.0).tick(panels, None, panel_out)   # live-refresh panels as background agents write
        demo.load(panels, None, panel_out)
    return demo


def launch(**kwargs):
    """Build and launch the app. In Gradio 6, css/js/theme go to launch()."""
    return build_demo().launch(css=CSS, head=HEAD, theme=gr.themes.Base(), **kwargs)


if __name__ == "__main__":
    launch()
